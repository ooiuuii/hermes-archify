"""Registration contracts and an opt-in real Hermes loader smoke.

Set HERMES_SOURCE_DIR to a Hermes checkout for the integration test.
HERMES_PYTHON optionally selects its Python environment. Neither setting is
product configuration; the child receives an isolated home and no credentials.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class RecordingContext:
    def __init__(self):
        self.tools = []
        self.skills = []

    def register_tool(self, **kwargs):
        self.tools.append(kwargs)

    def register_skill(self, name, path, description=""):
        self.skills.append((name, path, description))


class PluginTests(unittest.TestCase):
    def test_registration_and_invalid_arguments_do_not_launch_processes(self):
        spec = importlib.util.spec_from_file_location(
            "archify_registration_test",
            PLUGIN_ROOT / "__init__.py",
            submodule_search_locations=[str(PLUGIN_ROOT)],
        )
        module = importlib.util.module_from_spec(spec)
        context = RecordingContext()
        with patch("subprocess.run", side_effect=AssertionError("process on import")), patch(
            "subprocess.Popen", side_effect=AssertionError("process on import")
        ):
            spec.loader.exec_module(module)
            module.register(context)
            invalid = json.loads(module.archify_diagram(None))
        self.assertFalse(invalid["ok"])
        self.assertEqual([tool["name"] for tool in context.tools], ["archify_diagram"])
        self.assertEqual(context.tools[0]["schema"]["name"], context.tools[0]["name"])
        self.assertEqual(context.skills[0][0], "archify")
        self.assertTrue(context.skills[0][1].is_file())

    @unittest.skipUnless(os.environ.get("HERMES_SOURCE_DIR"), "set HERMES_SOURCE_DIR for real Hermes integration")
    def test_real_loader_dispatch_and_both_skill_discovery_routes(self):
        source = Path(os.environ["HERMES_SOURCE_DIR"]).resolve()
        self.assertTrue((source / "hermes_cli" / "plugins.py").is_file())
        python = os.environ.get("HERMES_PYTHON", sys.executable)
        script = r'''
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

root = Path(sys.argv[1])
isolated_home = Path(os.environ["HERMES_HOME"])
assert isolated_home.is_dir()
import hermes_cli.plugins as plugins
from tools.registry import registry

manager = plugins.PluginManager()
plugins._plugin_manager = manager
manifest = manager._parse_manifest(root / "plugin.yaml", root, "user", "")
assert manifest is not None
# Exercise the actual loader. Registration must not start an engine or installer.
with patch("subprocess.run", side_effect=AssertionError("process during registration")), patch(
    "subprocess.Popen", side_effect=AssertionError("process during registration")
):
    manager._load_plugin(manifest)
loaded = manager._plugins[manifest.name]
assert loaded.enabled, loaded.error
assert loaded.error is None
assert set(loaded.tools_registered) == {"archify_diagram"}
assert registry.get_schema("archify_diagram")["parameters"]["required"] == ["action"]

# This is a real dispatch to the real bridge, with no process or result mocks.
raw = registry.dispatch("archify_diagram", {"action": "doctor"}, task_id="isolated-smoke")
assert isinstance(raw, str)
doctor = json.loads(raw)
assert doctor["action"] == "doctor"
assert isinstance(doctor["ok"], bool)
assert Path(doctor["plugin_root"]).resolve() == root.resolve()
assert all(doctor[key] for key in ("engine_dir", "schema_path", "examples_dir"))
engine_installed = (Path(doctor["engine_dir"]) / "bin" / "archify.mjs").is_file()
delivered_sha256 = None
if engine_installed:
    assert doctor["ok"], doctor
    specification = root / "examples" / "archify-pipeline.architecture.json"
    assert specification.is_file(), specification
    artifact_dir = isolated_home / "artifacts"
    artifact_dir.mkdir()
    artifact_path = artifact_dir / "hermes-registry-smoke.html"
    delivery_raw = registry.dispatch(
        "archify_diagram",
        {"action": "deliver", "input_path": str(specification),
         "output_path": str(artifact_path), "repo_root": str(root)},
        task_id="isolated-smoke",
    )
    assert isinstance(delivery_raw, str)
    delivery = json.loads(delivery_raw)
    assert delivery["ok"], delivery
    assert delivery["action"] == "deliver"
    assert delivery["receipt"]["ok"], delivery["receipt"]
    html_bytes = artifact_path.read_bytes()
    assert b"<html" in html_bytes.lower()
    delivered_sha256 = hashlib.sha256(html_bytes).hexdigest()
    artifact_receipt = delivery["receipt"]["artifact"]
    assert artifact_receipt["sha256"] == delivered_sha256
    assert artifact_receipt["bytes"] == len(html_bytes)
    diagram = next(item for item in delivery["files"] if item["role"] == "diagram")
    assert Path(diagram["path"]).resolve() == artifact_path.resolve()
    assert diagram["sha256"] == delivered_sha256
    assert diagram["bytes"] == len(html_bytes)
    assert delivery["browser_check"] == "not_run"
    assert delivery["visual_review"] == "not_run"

from tools.skills_tool import skill_view
from agent.skill_commands import scan_skill_commands
namespaced = json.loads(skill_view("hermes-archify:archify"))
assert namespaced["success"], namespaced
assert namespaced["name"] == "hermes-archify:archify"
assert 0 < len(namespaced["description"]) <= 60
assert "/archify" not in scan_skill_commands()

# An explicit ordinary skill installation supplies normal slash discovery.
installed_skill = isolated_home / "skills" / "archify"
shutil.copytree(root / "skills" / "archify", installed_skill)
ordinary = json.loads(skill_view("archify"))
assert ordinary["success"], ordinary
commands = scan_skill_commands()
assert Path(commands["/archify"]["skill_dir"]).resolve() == installed_skill.resolve()
print(json.dumps({"loaded": True, "tool": "archify_diagram", "doctor_ok": doctor["ok"],
                  "engine_installed": engine_installed, "delivered_sha256": delivered_sha256,
                  "plugin_skill": namespaced["name"], "ordinary_skill": "/archify"}))
'''
        with tempfile.TemporaryDirectory(prefix="hermes-archify-plugin-test-") as temp:
            isolated = Path(temp)
            hermes_home = isolated / "hermes-home"
            hermes_home.mkdir()
            env = {
                key: os.environ[key]
                for key in ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP")
                if key in os.environ
            }
            env.update({
                "HOME": str(isolated),
                "USERPROFILE": str(isolated),
                "HERMES_HOME": str(hermes_home),
                "PYTHONPATH": str(source),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUTF8": "1",
            })
            result = subprocess.run(
                [python, "-c", script, str(PLUGIN_ROOT)],
                cwd=isolated,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertTrue(summary["loaded"])
            if summary["engine_installed"]:
                self.assertTrue(summary["doctor_ok"])
                self.assertIsNotNone(summary["delivered_sha256"])


if __name__ == "__main__":
    unittest.main()
