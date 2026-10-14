# Course Delivery Checklist

Use this checklist when creating or reviewing a course delivery layer.

## Repository navigation

- [ ] Root README explains the course to a new teacher/student.
- [ ] README has clickable module/UDA index.
- [ ] Every module links to lesson material.
- [ ] Every module links to slides or explicitly says slides are pending.
- [ ] Every module links to Activity/lab entry points where applicable.
- [ ] Longitudinal project milestones are visible from the README.

## Slides

- [ ] Slides source lives under `slides/<course-id>/`.
- [ ] Slide anchors or filenames are stable.
- [ ] The slide index explains how to present/build the deck.
- [ ] Generated slide artifacts are reproducible or intentionally not committed.
- [ ] Slides include lab handoff points, not only theory.

## Teacher documentation

- [ ] `doc/teacher/README.md` exists.
- [ ] Lesson notes identify demos, timing, expected difficulties and recovery paths.
- [ ] Assessment/rubric guidance is available.
- [ ] Licensed teacher-only references are linked, not redistributed.

## Student documentation

- [ ] `doc/student/README.md` exists.
- [ ] Setup guide exists.
- [ ] Run/test/debug/submit workflow exists.
- [ ] Troubleshooting guide exists.
- [ ] TheBitLab and local fallback are both documented where applicable.

## Operational workflow

- [ ] Local setup is reproducible.
- [ ] Lab execution commands are documented.
- [ ] Test commands are documented.
- [ ] Evidence/submission expectations are documented.
- [ ] Safety notes exist for hardware/robotics courses.

## During-year changes

- [ ] PR is labeled or described as `delivery-only` or `curriculum-change`.
- [ ] Delivery-only PR does not modify curriculum contracts.
- [ ] Curriculum-change PR updates Course Design, coverage, manifest and tests as needed.
- [ ] Delivery changelog is updated when the change affects class use.

## Quality

- [ ] Existing curriculum CI remains green.
- [ ] Link checks/build checks are run when available.
- [ ] Slide build succeeds when enabled.
- [ ] Generated artifacts are reproducible from source.
