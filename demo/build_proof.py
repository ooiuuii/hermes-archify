"""Run the real bridge on the public example; write only sanitized demo evidence."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bridge import execute


def main():
    destination = ROOT / "artifacts" / "demo"
    destination.mkdir(parents=True, exist_ok=True)
    source = ROOT / "examples" / "archify-pipeline.architecture.json"
    output = destination / "architecture.html"
    result = execute("deliver", str(source), str(output))
    if not result["ok"]:
        print(json.dumps(result, indent=2))
        return 1
    before = output.read_bytes()
    with tempfile.TemporaryDirectory(prefix="last-good-", dir=destination) as temp:
        invalid = Path(temp) / "invalid.json"
        invalid.write_text('{"broken":', encoding="utf-8")
        failed = execute("deliver", str(invalid), str(output))
    retained = not failed["ok"] and output.read_bytes() == before
    if not retained:
        raise RuntimeError("Last-good preservation failed; demo evidence was not published.")
    receipt = result["receipt"]
    public = {
        "ok": True, "engine": "Archify v2.16.0", "action": "deliver",
        "artifact": {"name": output.name, **receipt["artifact"]},
        "specification": {"name": source.name, **receipt["specification"]},
        "validation": receipt["validation"], "browser_check": "not_run",
        "hermes_plugin_smoke": "not_run",
        "source_grounding": "Pre-authored, source-grounded Archify pipeline; not runtime topology proof.",
        "last_good_preserved": retained,
        "failed_update_stage": failed.get("receipt", {}).get("stage"),
    }
    (destination / "receipt.public.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "artifact": "artifacts/demo/architecture.html",
                      "receipt": "artifacts/demo/receipt.public.json",
                      "sha256": hashlib.sha256(before).hexdigest(),
                      "last_good_preserved": retained}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
