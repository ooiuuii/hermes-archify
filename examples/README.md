# Archify pipeline example

[`archify-pipeline.architecture.json`](archify-pipeline.architecture.json) explains
the real Archify project's authoring and rendering pipeline. It is a small,
manually authored source model, not an automatically discovered runtime trace.

## Provenance

This example adapts Archify's
[`archify-repo-grid.architecture.json`](https://github.com/tt-a1i/archify/blob/c826e6c3a7abad19c0f3cd1ca57207d54b1ad8de/examples/archify-repo-grid.architecture.json)
at release **v2.16.0**, commit
`c826e6c3a7abad19c0f3cd1ca57207d54b1ad8de` (MIT, copyright 2026 tt-a1i and
2025 Cocoon AI). The upstream topology is a conceptual authoring/rendering
pipeline; its boxes do not imply separate services or network hops.

The derivative adds stable relationship IDs, two guided views, a showcase quality
profile, revised spacing and explanatory cards. `SKILL.md` points toward its
consumer, the agent. The schema node describes bundled validators rather than an
AJV package that users must install at runtime. No third-party logos are used.

The model is grounded in the upstream
[CLI](https://github.com/tt-a1i/archify/blob/c826e6c3a7abad19c0f3cd1ca57207d54b1ad8de/archify/bin/archify.mjs),
[schema contract](https://github.com/tt-a1i/archify/blob/c826e6c3a7abad19c0f3cd1ca57207d54b1ad8de/archify/schemas/README.md)
and [delivery contract](https://github.com/tt-a1i/archify/blob/c826e6c3a7abad19c0f3cd1ca57207d54b1ad8de/archify/references/delivery-contract.md).
It intentionally omits Git-verified `meta.repository` / `sources` fields: those
require a separate matching upstream checkout and `repo_root` verification.

## Render and explore

Complete the engine setup in the [project README](../README.md) first. From this
repository root, the bridge API accepts absolute paths:

```python
import json
from pathlib import Path
from bridge import execute

root = Path.cwd().resolve()
(root / "artifacts").mkdir(exist_ok=True)
result = execute(
    "deliver",
    input_path=str(root / "examples" / "archify-pipeline.architecture.json"),
    output_path=str(root / "artifacts" / "archify-pipeline.html"),
)
print(json.dumps(result, indent=2))
```

Only open the resulting HTML after `ok` is true. The delivery receipt describes
deterministic checks, not browser behavior or visual approval. A failed update
must retain the previous successful HTML; that old file is not evidence that the
new source succeeded.

The two authored views are **Render and deliver** (`render-path`) and
**Authoring and validation** (`authoring-contract`). A short demonstration can
show the successful receipt, open the HTML, select both views, trace the directed
route from `user` to `html`, and switch between light and dark themes. The views
and route explore only relationships in this JSON. Record actual interaction
with the artifact; do not substitute an animation mockup or label it as live
infrastructure discovery.

If the source changes, rerun delivery before collecting browser evidence or
recording a new demo. Keep the JSON and the latest receipt alongside the result
so readers can reproduce it.
