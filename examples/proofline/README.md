# Proofline example

Proofline is a small offline verifier for source-to-claim evidence. It hashes
the files named by a manifest, checks that transformations reference known
inputs and outputs, and requires every `verified` claim to cite a known file
and a human-inspectable locator.

Run the project-owned example:

```bash
python proofline.py examples/proofline/manifest.json
```

Expected result:

```text
Proofline PASS
Manifest: .../examples/proofline/manifest.json
Checked: 2 files, 2 claims, 1 transformations
```

The verifier never fetches a URL or uploads a file. It confirms that the local
evidence chain is internally intact; it does not prove that a claim is true,
that a source is trustworthy, or that the operator has redistribution rights.
