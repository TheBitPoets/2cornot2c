# Course Delivery Standard v1 — adoption roadmap

This roadmap tracks operational adoption of `course-delivery-standard-v1.md`. It does not redefine each course curriculum.

| Course | Profile | Initial target | Current direction |
|---|---|---:|---|
| TPSI quinto | Software development | Level 3 | **Level 3 verified on PR #26**: teacher/student guides, delivery changelog, 19 modular decks, HTML/PDF/PPTX CI bundle, manifest/checksums, ordinary Quality green. |
| TPSI quarto | Software development | Level 2→3 | **Delivery layer implemented on PR #4**, preserving Content Pack `0.1.0 / draft`: dashboard, teacher/student guides, 7 decks and reproducible artifact builder. Acceptance is blocked by private-repository Actions jobs failing before any workflow step executes; PR remains draft/unmerged. |
| Romeo | Robotics | Level 3 | **Level 3 verified on PR #14**: existing Sphinx/student/teacher/operations/hardware docs reused, 10 macro-decks cover 20+23 units, simulator→real gate, HTML/PDF/PPTX bundle and Quality/Slides green. Hardware doctor implementation remains separate in PR #15 and physical commissioning is not claimed complete. |
| C | Software development / legacy | Level 1→2 | Preserve the large existing body while adding a navigable dashboard, decks and guides incrementally. |
| Hardware/Proxmox | Hardware/infrastructure | Level 2→3 | **Delivery layer implemented on PR #27**: dashboard, changelog, 14 decks (map + U01–U12 + optional Proxmox Advanced), reproducible artifact builder/test/workflow. Core `1.1.0` / 12 units / 60h / 28 Activity and optional Proxmox `0.1.0` boundary are enforced. Acceptance is blocked by the same private-repository pre-step Actions failure tracked in #750. |
| Python (future) | Software development | Level 3 from inception | Start natively with dashboard, lessons, slides, guides, labs and CI-generated artifacts. |

## Verified consumer evidence

### TPSI quinto

Source head:

```text
5c249eece46faef49ca6c0ef710b90c535739e44
```

- Slides #10 / run `32510302002`: SUCCESS.
- Artifact ID `9456794079`, digest `sha256:9e4172336460fc9e8450f13d2fc6a44b77a2c36b88b9cca0c5e26f48c198eb99`.
- Bundle: 20 HTML + 20 PDF + 20 PPTX + manifest/checksums.
- Quality #203 / run `32510301892`: SUCCESS across Ubuntu Python 3.11/3.12 and Windows Python 3.11.

### Romeo

Source head:

```text
d975478c80730ccb056b0877e6c924394a2281e3
```

- Quality #155 / run `32518544695`: SUCCESS.
- Slides #7 / run `32518544771`: SUCCESS.
- Artifact ID `9459704131`, digest `sha256:b7e32d04cd426459f4ad7571aa7f8bcabae6ba271cfae611c9e138c1f5c2645b`.
- Bundle: 10 HTML + 10 PDF + 10 PPTX + manifest/checksums.
- Robotics boundary: `romeo-doctor` is installation-versioned; even when present it does not replace supervised physical commissioning. PR #15 is implementation work and explicitly reports no reachable physical target.

The reproducible generated-artifact rules extracted from these consumers are documented in `course-delivery-artifact-contract-v1.md`.

## Blocked private consumers

The cross-course infrastructure blocker is tracked in **#750**. GitHub Status currently reports Actions operational, while GitHub's billing model treats private-repository hosted-runner usage differently from public repositories. Therefore organization billing/quota/budget and private Actions policies are the first settings to verify before changing workflow code.

### TPSI quarto

PR #4 head:

```text
e57eb5c18ad7551bf9606ed1768feec01ed531b0
```

Quality #26 (`32511595832`) and Slides #1 (`32511595866`) terminate before any executable workflow step is recorded. A Slides rerun reproduces the same pre-step failure. TPSI quarto is **not** marked Level 3 verified and the PR must remain draft/unmerged.

### Hardware/Proxmox

PR #27 head:

```text
1c5cf946e9f36015f55f06f13fe8d05e3558e79f
```

The consumer preserves core Course Bundle `1.1.0`, 12 units, 60 hours, 28 Activity and optional Proxmox Advanced `0.1.0`, with the latter explicitly outside the core hours. Four independent workflows all terminate before checkout with `steps=null`:

- Quality #316 / `32519780916`;
- Slides #1 / `32519781059`;
- Build student manual #75 / `32519780980`;
- Build teacher manual #66 / `32519780912`.

Because both legacy workflows and the new Slides workflow fail before user code executes, Hardware/Proxmox is **implemented but not Level 3 verified** until #750 is resolved and the same head or a reviewed successor is rerun.

## Rollout rule

Each course gets its own PR(s), CI and acceptance evidence. Cross-course standard changes remain in `2cornot2c`; course-specific teaching content remains in the course repository.

## In-year rule

Delivery material is expected to evolve during teaching. A correction should be applied to canonical source and recorded in the course delivery changelog. Curriculum-significant changes remain subject to explicit curriculum review/versioning.
