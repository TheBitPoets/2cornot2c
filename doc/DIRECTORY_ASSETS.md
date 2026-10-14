# Directory-valued student assets

TheBitLab assignment scaffolds accept student-visible Activity assets whose `path` is either a file or a directory.

## Semantics

For a file asset, `target_path` remains the destination file path.

For a directory asset, TheBitLab recursively expands the directory into individual managed files before the scaffold is written. The relative structure is preserved below `target_path`.

Example:

```json
{
  "type": "starter",
  "path": "starter/app",
  "target_path": "app",
  "visibility": "student"
}
```

If `starter/app` contains:

```text
__init__.py
routes/health.py
```

the copy plan contains:

```text
starter/app/__init__.py      -> app/__init__.py
starter/app/routes/health.py -> app/routes/health.py
```

`target_path: "."` is valid only for a directory asset and means: copy the directory **contents** into the root of the assignment scaffold.

## Dry-run visibility

`assign_activity.py --dry-run` exposes an expanded `copy_plan` with one source/target entry for each file. The original `student_assets` metadata remains available as declared by the Activity.

This makes directory expansion auditable before writing student repositories.

## Security and portability

Directory assets use the same managed-file pipeline as ordinary file assets. Before any write, TheBitLab:

- rejects source path traversal and paths outside the Activity bundle;
- rejects symbolic links anywhere inside the declared directory tree;
- validates every descendant name against the portable Windows/Linux path policy;
- rejects portable aliases such as names that differ only by case where they could collide on Windows;
- rejects empty directory assets;
- expands descendants deterministically;
- applies reserved scaffold targets (`README.md`, `activity.json`) to every expanded file;
- rejects duplicate, equivalent, parent/child or source-file target collisions before writing;
- copies only student-visible asset types;
- tracks every expanded file in the existing teacher-side managed-assets manifest.

Because directory assets are flattened into normal file targets before scaffold reconciliation, the existing overwrite behavior continues to apply per file: unchanged stale managed files may be removed, student-modified stale files are preserved, and modified current student files are not silently overwritten.

## Boundary

This capability is about **assignment packaging**, not runtime execution. Language-specific runners/checkers remain separate capabilities; for example, TypeScript support is tracked independently.
