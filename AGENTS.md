# Hermes Archify contributor guide

This is an independent Hermes extension, not a Hermes core fork.

## Scope

One workflow: source-grounded architecture JSON -> pinned Archify CLI -> checked,
interactive HTML plus an honest machine-readable receipt. Hermes reads the source;
Archify validates and renders the authored model. Neither proves runtime topology.

- Keep the bridge standard-library-only and invoke Node with argument arrays.
- No engine execution or installation during Python import or plugin registration.
- No telemetry, automatic updates, cloud upload, service startup, or core patches.
- Rendering errors must not replace an existing successful HTML artifact.
- Browser inspection and visual judgement are separate from deterministic checks.
- Use isolated HERMES_HOME for integration tests; never modify production settings.
- Test observable behavior, including real engine execution. Do not substitute mocks
  for the plugin loader/renderer smoke test.
- Preserve upstream license notices. The engine is downloaded separately, pinned by
  release and SHA-256, never silently fetched during a model tool call.

## Ownership during initial implementation

- Main agent: bridge, engine setup, README, CI, integration, recording, Git operations.
- Hermes integration agent: plugin.yaml, __init__.py, skills/archify/SKILL.md.
- Engine agent: tests/test_bridge.py and examples/ once the interface is confirmed.

## Verification and review boundary

Run focused unit tests, real-engine last-good behavior, and isolated Hermes loading.
One scoped structured review before shipping; fix concrete in-scope blockers only.
Viewer changes, other diagram kinds, hosted sharing, MCP servers and Hermes core
interfaces are out of scope for v0.1.
