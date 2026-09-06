# Verified scope — v0.1.1

The plugin has completed a real, supervised end-to-end Hermes workflow on Windows:
source reading → architecture JSON → registered `archify_diagram` calls → pinned
Archify validation/delivery → actual browser use. This is a working local plugin,
not just a mock UI or a renderer demo. It is **not** a guarantee of zero defects,
unattended one-shot generation, universal compatibility, or semantic correctness.

## Recorded source-grounded Hermes result

- Hermes source revision: `126ff7071b6b755055879648f4e859b3187d0fac`.
- Model/provider: `gpt-5.6-sol` / `openai-codex`, using an existing authorized login.
- Pinned engine: Archify **2.16.0** (official release archive verified by SHA-256).
- Delivered model: **12 nodes, 13 relationships, two views, 34 source references**.
- Engine receipt: **9/9 checks**, zero errors/warnings, source evidence verified
  against the recorded repository/revision. These are source-range/structure
  checks, not proof of the meanings asserted by the diagram's arrows.
- Original interactive HTML SHA-256:
  `83c0782061b045c7c0d3b470a6b9e9aed753e9c8dbb53a0f920295e232c02f18`.
- Browser inspection and continuous capture checked the real delivered page,
  route selection and node/source inspection. The engine's own `browser_check`
  remains `not_run`; the separate observer evidence does not rewrite that receipt.
- The model was supervised and corrected. Early Windows path handling, missing
  repository metadata and unattended terminal approval were not successful runs.
  The skill now explains these constraints instead of hiding them.

## Release-candidate local tests — 2026-09-06

Windows 11 x64 build 26200; Python **3.11.15**; Node **22.22.3**; Archify **2.16.0**;
the real Hermes checkout at the revision above.

```powershell
$env:HERMES_SOURCE_DIR = '<existing Hermes checkout>'
$env:HERMES_PYTHON = '<Hermes Python environment executable>'
python -m unittest discover -s tests -v
```

The existing suite passed **19 tests, 0 failures, 0 skips**. It covers the bridge,
explicit checksum-pinned engine setup, real rendering and last-good preservation,
registration without starting processes, and the actual Hermes plugin
loader/registry. The integration child receives a fresh temporary `HERMES_HOME`
and a credential-free environment. The initial pass used `ee67a6a`; release edits
since then change documentation, packaging and version labels, not the renderer.

The real loader's `registry.dispatch` → bridge → engine delivery was explicitly
confirmed again without replacing its result or process: loaded/enabled, doctor
ready, engine installed, and actual delivered HTML. Namespaced skill loading and
the optional ordinary `/archify` discovery route both passed. The delivered
fixture HTML hash was
`3da57f96f0b84dd2435509220185c856edfd15a701be0729551f0ef0d5256719`.

The daily Windows installation's bridge, registration, setup and lock files match
the tested implementation. Both installed skill copies contain the tested
source-grounding instructions; their older version label does not change the
behavior. No daily configuration, login, engine or running session was changed
by this release verification.

## Demo verification

V5 is 3:42, 1920 × 1080 at 30 fps with Chinese narration and 43 burned-in subtitles.
Complete FFmpeg decoding and browser playback passed. Subtitle regression tests
passed. Only the native segment changed from V4; the other nine scene segments
remain identical. Original final MP4 SHA-256:
`5f38f60079b7b3f261ddf52561578efd44af3fa31436be7774d4ef6023c74c09`.

A is a new isolated Hermes run using the unmodified native `architecture-diagram`
skill, without Archify. It generated a real standalone HTML/SVG and source notes;
its PNG is a browser screenshot. B is the earlier supervised plugin result.
Three product segments are continuous recordings of browser input, not recordings
of live model generation. Other scenes are explanatory visuals.

The native sample is useful, includes source notes and also contains a potentially
ambiguous history→executor arrow. That is not a claim that all native output is
bad, or that Archify's structural validator would detect that semantic ambiguity.

## Limits and remaining prerequisites

- Supported **tested local workflow**: the Windows environment above. CI also
  runs unit/real-engine tests on Windows and Linux; it does not run a live model.
  This release does not claim a new macOS or Linux Hermes live-model end-to-end run.
- Install/enable the plugin, explicitly install its pinned engine, and restart
  Hermes sessions. Bundled skill loading is explicit; ordinary skill discovery
  needs the separate optional skill installation.
- Models can author invalid or misleading data. Read diagnostics and inspect the
  output; a successful render is not an accuracy guarantee.
- Repository files and output paths must exist on the **Hermes host**. Remote
  terminal paths do not automatically refer to that host's filesystem.
- Terminal operations still require normal approvals. An unattended query with
  no approval responder cannot silently bypass them.
- No plugin marketplace submission, official endorsement, hosted service or
  automatic publishing is implied by a GitHub release.
- Public downloads exclude private logs, credentials, profiles and databases.
  Source-note paths are normalized, with original and published hashes separated.

See [the release](https://github.com/ooiuuii/hermes-archify/releases/tag/v0.1.1)
for the actual outputs, evidence and checksums. CI results remain available in
[GitHub Actions](https://github.com/ooiuuii/hermes-archify/actions/workflows/test.yml).
