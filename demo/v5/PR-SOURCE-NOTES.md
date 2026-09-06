# PR summary images and the native architecture skill

Checked 2026-09-06, using live GitHub PR bodies and the installed Hermes skill.

## Confirmed

Teknium introduced the built-in `architecture-diagram` skill in
[Hermes PR #9906](https://github.com/NousResearch/hermes-agent/pull/9906), merged
2026-04-14. Its documented method is to read the design instructions/template and
write a standalone HTML file containing SVG and CSS. The current inspected native
skill explicitly excludes JavaScript. The file can be displayed in a browser and
captured as an image, but that possibility alone does not establish provenance.

## Not established

These Teknium PR bodies end in an **Infographic** section linking to a PNG:

- [#103943](https://github.com/NousResearch/hermes-agent/pull/103943), created
  2026-09-05 23:32:52 UTC.
- [#103884](https://github.com/NousResearch/hermes-agent/pull/103884), created
  2026-09-05 20:29:40 UTC.
- [#103821](https://github.com/NousResearch/hermes-agent/pull/103821), created
  2026-09-05 18:13:35 UTC.

Those inspected bodies do not identify which skill, model or generation call made
their summary images. Hosting on a `fal.media` domain is not proof of a particular
generator. They must not be labeled as outputs of `architecture-diagram` without
additional evidence. We did not download or reuse those images in the demo.

There is, however, explicit documentation of the project's PR-image publishing
workflow in [infographic-check.yml, lines 3–7](https://github.com/NousResearch/hermes-agent/blob/126ff7071b6b755055879648f4e859b3187d0fac/.github/workflows/infographic-check.yml#L3-L7):
PR infographics are rendered to an image-provider URL and embedded in the PR body,
not committed as image binaries. That establishes the documented workflow, not
which skill generated any particular PNG. The bundled
[baoyu-infographic skill](https://github.com/NousResearch/hermes-agent/blob/126ff7071b6b755055879648f4e859b3187d0fac/skills/creative/baoyu-infographic/SKILL.md#L210-L217)
uses image generation, but the inspected PR instructions do not mandate it.

V5 therefore uses a new, recorded local Hermes native-skill run as its A example,
and labels it with that actual provenance. It does not claim Teknium created,
endorsed or used our demo or plugin.
