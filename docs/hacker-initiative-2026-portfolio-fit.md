# Hacker Initiative 2026: portfolio-fit decision

Verified: 2026-09-11

## Decision

The 2026 `Signal/Noise` call is a real portfolio opportunity, but it is not a
shortcut to the first USD 1,000 in customer revenue. Awards are USD
5,000–25,000, applications close November 9, and the program explicitly names
open-source provenance tools and sensing or signal-processing projects.^1

**Keep Proofline as the controllable application candidate. Do not submit an
OpenHI application under LazyingArt LLC unless authority to represent the
project and separation from its earlier institutional funding are documented.**

OpenHI is the stronger technical exhibit. Proofline is the safer project to
represent. Neither is ready for a truthful submission today: OpenHI has an
authority and funding-boundary gate, while Proofline still needs a credible,
allowable USD 5,000 cost plan rather than a budget padded to meet the minimum.

## What the funder actually selects

The call favors lean projects that strengthen the worldwide hacker community
and are unlikely to receive corporate, institutional, or government support.^1
Eligible applicants include individuals, independent researchers, and small
organizations. Salaries, websites, books, films, social media, advertising, and
general awareness work are excluded.^2

Earlier selections show a practical pattern:

- A 2023 award supported a drone-carried radio relay and virtual satellite with
  two concrete demonstrations and benefits for emergency responders, young
  radio enthusiasts, and citizen scientists.^3
- A 2022 award supported OpenQuantum, an open hardware and software platform
  with CAD, schematics, firmware, control software, build guidance, and kits for
  schools. The applicant openly described relevant university-lab experience.^4
- A 2021 award supported a low-cost signal-intelligence hardware library whose
  outputs were bills of materials, printable parts, build instructions, code,
  and a small number of community devices.^5

The common strength is not a broad mission statement. It is a bounded build,
reproducible public artifacts, a named community, and observable completion.

## Portfolio comparison

| Criterion | Proofline | OpenHI |
| --- | --- | --- |
| 2026 theme | Exact match for source and provenance verification | Exact match for sensing, measurement, and signal processing |
| Current proof | Small working offline CLI, tests, example manifest, and live proof page | Published Optica paper, open hardware/software, 104 stars, 32 forks, and 628 repository commits |
| Community result | Plausible but not yet demonstrated beyond project-owned examples | Strong reproducibility and citizen-science potential; existing public attention is visible |
| Independent-funding preference | Strong: no outside funding is represented for the current prototype | Weaker: the paper acknowledges HKU and Hong Kong RGC support |
| Applicant authority | Clear within the LazyingArt-owned promotion repository | Not established for an LLC application: the paper has six authors and the license names the authors collectively |
| Clean cash need | Weak until allowable review/testing costs are confirmed | Strong: independent reproduction needs event-camera, optical, mechanical, and calibration equipment |
| Submission state | Private draft, not submitted | Research candidate only; no application draft or representation claim |

OpenHI's published research reports a self-calibrating event-based
hyperspectral system covering 420–700 nm. It reports a roughly USD 35 core
illumination module excluding the event camera and optional validation optics,
a roughly 585 ms scan versus 300 seconds for the reference system, and an open
hardware–firmware–software pipeline.^6 The repository also exposes real
reproducibility gaps: there is no locked root environment, and some legacy
documentation refers to files that are not present.^7 Those gaps could support
a useful community-reproduction project rather than another research claim.

The same paper acknowledges prior University of Hong Kong and Hong Kong
Research Grants Council funding.^6 This is not an automatic exclusion—the
guidelines express a preference, not a ban, and an earlier recipient had an
academic-lab background.^2,4 It does mean a new application must identify a
distinct unfunded phase, the lawful applicant, the project contributors, the
equipment owner, and the authority to make the commitments. Public repository
control alone does not answer those questions.

## Recommended Proofline milestone

If the cost questions are resolved, the application should fund one specific
result: **a reproducible offline source-to-claim verifier that independent
maintainers can install, break, inspect, and rebuild without sending source
material to a service.**

