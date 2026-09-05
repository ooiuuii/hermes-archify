"""Bridge boundary tests plus an opt-in-by-presence real-engine smoke test.

Run from the repository root with ``python -m unittest discover -s tests -v``.
The real-engine test runs when the separately installed pinned engine is present.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bridge


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "archify-pipeline.architecture.json"


def fingerprint(data: bytes) -> dict:
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hermes-archify-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.engine = self.root / "engine"
        (self.engine / "bin").mkdir(parents=True)
        (self.engine / "bin" / "archify.mjs").write_text("// test double\n", encoding="utf-8")
        (self.engine / "package.json").write_text(
            json.dumps({"name": "archify", "version": "2.16.0"}), encoding="utf-8"
        )
        self.spec = self.root / "input with spaces.architecture.json"
        self.spec.write_bytes(EXAMPLE.read_bytes())
        self.output = self.root / "output with spaces.html"

    def execute(self, action="deliver", **overrides):
        options = {
            "input_path": str(self.spec),
            "output_path": str(self.output),
            "engine_dir": str(self.engine),
            "node_binary": sys.executable,
            "timeout": 7,
        }
        options.update(overrides)
        return bridge.execute(action, **options)

    def receipt(self, artifact=b"<!doctype html><html><body>checked</body></html>"):
        return {
            "schemaVersion": 1,
            "ok": True,
            "command": "deliver",
            "type": "architecture",
            "input": str(self.spec),
            "output": str(self.output),
            "specification": fingerprint(self.spec.read_bytes()),
            "artifact": fingerprint(artifact),
            "validation": {
                "checksPassed": 9,
                "checkCount": 9,
                "compositionProfile": "showcase",
                "compositionStatus": "pass",
                "errors": 0,
                "warnings": 0,
            },
        }

    def test_import_does_not_execute_engine(self):
        with patch("subprocess.run") as run, patch("subprocess.Popen") as popen:
            importlib.reload(bridge)
        run.assert_not_called()
        popen.assert_not_called()

    def test_missing_engine_returns_actionable_failure_without_subprocess(self):
        with patch("subprocess.run") as run:
            result = self.execute(engine_dir=str(self.root / "missing-engine"))
        self.assertFalse(result["ok"])
        self.assertTrue(result.get("error") or result.get("diagnostics"))
        run.assert_not_called()

    def test_invalid_paths_are_rejected_before_subprocess(self):
        cases = [
            {"input_path": "relative.json"},
            {"output_path": "relative.html"},
            {"output_path": str(self.root / "not-html.txt")},
        ]
        for options in cases:
            with self.subTest(options=options), patch("subprocess.run") as run:
                result = self.execute(**options)
                self.assertFalse(result["ok"])
                run.assert_not_called()

    def test_subprocess_start_failure_is_reported(self):
        with patch("subprocess.run", side_effect=OSError("test process unavailable")):
            result = self.execute()
        self.assertFalse(result["ok"])
        self.assertTrue(result.get("error") or result.get("diagnostics"))

    def test_subprocess_timeout_is_reported(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["node"], 7)):
            result = self.execute()
        self.assertFalse(result["ok"])
        self.assertIn("timeout", json.dumps(result).lower().replace("timed out", "timeout"))

    def test_non_json_stdout_is_not_success(self):
        for returncode in (0, 2):
            with self.subTest(returncode=returncode):
                completed = subprocess.CompletedProcess([], returncode, "not a JSON receipt", "usage failure")
                with patch("subprocess.run", return_value=completed):
                    result = self.execute()
                self.assertFalse(result["ok"])

    def test_engine_failure_preserves_diagnostic_and_old_output(self):
        previous = b"last successful artifact"
        self.output.write_bytes(previous)
        diagnostic = {
            "code": "composition/label-route-clearance",
            "severity": "error",
            "message": "A label overlaps an unrelated route.",
            "subject": {"relationship": "agent-to-ir"},
            "evidence": {"clearance": 0},
            "supportedFixes": ["adjust labelAt"],
        }
        receipt = {
            "schemaVersion": 1,
            "ok": False,
            "command": "deliver",
            "stage": "check",
            "type": "architecture",
            "input": str(self.spec),
            "output": str(self.output),
            "error": "Final artifact check failed.",
            "diagnostics": [diagnostic],
        }
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 1, json.dumps(receipt), "")):
            result = self.execute()
        self.assertFalse(result["ok"])
        self.assertIn(diagnostic["code"], json.dumps(result))
        self.assertIn("adjust labelAt", json.dumps(result))
        self.assertEqual(previous, self.output.read_bytes())

    def test_deliver_uses_argument_array_and_returns_verified_artifact_metadata(self):
        artifact = b"<!doctype html><html><body>checked</body></html>"
        receipt = self.receipt(artifact)

        def deliver(arguments, **options):
            self.assertIsInstance(arguments, list)
            self.assertEqual(arguments[0], sys.executable)
            self.assertEqual(Path(arguments[1]), self.engine / "bin" / "archify.mjs")
            self.assertEqual(arguments[2:4], ["deliver", "architecture"])
            self.assertIn(str(self.spec), arguments)
            self.assertIn(str(self.output), arguments)
            self.assertIn("--json", arguments)
            self.assertEqual(arguments[arguments.index("--quality") + 1], "showcase")
            self.assertNotIn("--open", arguments)
            self.assertFalse(options.get("shell", False))
            self.assertEqual(options["timeout"], 7)
            self.output.write_bytes(artifact)
            return subprocess.CompletedProcess(arguments, 0, json.dumps(receipt), "")

        with patch("subprocess.run", side_effect=deliver) as run:
            result = self.execute()
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["receipt"], receipt)
        diagram = next(item for item in result["files"] if item["role"] == "diagram")
        self.assertEqual(diagram["path"], str(self.output))
        self.assertEqual(diagram["mime"], "text/html")
        self.assertEqual(diagram["bytes"], len(artifact))
        self.assertIn(fingerprint(artifact)["sha256"], json.dumps(result))
        run.assert_called_once()

    def test_success_receipt_with_wrong_artifact_hash_is_rejected(self):
        receipt = self.receipt()
        self.output.write_bytes(b"not the artifact described by the receipt")
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, json.dumps(receipt), "")):
            result = self.execute()
        self.assertFalse(result["ok"])

    def test_validate_does_not_request_a_delivery_output(self):
        receipt = {
            "schemaVersion": 1,
            "ok": True,
            "command": "validate",
            "type": "architecture",
            "input": str(self.spec),
            "checks": [{"name": name, "ok": True} for name in (
                "single_svg", "finite_svg", "orthogonal_arrows", "legend_clearance",
                "label_route_clearance", "relationship_crossings", "relationship_corridors",
                "container_border_runs", "route_rhythm",
            )],
            "composition": {"profile": "showcase", "status": "pass", "summary": {"errors": 0, "warnings": 0}},
        }
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, json.dumps(receipt), "")) as run:
            result = self.execute("validate", output_path=None)
        self.assertTrue(result["ok"], result)
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[2:4], ["validate", "architecture"])
        self.assertNotIn(str(self.output), arguments)
        self.assertFalse(self.output.exists())


class RealEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = Path(os.environ.get("ARCHIFY_TEST_ENGINE", ROOT / ".engine" / "archify")).resolve()
        cls.node = os.environ.get("ARCHIFY_TEST_NODE") or shutil.which("node")
        if not cls.node or not (cls.engine / "bin" / "archify.mjs").is_file():
            raise unittest.SkipTest("pinned engine and Node are not installed; run the documented engine setup")

    def test_real_delivery_then_invalid_update_keeps_last_good_bytes(self):
        with tempfile.TemporaryDirectory(prefix="hermes-archify-real-") as directory:
            root = Path(directory).resolve()
            source = root / "pipeline.architecture.json"
            output = root / "pipeline.html"
            source.write_bytes(EXAMPLE.read_bytes())
            options = {
                "input_path": str(source),
                "output_path": str(output),
                "engine_dir": str(self.engine),
                "node_binary": str(self.node),
            }
            success = bridge.execute("deliver", **options)
            self.assertTrue(success["ok"], success)
            before = output.read_bytes()
            self.assertEqual(success["receipt"]["artifact"], fingerprint(before))
            self.assertEqual(success["receipt"]["specification"], fingerprint(source.read_bytes()))
            self.assertEqual(success["receipt"]["validation"]["checksPassed"], 9)
            source.write_text('{"schema_version":', encoding="utf-8")
            failure = bridge.execute("deliver", **options)
            self.assertFalse(failure["ok"], failure)
            self.assertIn("input/json-parse", json.dumps(failure))
            self.assertEqual(before, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
