# Course Delivery Standard v1 — adoption roadmap

This roadmap tracks operational adoption of `course-delivery-standard-v1.md`. It does not redefine each course curriculum.

| Course | Profile | Initial target | Current direction |
|---|---|---:|---|
| TPSI quinto | Software development | Level 3 | **Pilot Level 3 verified on branch/PR #26**: teacher/student guides, delivery changelog, 19 modular decks, HTML/PDF/PPTX CI bundle, manifest/checksums, ordinary Quality green. |
| TPSI quarto | Software development | Level 2→3 | Next consumer: add dashboard/slide/lab mapping, teacher/student delivery surfaces and generated artifacts using the TPSI5 artifact contract as reference. |
| Romeo | Robotics | Level 3 | Add simulator workflow, install guide, robot self-test, safe physical commissioning and teaching decks. |
| C | Software development / legacy | Level 1→2 | Preserve the large existing body while adding a navigable dashboard, decks and guides incrementally. |
| Hardware/Proxmox | Hardware/infrastructure | Level 2→3 | Add topology/compatibility/safety content, virtual labs and reproducible classroom setup. |
| Python (future) | Software development | Level 3 from inception | Start natively with dashboard, lessons, slides, guides, labs and CI-generated artifacts. |

## Verified pilot evidence

TPSI quinto source head:

```text
5c249eece46faef49ca6c0ef710b90c535739e44
```

- Slides #10 / run `32510302002`: SUCCESS.
- Artifact ID `9456794079`, digest `sha256:9e4172336460fc9e8450f13d2fc6a44b77a2c36b88b9cca0c5e26f48c198eb99`.
- Bundle: 20 HTML + 20 PDF + 20 PPTX + manifest/checksums.
- Quality #203 / run `32510301892`: SUCCESS across Ubuntu Python 3.11/3.12 and Windows Python 3.11.

The reproducible generated-artifact rules extracted from this pilot are documented in `course-delivery-artifact-contract-v1.md`.

## Rollout rule

Each course gets its own PR(s), CI and acceptance evidence. Cross-course standard changes remain in `2cornot2c`; course-specific teaching content remains in the course repository.

## In-year rule

Delivery material is expected to evolve during teaching. A correction should be applied to canonical source and recorded in the course delivery changelog. Curriculum-significant changes remain subject to explicit curriculum review/versioning.
