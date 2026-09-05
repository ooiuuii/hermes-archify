"""Small, offline runtime bridge to the separately installed Archify engine."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent


def _failure(action, message, **details):
    return {"ok": False, "action": action, "error": message, **details}


def _absolute_file(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an absolute file path.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute; relative paths are not portable between Hermes tools.")
    return path.resolve()


def execute(action, input_path=None, output_path=None, repo_root=None, *,
            engine_dir=None, node_binary=None, timeout=90):
    """Return JSON-compatible results; never install, upload, or open a browser."""
    if action not in ("doctor", "validate", "deliver"):
        return _failure(action, "Unknown action; choose doctor, validate, or deliver.")
    engine = Path(engine_dir).resolve() if engine_dir else ROOT / ".engine" / "archify"
    cli = engine / "bin" / "archify.mjs"
    resources = {
        "plugin_root": str(ROOT), "engine_dir": str(engine),
        "schema_path": str(engine / "schemas" / "architecture.schema.json"),
        "examples_dir": str(engine / "examples"),
    }
    node = node_binary or shutil.which("node")
    if not node:
        return _failure(action, "Node.js 18 or newer is required. Install Node, then restart Hermes.", **resources)
    if not cli.is_file():
        return _failure(action, "Pinned Archify engine is not installed. Run python setup_engine.py from the plugin directory.", **resources)
    if action == "doctor":
        try:
            probe = subprocess.run([str(node), "--version"], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=10)
            version = probe.stdout.strip()
            match = re.match(r"^v(\d+)\.", version)
            if probe.returncode or not match or int(match[1]) < 18:
                return _failure(action, "Node.js 18 or newer is required.", node_version=version, **resources)
            package = json.loads((engine / "package.json").read_text(encoding="utf-8"))
            return {"ok": True, "action": action, **resources,
                    "node_version": version, "engine_version": package.get("version"),
                    "network_on_render": False, "browser_check": "not_run"}
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            return _failure(action, f"Engine readiness check failed: {exc}", **resources)
    try:
        source = _absolute_file(input_path, "input_path")
        if not source.is_file():
            raise ValueError("input_path does not name an existing file.")
        argv = [str(node), str(cli), action, "architecture", str(source)]
        destination = None
        if action == "deliver":
            destination = _absolute_file(output_path, "output_path")
            if destination.suffix.lower() != ".html":
                raise ValueError("output_path must end in .html.")
            if destination == source:
                raise ValueError("The output must not overwrite the input specification.")
            if not destination.parent.is_dir():
                raise ValueError("Create the output directory before delivery.")
            argv.append(str(destination))
        argv += ["--quality", "showcase", "--json"]
        if repo_root is not None:
            repository = _absolute_file(repo_root, "repo_root")
            if not repository.is_dir():
                raise ValueError("repo_root must be an existing directory.")
            argv += ["--repo-root", str(repository)]
        env = os.environ.copy()
        env["ARCHIFY_UPDATE_CHECK_DISABLED"] = "1"
        completed = subprocess.run(argv, cwd=str(source.parent), env=env,
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=timeout, shell=False)
    except subprocess.TimeoutExpired:
        return _failure(action, "Archify execution timed out; no successful delivery is claimed.")
    except (OSError, ValueError) as exc:
        return _failure(action, str(exc))
    try:
        receipt = json.loads(completed.stdout)
        if not isinstance(receipt, dict):
            raise ValueError("Receipt must be a JSON object")
    except (ValueError, TypeError):
        return _failure(action, "Archify did not return a valid JSON receipt.",
                        exit_code=completed.returncode, stderr=completed.stderr[-4000:])
    if completed.returncode != 0 or receipt.get("ok") is not True:
        return _failure(action, receipt.get("error", "Archify checks failed."),
                        exit_code=completed.returncode, receipt=receipt,
                        diagnostics=receipt.get("diagnostics", []))
    result = {"ok": True, "action": action, "receipt": receipt,
              "browser_check": "not_run", "visual_review": "not_run",
              "source_grounding": "Authored model; checks do not prove runtime architecture."}
    if destination:
        try:
            data = destination.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            expected = receipt.get("artifact", {})
            if digest != expected.get("sha256") or len(data) != expected.get("bytes"):
                raise ValueError("Delivered HTML does not match the engine receipt.")
            result["files"] = [{"role": "diagram", "path": str(destination),
                                "mime": "text/html", "sha256": digest, "bytes": len(data)}]
            # The source is editable. Only label it the delivered source while its bytes
            # still match the frozen input receipt; another process may have edited it.
            specification = receipt.get("specification", {})
            current_source = source.read_bytes()
            if hashlib.sha256(current_source).hexdigest() == specification.get("sha256"):
                result["files"].append({"role": "specification", "path": str(source),
                                        "mime": "application/json", **specification})
            else:
                result["source_warning"] = "Input changed after rendering; it is not the delivered specification."
            result["validation"] = receipt.get("validation", {})
        except (OSError, ValueError) as exc:
            return _failure(action, str(exc), receipt=receipt)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("doctor", "validate", "deliver"))
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--output", dest="output_path")
    parser.add_argument("--repo-root")
    args = parser.parse_args()
    result = execute(**vars(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
