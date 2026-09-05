# Hermes Archify

[![Verify extension](https://github.com/ooiuuii/hermes-archify/actions/workflows/test.yml/badge.svg)](https://github.com/ooiuuii/hermes-archify/actions/workflows/test.yml)

**Hermes understands the source. Archify checks and renders the diagram.**

A small, independent Hermes plugin and skill for editable, interactive architecture
diagrams. No Hermes core patches, cloud service, API key, or npm install required.

## What it adds

- Source-reading guidance and an editable, typed JSON model, not just generated HTML.
- A single `archify_diagram` tool: readiness, validation, and checked delivery.
- Precise engine diagnostics for fixing invalid models.
- HTML delivery with verified SHA-256/byte metadata; failed engine updates keep the
  previous successful HTML.
- Archify's real viewer: guided views, node relationships, routes, and themes.

This does **not** replace Hermes' existing Mermaid, `architecture-diagram`, or
`code-wiki` skills. Use it when interactive exploration and a reproducible model
justify the extra engine. It does not automatically discover runtime topology.

## Install

Requires Hermes with standalone plugins, Python 3.10+, and Node.js 18+ on PATH.
The tool runs on the **Hermes host filesystem**. If your terminal backend is remote
or containerized, transfer files to the host first; matching path strings do not
make two filesystems the same.

```text
hermes plugins install ooiuuii/hermes-archify --no-enable
```

Locate the installed directory under your active Hermes home:
`<HERMES_HOME>/plugins/hermes-archify` (normally `~/.hermes/plugins/hermes-archify`).
Profiles or a custom `HERMES_HOME` may use a different location.

From that directory, run:

```text
python setup_engine.py
python bridge.py doctor
hermes plugins enable hermes-archify --no-allow-tool-override
```

Restart your Hermes session after enabling the plugin. If a gateway is running,
restart it through your normal service workflow; the installer does not restart it.

Setup explicitly downloads the official Archify **v2.16.0** ZIP, checks its size and
SHA-256 from [engine-lock.json](engine-lock.json), and retains the complete package
and upstream notices. Tool calls never install or update it. For offline setup,
use `python setup_engine.py --archive /absolute/path/to/archify.zip`; the exact same
checksum is required. Existing engine directories are never overwritten by setup.

## Use in Hermes

> Load the skill `hermes-archify:archify`. Read the entry points and relevant source
> of this repository, then create an interactive architecture diagram. Distinguish
> observed relationships from inference. Validate and deliver it to the absolute
> output path I provide; report which checks actually ran.

The plugin bundles an explicitly loadable skill. Hermes currently does not put
plugin-bundled skills into ordinary skill discovery. For automatic skill discovery
and `/archify`, you may **explicitly** install a separate copy:

```text
hermes skills install ooiuuii/hermes-archify/skills/archify
```

The plugin still needs to be enabled. The skill obtains engine/schema paths from
`doctor`, so a separately installed skill does not guess where the plugin lives.

Example tool input:

```json
{
  "action": "deliver",
  "input_path": "/absolute/path/architecture.json",
  "output_path": "/absolute/path/architecture.html"
}
```

Use native absolute Windows paths on Windows. Create the output directory first.
The model should contain `meta.quality_profile: "showcase"`. A failed result has
`ok: false` and an error or engine diagnostics. A successful delivery returns file
paths plus an **inline JSON receipt**; it does not create a separate receipt file.

## Try the included example

From a checkout or the installed plugin directory:

```text
python demo/build_proof.py
```

This runs the real bridge and pinned engine on the included, pre-authored Archify
pipeline example. It writes `artifacts/demo/architecture.html` and a sanitized
receipt, including a real failed-update/last-good-file check. Open the HTML locally.
It is not a recording of an LLM autonomously analyzing a repository.

See [example provenance](examples/README.md) and [demo/README.md](demo/README.md).

## Evidence boundaries

| Result | What it establishes |
| --- | --- |
| Engine validation | The authored model and generated artifact pass the engine's checks. |
| Receipt/hash verification | Delivered HTML bytes match the successful engine receipt. |
| Browser inspection | The actual page loads and its tested interactions work. |
| Source grounding | A human/agent read and checked the referenced source; not runtime tracing. |

Runtime tool results always report browser and visual checks as `not_run` because
the bridge does not run a browser. A separate observer can report its own evidence.
Don't treat an old file still existing after a failed update as a successful update.
Archify's `--repo-root` evidence checks are available via `repo_root` for models
that actually include its supported repository/source fields.

No telemetry or network requests occur in this extension's rendering path. Explicit
engine setup downloads from GitHub. Keep sensitive repository diagrams local unless
you have permission to share them. Any model/provider used by Hermes has its own
data-handling behavior; this extension does not change that.

## Verify and develop

```text
python -m unittest discover -s tests -v
```

Tests need no third-party Python packages. With the engine installed, the suite
exercises real delivery and last-good preservation. For the optional **real Hermes
loader/registry** integration test, set `HERMES_SOURCE_DIR` to a Hermes checkout and
run with its Python environment (`HERMES_PYTHON` can select it). That child process
gets a fresh temporary Hermes home and a credential-free environment. Without that
checkout the integration test is explicitly skipped, not reported as passed.

CI runs unit/real-engine tests on Windows and Linux. It does not claim a live-model
or full Hermes test run. Browser demo code is development-only, not a new Hermes UI.

## Update and uninstall

Update the plugin through Hermes' plugin workflow, then check its release notes
before changing the separately pinned engine. The setup script deliberately refuses
to overwrite an existing engine; retain a backup before a deliberate engine upgrade.

```text
hermes plugins disable hermes-archify
```

Restart affected Hermes sessions. You can then remove only the installed
`<HERMES_HOME>/plugins/hermes-archify` directory. If you separately installed the
ordinary skill, remove only its `skills/archify` directory too. Your diagrams live
where you chose to save them; disabling/removing the plugin should not delete them.

## Credits

Powered by [Archify](https://github.com/tt-a1i/archify), created by tt-a1i, building
on Cocoon AI's architecture-diagram-generator. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
This is a community extension, **not an official Nous Research or Archify product**.
