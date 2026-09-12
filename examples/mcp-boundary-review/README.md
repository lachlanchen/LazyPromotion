# MCP boundary review sample

`build_sample.py` freezes the protocol inventory, calls, focused test log,
source hashes, report, manifest, and deterministic ZIP for the public LKT
sample.

After building the packet, create the separate printable report with:

```bash
pandoc artifacts/report.md \
  -o artifacts/report.pdf \
  --pdf-engine=xelatex \
  -V geometry:margin=1in \
  -V fontsize=10pt \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V mainfont='Noto Sans CJK TC' \
  -V monofont='Noto Sans Mono CJK TC'
```

The PDF is kept outside the deterministic ZIP because TeX records build
metadata. The Markdown report and every machine-readable result remain inside
the hashed packet.
