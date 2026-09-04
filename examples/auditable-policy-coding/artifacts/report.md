# Auditable policy content-coding sample

> Project-owned synthetic workflow proof; not a customer result, benchmark, offer, revenue claim, or analysis of client or copyrighted text.

## Frozen codebook

Version `1.0.0` was frozen on 2026-09-05. The unit of analysis is one synthetic policy passage.

### PUBLIC_ACCESS — Public access commitment

The policy commits to making an official resource available to the public without an account or access fee.

- Include: Apply when the text expressly provides public access and states either no fee or no account barrier.
- Exclude: Exclude staff-only access, undefined future access, and access that requires an account or fee.

### PHASED_IMPLEMENTATION — Phased implementation schedule

The policy names at least two implementation stages and gives a date or deadline for each stage.

- Include: Apply when a pilot or interim stage and a complete stage each have an explicit date.
- Exclude: Exclude a single deadline, an undated aspiration, or an ordering of steps without dates.

### INDEPENDENT_REVIEW — Independent review mechanism

A reviewer outside the implementing department examines decisions and reports findings.

- Include: Apply when the text identifies an external reviewer, a review object, and a reporting duty.
- Exclude: Exclude internal quality checks and external advice that includes no review of decisions.

## Coding decisions

### P-001 — Archive access rule

The city archive shall provide free online access to final meeting minutes. Documents must remain downloadable without an account.

- Classification: `PUBLIC_ACCESS` (Public access commitment)
- Primary code: `PUBLIC_ACCESS`
- Rationale: The passage expressly removes both the price and account barriers to public access.
- Ambiguity: No — Both the no-fee and no-account conditions are explicit.
- Deciding evidence:
  - `P-001:S-01` — “The city archive shall provide free online access to final meeting minutes.”
  - `P-001:S-02` — “Documents must remain downloadable without an account.”

### P-002 — Register rollout rule

The department will publish a pilot register by 30 June 2031. A complete register is scheduled for 31 December 2031, subject to approved funding.

- Classification: `PHASED_IMPLEMENTATION` (Phased implementation schedule)
- Primary code: `PHASED_IMPLEMENTATION`
- Rationale: The text dates both a pilot stage and a complete stage, while making the latter conditional.
- Ambiguity: Yes — The final-stage date is explicit, but delivery depends on later funding approval.
- Deciding evidence:
  - `P-002:S-01` — “The department will publish a pilot register by 30 June 2031.”
  - `P-002:S-02` — “A complete register is scheduled for 31 December 2031, subject to approved funding.”

### P-003 — Annual review rule

An external reviewer selected by the civic panel shall audit a sample of decisions each year. The reviewer shall publish a summary that names no individual applicants.

- Classification: `INDEPENDENT_REVIEW` (Independent review mechanism)
- Primary code: `INDEPENDENT_REVIEW`
- Rationale: An external reviewer must inspect decisions annually and publish a privacy-preserving summary.
- Ambiguity: No — The reviewer, review object, frequency, and reporting duty are all stated.
- Deciding evidence:
  - `P-003:S-01` — “An external reviewer selected by the civic panel shall audit a sample of decisions each year.”
  - `P-003:S-02` — “The reviewer shall publish a summary that names no individual applicants.”

## Verification boundary

The builder resolves every locator, requires every deciding excerpt to match its source segment byte for byte, validates complete passage coverage, and rejects unknown codes. It makes no network or model calls.
