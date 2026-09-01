# Course Delivery Artifact Contract v1

Status: **draft companion contract** to `course-delivery-standard-v1.md`.

## Purpose

Generated classroom files are derivatives of canonical course sources. A PDF or PPTX must therefore be traceable back to the exact source revision that produced it.

This contract defines the minimum evidence for CI-generated slide/course bundles without prescribing one presentation engine to every course.

## Source-of-truth rule

Editable Markdown/source material remains canonical unless a course explicitly documents a different authoring source.

Generated HTML, PDF, PPTX, handouts and sites are **derived artifacts**. They should not be manually edited and committed as the new source of truth.

## Bundle identity

A CI-generated delivery bundle SHOULD have an artifact name containing the course identifier and source commit, for example:

```text
tpsi5-slides-5c249eece46faef49ca6c0ef710b90c535739e44
```

The source commit MUST also be recorded inside the bundle manifest. Pull-request synthetic merge SHAs may be recorded as CI metadata, but the manifest SHOULD preserve the actual source/head SHA used for classroom material whenever the workflow can resolve it.

## Required manifest

A reproducible bundle SHOULD contain `MANIFEST.json` with at least:

```json
{
  "schema": "thebitpoets.course-slides-artifact.v1",
  "course": "course-id",
  "content_pack": "1.0.0",
  "renderer": "marp-cli",
  "renderer_version": "4.5.0",
  "source_commit": "<sha>",
  "formats": ["html", "pdf", "pptx"],
  "source_decks": [
    {"path": "slides/module.md", "sha256": "..."}
  ],
  "artifacts": [
    {"path": "pdf/module.pdf", "sha256": "...", "bytes": 12345}
  ]
}
```

Equivalent field names are allowed during pilot adoption, but the semantics MUST remain explicit: course, curriculum/release when applicable, renderer/version, source revision, source hashes, generated artifact hashes and requested formats.

## Checksums

The bundle SHOULD also contain a human/tool-friendly `SHA256SUMS.txt` covering generated classroom artifacts.

Checksums serve two purposes:

1. distinguish two exports with the same visible filename;
2. prove which exact files were distributed or used in class.

## Renderer pinning

The rendering toolchain SHOULD be pinned to a known version in CI. A renderer upgrade is a delivery-toolchain change and should be recorded in the course delivery changelog when it may affect layout or generated files.

For Markdown/Marp courses, the TPSI5 pilot validated Marp CLI `4.5.0` for HTML, PDF and PPTX generation. This is **pilot evidence**, not a permanent cross-course requirement; later courses may deliberately pin a different reviewed version.

## Format policy

Courses SHOULD generate the formats useful to their classroom workflow.

For slide-based courses:

- HTML is useful for browser presentation and lightweight publication;
- PDF is useful for stable projection/printing/sharing;
- PPTX is useful when PowerPoint interoperability matters and the renderer supports it reliably.

A course MAY omit a format that is not operationally useful, but the manifest must describe the formats actually built.

## Reliability policy

Different output formats may require different rendering strategies.

The source decks MUST remain identical across formats, but CI MAY use:

- different safe parallelism per format;
- longer browser/render timeouts for expensive exports;
- isolated or serial rendering for resource-heavy formats;
- temporary sidecar output followed by deterministic staging into the artifact bundle.

TPSI5 pilot evidence showed that HTML/PDF rendered reliably in parallel while concurrent PPTX conversion could exhaust browser/Puppeteer timing. Serial PPTX rendering solved the problem without changing slide sources. This is the preferred failure model: **harden the delivery toolchain, do not weaken the teaching content to satisfy the renderer**.

## Temporary files

A builder MUST NOT leave generated sidecars beside canonical sources after a successful or failed CI run. Temporary HTML/PDF/PPTX files should be moved into the staging directory or removed in a cleanup/finally path.

Generated output directories SHOULD be ignored by version control unless a course deliberately publishes them through a dedicated release/site mechanism.

## CI acceptance

A Level 3 course with generated slides SHOULD demonstrate:

1. source/deck structural validation passes;
2. renderer/browser prerequisites are present;
3. every requested format renders successfully;
4. the expected number of outputs exists;
5. manifest/checksum generation succeeds;
6. the bundle is uploaded as a CI artifact;
7. the ordinary course Quality suite remains green on the same source head.

## Pilot evidence — TPSI quinto

Validated source head:

```text
5c249eece46faef49ca6c0ef710b90c535739e44
```

Evidence:

- `Slides #10`, run `32510302002`: success;
- artifact `9456794079`;
- artifact digest `sha256:9e4172336460fc9e8450f13d2fc6a44b77a2c36b88b9cca0c5e26f48c198eb99`;
- 20 source decks: course overview + modules 00–18;
- 60 generated classroom files: 20 HTML + 20 PDF + 20 PPTX;
- `MANIFEST.json` and `SHA256SUMS.txt` included;
- ordinary `Quality #203`, run `32510301892`: success on Ubuntu Python 3.11/3.12 and Windows Python 3.11.

This pilot is the reference implementation for the first rollout to TPSI quarto, Romeo and later courses.