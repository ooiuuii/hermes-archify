# Workflow-first demo, v2

This edit explains what the existing Hermes `architecture-diagram` skill already
does, what the independent bridge adds, and how to ask a useful architecture
question. It is a narrated explainer with **real browser interaction states,
edited step by step**, not a continuous live recording or a new model run.

## Editorial boundaries

- Native Hermes already produces HTML with inline SVG, has design/layout rules,
  and is a sensible choice for lightweight static explanations. The inspected
  bundled skill requires no JavaScript. Its original template preview is labeled
  as a template, **not an equal-prompt A/B generation experiment**.
- Hermes authors the structured model. This plugin calls pinned Archify
  validate/deliver; Archify supplies the renderer, viewer and graph interactions.
  Do not attribute those viewer features to our bridge.
- One file should answer a concrete question; prefer 8–12 major components and
  source-supported relationships. Better prompts also help the native skill.
- A path through authored edges is not a runtime trace. Reference verification
  checks repository/revision/files/ranges, not whether every arrow is true.
- Passing deterministic checks, browser inspection and semantic review are
  separate claims. Do not claim perfect accuracy, superior speed/cost, or that
  native Hermes could never be extended with links or interactivity.
- Do not claim the opened HTML never uses the network: both inspected templates
  reference Google Fonts. Engine execution and browser resource loading differ.
- No original Better Stack footage, transcript audio, private logs, provider
  credentials or desktop screens are used. Narration is local Windows TTS.

## Evidence used

The native baseline is the bundled skill/template at Hermes revision
`126ff7071b6b755055879648f4e859b3187d0fac`:

- [Skill](https://github.com/NousResearch/hermes-agent/blob/126ff7071b6b755055879648f4e859b3187d0fac/skills/creative/architecture-diagram/SKILL.md)
- [Template](https://github.com/NousResearch/hermes-agent/blob/126ff7071b6b755055879648f4e859b3187d0fac/skills/creative/architecture-diagram/templates/template.html)

The actual recorded HTML was authored in a real Hermes run, then supervised and
corrected before delivery. It contains 12 nodes, 13 edges, 34 source references,
and 2 guided chapters. Expected SHA-256:
`83c0782061b045c7c0d3b470a6b9e9aed753e9c8dbb53a0f920295e232c02f18`.
The bridge candidate used is `04bcfc9`; Archify engine is pinned to v2.16.0.

The saved delivery receipt records 9/9 checks and 0 errors/warnings. Its
generation-time `browser_check: not_run` remains unchanged. A separate subsequent
browser smoke record passed; it is not an engine-generated visual certificate.
This demo does not imply that this local candidate is already a public release.

Interaction proof retained beside the captures:

1. CLI/model-loop chapter and tools/plugin chapter.
2. Path **Hermes CLI → hermes-archify**, 6 nodes / 5 authored directed hops.
3. Search `tool_registry`, open source passport, show pinned `registry.py` ranges.

Method reference: Better Stack, *This Open-Source Tool Makes Claude Create
Architecture Diagrams*, September 4, 2026.
[1:34–2:10](https://www.youtube.com/watch?v=iuJszJuiuSg&t=94s) discusses narrowing
the question; [5:53–6:03](https://www.youtube.com/watch?v=iuJszJuiuSg&t=353s)
warns that a valid graph can describe the wrong system. The native transcript
panel did not load during research, so wording was checked against the
[public transcript](https://tubrief.io/en/videos/iuJszJuiuSg), with technical claims
cross-checked against [Archify's official guide](https://github.com/tt-a1i/archify/blob/main/docs/authoring-cookbook.zh-CN.md).

## Recommended prompt

> 用 Archify 只回答：一次 Hermes 请求怎样从 CLI 进入模型循环，再分派到工具？
> 读取本机源码，最多 12 个主要节点。组件和关系必须有源码依据；不确定的明确标注，
> 不把文件相邻当作调用关系，不扩展无关模块。先编写结构化 JSON，运行 validate，
> 修正本题相关诊断，再 deliver。交付 HTML、JSON 和回执；最后检查关键箭头和实际页面。

## Rebuild

Prerequisites: Python with Pillow, FFmpeg/FFprobe, a local Chinese font, and on
Windows an installed `System.Speech` Chinese voice. No speech API is used.

1. Use a fresh artifact directory. Put authorized real browser screenshots under
   `captures/`, using the filenames in `storyboard.json`. Preserve source PNGs.
2. Copy the exact final HTML, native template and the original receipt into the
   artifact directory. Never serve a directory containing credentials or raw logs.
3. Run `narrate.ps1 -OutputDirectory <artifact-directory>`. It refuses to overwrite
   existing audio. Synthetic narration is disclosed in the player and credits.
4. Run `python demo/v2/build_video.py --assets <artifact-directory>
   --receipt <original-receipt.json> --font <CJK-font-file>`.
5. Inspect the contact sheet and representative full-resolution frames, validate
   the MP4 audio/video streams and duration, and play it in a browser.

For chapter seeking in the local player, use the optional `serve_preview.py`
helper with installed Starlette (FileResponse range support) and Uvicorn:

```powershell
python demo/v2/serve_preview.py --directory <artifact-directory> --port 8769
```

It binds only to loopback. A basic server without HTTP byte-range support can
play the video but may fail to seek; this is a preview-server constraint, not an
Archify/plugin failure. Copy `player.html` to the artifact directory as
`index.html` before starting the server.

The build refuses to replace an existing final MP4. Generated media, sanitized
receipt, timing/capture manifests and the local player stay under the ignored
artifact directory. This change does not alter plugin code or publish a release.
