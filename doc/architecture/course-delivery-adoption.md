# Course Delivery Standard v1 — adoption roadmap

This roadmap tracks operational adoption of `course-delivery-standard-v1.md`. It does not redefine each course curriculum.

| Course | Profile | Initial target | Current direction |
|---|---|---:|---|
| TPSI quinto | Software development | Level 3 | Complete module decks, teacher/student guides, generated slide artifacts and link checks. |
| TPSI quarto | Software development | Level 2→3 | Add dashboard/slide/lab mapping, then generated artifacts. |
| Romeo | Robotics | Level 3 | Add simulator workflow, install guide, robot self-test, safe physical commissioning and teaching decks. |
| C | Software development / legacy | Level 1→2 | Preserve the large existing body while adding a navigable dashboard, decks and guides incrementally. |
| Hardware/Proxmox | Hardware/infrastructure | Level 2→3 | Add topology/compatibility/safety content, virtual labs and reproducible classroom setup. |
| Python (future) | Software development | Level 3 from inception | Start natively with dashboard, lessons, slides, guides, labs and CI-generated artifacts. |

## Rollout rule

Each course gets its own PR(s), CI and acceptance evidence. Cross-course standard changes remain in `2cornot2c`; course-specific teaching content remains in the course repository.

## In-year rule

Delivery material is expected to evolve during teaching. A correction should be applied to canonical source and recorded in the course delivery changelog. Curriculum-significant changes remain subject to explicit curriculum review/versioning.
