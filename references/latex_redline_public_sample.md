# LaTeX redline public sample plan

## Revision stage

Internal synthetic revision sample. This is not a reviewer response, customer manuscript, scientific result, or journal submission.

## Problem

The public PaperAgentDemo proves a clean LaTeX build but has no distinct baseline and the checked workstation toolchain lacks `latexdiff`. It therefore cannot demonstrate the redline workflow described in the source-backed guide.

## Allowed files

- `examples/latex-redline/baseline/main.tex`
- `examples/latex-redline/revision/main.tex`
- `examples/latex-redline/build.sh`
- `examples/latex-redline/README.md`
- Generated files under `examples/latex-redline/artifacts/`
- This plan and the matching campaign evidence

## Planned content change

The baseline will be a short, explicitly synthetic methods note with one equation, one table, and one conclusion. The revision will:

- clarify that a redline is a third build;
- add the requirement to freeze the old and revised source trees;
- change the table from two checked artifacts to three;
- add a short verification paragraph without introducing scientific or customer claims.

The two active source filenames remain `main.tex`. Baseline and revision live in separate named directories and are never overwritten by the redline generator.

## Out of scope

- Editing PaperAgentDemo or any real manuscript.
- Scientific, statistical, methodological, citation, or journal-style review.
- A response letter, supplement, cover letter, submission login, or acceptance claim.
- Customer data, confidential source, or a commercial service activation.
- Manual cleanup that cannot be repeated from the build script.

## Verification

1. Use the official `latexdiff` 1.4.0 tag at commit `57d0ec532c41eb73645804d7f67667336da8bd01` for the checked local run.
2. Build baseline and revision independently with `latexmk -pdf -interaction=nonstopmode -halt-on-error`.
3. Generate `redline.tex` from the two named sources.
4. Build the redline with the same TeX engine and environment.
5. Confirm all three PDFs exist, inspect page counts and extracted text, and reject undefined references or LaTeX errors.
6. Run the complete build twice and require identical source and PDF hashes.
7. Record source, tool, and PDF SHA-256 values in a manifest.
8. Keep generated auxiliary files out of Git; retain only the three current PDFs, the generated redline source, build logs, and manifest needed to reproduce the proof.

## Acceptance criteria

- Three successful, separate builds.
- Identical manifest hashes across consecutive builds.
- The redline visibly contains additions and deletions corresponding to the planned revision.
- No undefined references or LaTeX errors in final logs.
- No unsupported result, customer, delivery, or journal claim.
- Repository worktree remains free of unrelated staged changes.

## Response-letter impact

None. The sample has no reviewer or editor correspondence.
