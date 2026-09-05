"""Hermes registration only; the local engine is invoked on explicit tool calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TOOL_SCHEMA = {
    "name": "archify_diagram",
    "description": (
        "Check or deliver an interactive architecture diagram using the pinned "
        "local Archify engine. Before first use, read the bundled skill "
        "hermes-archify:archify. The input is source-grounded architecture JSON; "
        "validation does not prove runtime topology. Never installs the engine."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["doctor", "validate", "deliver"],
                "description": (
                    "doctor checks engine readiness and reports resource paths; "
                    "validate checks an authored architecture model; "
                    "deliver validates and writes interactive HTML plus a receipt."
                ),
            },
            "input_path": {
                "type": "string",
                "description": "Absolute architecture JSON file path; required for validate and deliver.",
            },
            "output_path": {
                "type": "string",
                "description": "Absolute .html output file path; required for deliver.",
            },
            "repo_root": {
                "type": "string",
                "description": "Absolute source repository root for checking source references, when applicable.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}


def archify_diagram(args: dict[str, Any], **kwargs: Any) -> str:
    """Adapt Hermes' args/keyword-context contract to the standalone bridge."""
    action = args.get("action") if isinstance(args, dict) else None
    try:
        if not isinstance(args, dict):
            raise ValueError("Tool arguments must be a JSON object.")
        from .bridge import execute

        result = execute(
            action=action,
            input_path=args.get("input_path"),
            output_path=args.get("output_path"),
            repo_root=args.get("repo_root"),
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps(
            {"ok": False, "action": action, "error": str(exc)},
            ensure_ascii=False,
        )


def register(ctx: Any) -> None:
    """Expose one model tool and an explicitly loadable, namespaced skill."""
    ctx.register_tool(
        name="archify_diagram",
        toolset="archify",
        schema=TOOL_SCHEMA,
        handler=archify_diagram,
    )
    ctx.register_skill(
        "archify",
        Path(__file__).parent / "skills" / "archify" / "SKILL.md",
        "Deliver source-grounded interactive architecture diagrams.",
    )
