# A/B contrast edit, v3

The v2 edit blended the two workflows. This version uses persistent, named lanes:

- **A / orange:** the inspected native `architecture-diagram` default workflow,
  where Hermes directly writes HTML/inline SVG for the reader to inspect.
- **B / green:** Hermes authors JSON; our bridge invokes pinned Archify checks;
  Hermes fixes diagnostics; the engine delivers an interactive HTML and receipt.

The hook is direct and question-led: an attractive diagram that cannot answer its
reader's question is a poor result. It does **not** assert that every native
diagram is bad, that every agent workflow lacks validation, or that Archify
eliminates semantic mistakes. The generic tangled-module sketch is labeled an
editorial illustration, never a recorded failed Hermes generation.

At 00:00–00:42 and 02:39–03:20, the referenced Better Stack video uses a concrete
failure, a changed production process, and a reading action to explain value.
This edit adopts those broad rhetorical devices, not the original footage,
voice, or a translated script. [Video](https://www.youtube.com/watch?v=iuJszJuiuSg),
[transcript used for wording research](https://tubrief.io/en/videos/iuJszJuiuSg).
Technical claims remain grounded in the inspected source listed in
[v2 evidence notes](../v2/README.md).

## Evidence and scope

Existing real browser captures are reused with exact PNG hashes. There is no new
model generation or same-prompt A/B quality/speed benchmark. Native previews show
the official bundled template. Actual interactive graph shots show the verified
Hermes CLI/tool graph, and the viewer features are credited to Archify.

`check_rejection.py` damages a **copy** of the authored graph by changing one edge
target to `demo_missing_node`, then calls the actual plugin bridge's `validate`.
The observed result was `ok: false`, exit code 1, `layout/constraint`, unknown
target. The existing valid HTML remained unchanged. The screen labels this an
intentional structural test, not a real native Hermes defect or a topology proof.
Validation may temporarily render a candidate; it is not a promise that no
rendering occurs before the check. No bad candidate is presented as a delivery.

No core, installed plugin, engine, credentials, or production settings change.
This is a local media/editing change. Older videos are retained; no upload,
publication, upstream PR, or release is part of this request.

## Reproduce

Use a fresh artifact directory with the exact verified HTML, native template and
saved captures described in v2. Generate `rejection.public.json` with the helper.
Then use the existing media tools with the v3 storyboard:

```powershell
./demo/v2/narrate.ps1 -OutputDirectory <assets> -StoryboardPath ./demo/v3/storyboard.json
python demo/v2/build_video.py --assets <assets> --receipt <original-receipt.json> --font <CJK-font> --storyboard demo/v3/storyboard.json
```

Copy the v3 player to `index.html` in the artifact directory and serve that
specific directory with the range-capable v2 preview helper. Verify the contact
sheet, encoded subtitle frames, full decode, audio and browser chapter seeking.
