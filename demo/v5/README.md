# V5: an actual native-skill baseline

This edit replaces only V4 scene `02-native`. The other nine scene MP4s, all
narration, and the 43 subtitle cues are preserved. It is a reading-workflow demo,
not a controlled model accuracy, speed, or cost comparison.

## A was really generated

`run_native.py` launched installed Hermes at revision
`126ff7071b6b755055879648f4e859b3187d0fac`, with a fresh isolated profile and
only the file/skills toolsets. It copied the unmodified native
`architecture-diagram` instructions and template. No Archify plugin was installed
in this profile. The existing login was used only for the intended inference
endpoint, through an anonymous stdin pipe; no credentials are recorded in public
metadata or command arguments.

The published query template is in `native-task.md`; `--hermes-source` supplies
the local checkout and the runner supplies its plugin root. The original rendered
prompt and historical hash are retained privately, not replaced by the template's
hash. No account-specific home directory is committed in the publication history.
The successful run took 464.71 seconds
and wrote a new 14,425-byte HTML/SVG plus source notes. `verify_native.py`
confirmed the recorded skill/template reads, real writes, one SVG, no JavaScript,
and no Archify tool invocation. These are provenance/basic file checks, not a
semantic correctness certificate. Windows search-path errors occurred; the agent
recovered through direct source-file reads. We did not change Hermes core.

The run's private log and database are outside this repository. Only local
delivery artifacts are collected under ignored `artifacts/demo-v5`. The source
notes and diagram retain useful local source paths; review/redact those before a
future public upload. Nothing was uploaded or pushed for this edit.

## Real browser reading

Serve only the generated public-artifact folder, never the profile or private log.
Use the supported in-app browser session, take the PNG before the temporary cursor
overlay, then invoke `record-native.mjs` with that session's tab and CDP capability.
The recorder resolves actual visible labels and sends actual mouse/wheel events.
It adds no diagram interactions. Reloading removes the recording-only cursor.

The accepted take has 142 live Chromium screencast frames, 280 recorded mouse
moves and two wheel events over 27.004 seconds. A static page needed a real mouse
event after screencast startup to trigger its first paint. An initial empty take
was rejected and is not used. The final uses only the first 24.866667 seconds;
it never extends the recording to fill narration. Excess raw encoding tail is
not used. Input coordinates, DOM checkpoints, frame timestamps and raw clips are
kept with the local artifacts.

After the native evidence and `recordings/02-native.*` are in a fresh assets
directory:

```powershell
python demo/v5/compose.py --previous E:/hermes-archify/artifacts/demo-v4 --assets E:/hermes-archify/artifacts/demo-v5
```

This command refuses to overwrite a finished edit. It verifies prior segment
hashes, reuses their audio, letterboxes the complete browser viewport, and burns
the original corrected subtitles. The separate quality report records final
playback checks; the manifest retains its honest build-time pending-review value.

## Interpretation

A has useful source summaries and line numbers, not just decorative boxes. It
requires ordinary reading and scrolling. B reuses the earlier supervised plugin
output with Archify's path/source interfaces and structural checks. Neither
workflow certifies runtime behavior or semantic truth. The source audit found one
ambiguous A arrow: prompt/history visually feeds the executor, whereas the actual
conversation loop dispatches the model's response. That is a limitation of this
sample, not evidence that all native diagrams fail; structural validation alone
would not prove that relationship correct either.

For Teknium's PR images, see `PR-SOURCE-NOTES.md`. The PR Infographic workflow is
documented, but the inspected images do not identify their generating skill.