The bounded outputs should be:

1. A versioned JSON Schema and migration rules for files, transformations,
   claims, evidence locators, and rejected or unverified claims.
2. Deterministic CLI packages and clean-install checks on representative Linux,
   macOS, and Windows environments.
3. A threat model and negative-test corpus covering path escape, hash mismatch,
   missing evidence, duplicate identifiers, malformed manifests, and accidental
   source disclosure.
4. Four rights-cleared reference manifests for distinct hacker workflows, plus
   machine-readable reports and exact reproduction commands.
5. Two independent reproduction reports, issue records, and a close-out budget.

Success is not traffic. The tool must install cleanly on the declared platforms,
reject every seeded integrity failure, avoid network access and source-content
logging during verification, and be independently reproduced from the released
instructions.

## Budget gate

The existing provisional USD 5,000 budget assigns USD 1,500 to independent
security, privacy, and accessibility reviews and USD 600 to tester stipends.
The guidelines exclude salaries, while the application includes a
`Stipend/Expenses` category. Those facts do not establish that contractor review
or tester compensation is allowed.^2 A single concise question to the funder is
better than silently classifying these costs.

Do not substitute unnecessary hardware merely to reach the minimum. If the
funder disallows fixed-scope review and testing payments, Proofline does not yet
show an honest USD 5,000 cash need and should not be submitted this cycle.

## OpenHI fallback

OpenHI becomes the preferred candidate only when all four statements can be
documented:

1. The applicant is authorized to represent the project and its contributors.
2. The proposed phase and budget do not duplicate HKU or RGC-supported work.
3. Purchased equipment ownership, location, access, and post-grant use are
   explicit.
4. The application promises a community reproduction kit and validation record,
   not unsupported imaging performance or a commercial product.

A sensible phase would lock the software environment, define one reference
dataset and expected outputs, assemble an independently sourced unit, validate
it against declared calibration materials, and publish the exact build and
failure record. Prices must come from current quotes; no event-camera or optics
cost should be invented.

## Submission and money boundary

The application asks for identity, physical address, organization and tax
details, payee information, narrative, measurements, budget, timeline, and
agreement to reporting and anti-discrimination terms. The FAQ permits one
application per project per cycle and says payment is by check within three
weeks of notification; recipients owe progress and close-out reporting.^8

Keep those private values outside Git. An exact entity, payee, budget, and terms
review is required at submission. An application, shortlist, award, or uncashed
check is not revenue. Settled funding must be recorded as restricted grant
funding, separate from customer receipts.

## Sources

1. Hacker Initiative. “[The 2026 Grant Cycle Is Open: Signal/Noise](https://hackerinitiative.org/).” Accessed September 11, 2026.
2. Hacker Initiative. “[Grant Guidelines](https://hackerinitiative.org/grant-guidelines/).” Accessed September 11, 2026.
3. Hacker Initiative. “[2023 Grant Recipient](https://hackerinitiative.org/2023-grant-recipient/).” Accessed September 11, 2026.
4. Hacker Initiative. “[2022 Grant Recipients](https://hackerinitiative.org/2022-grant-recipients/).” Accessed September 11, 2026.
5. Hacker Initiative. “[2021 Grant Recipients](https://hackerinitiative.org/2021-grant-recipients/).” Accessed September 11, 2026.
6. Chen, Rongzhou, et al. “[Self-calibrated neuromorphic hyperspectral derivative imaging](https://www.eee.hku.hk/optima/pub/journal/2604_OPT.pdf).” *Optica* 13, no. 4 (2026): 587–590. DOI: 10.1364/OPTICA.585766.
7. Lachlan Chen. “[OpenHI](https://github.com/lachlanchen/OpenHI).” GitHub repository. Accessed September 11, 2026.
8. Hacker Initiative. “[Application FAQ](https://hackerinitiative.org/application-faq/).” Accessed September 11, 2026.
