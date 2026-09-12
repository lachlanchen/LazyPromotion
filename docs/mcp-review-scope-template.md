# MCP Server Pre-Deployment Review — scope record

Use this after a positive metadata-only fit check. Replace every bracketed field,
remove unused choices, and send no payment request until both sides accept the
finished record in writing.

## Parties and reviewed revision

- Client: `[legal name or contracting entity]`
- Provider: LazyingArt LLC
- Repository or private project label: `[URL or non-confidential label]`
- Base revision: `[immutable commit or release identifier]`
- MCP server: `[one server]`
- Intended client and version: `[client]`
- Transport and network boundary: `[stdio / Streamable HTTP / other]`
- Disposable test environment: `[OS, runtime, dependency lock, startup command]`
- Review start conditions: secured payment, authorized access, working setup
  instructions, and all agreed test dependencies are available.

The client confirms it controls or is authorized to provide this revision and
the agreed fixtures. No source code, credentials, private data, production
endpoint, exploit detail, or confidential log is included in the fit check.

## Included surface

One base revision of one MCP server, with no more than eight tools and resources
in total:

1. `[tool or resource]`
2. `[tool or resource]`
3. `[continue only as needed, maximum eight]`

The authority map records actual reads, writes, external calls, credentials,
approval points, output exposure, and failure impact for this surface.

## Ten agreed checks

1. Protocol version negotiation.
2. Advertised versus live tool and resource discovery.
3. One agreed valid tool call, including output bounds and result handoff.
4. One agreed valid resource read, including locator resolution by the intended client.
5. Unknown tool or resource rejection.
6. Malformed or missing input rejection.
7. Actual reads, writes, external calls, and approval gates.
8. Credential, path, and private-context disclosure in agreed outputs and logs.
9. One safe failure or timeout case.
10. Client and transport authentication and isolation boundary.

Any substitution must be written here before payment: `[none or exact replacement]`.
The checks use only the agreed disposable environment and these permitted
network calls or fixtures: `[exact boundary]`. Production secrets, destructive
live operations, and external writes are excluded unless separately authorized
and scoped in this record.

## Deliverables and acceptance

- Frozen inventory of the reviewed surface and environment.
- Authority map.
- Sanitized protocol packet for the ten checks.
- Failure ledger.
- Narrow go/no-go report for the stated client, transport, and network boundary.

Delivery is within seven business days after every start condition above is met.
Only one MCP review is active at a time. Acceptance means the listed files open,
identify the agreed revision and environment, cover the ten checks, and state a
supported go/no-go decision. The review is not a guarantee that the server is
secure or production-ready.

Within fourteen calendar days after delivery, the client may provide one
successor revision of the same server, transport, and reviewed surface. The
provider will re-run up to three checks that failed in the original report.
New tools, resources, cases, transports, implementation work, or another server
require a new scope.

## Handling and support

- Private transfer method: `[method agreed after scope acceptance]`
- Permitted automation: `[exact tools or local-only requirement]`
- Confidentiality constraints: `[terms]`
- Working-copy deletion: `[date or period after delivery, cancellation, or refund]`
- Required retained records: `[none, or the minimum required by contract or law]`
- Delivery format: `[archive, Markdown/PDF, repository branch, or other]`

Customer material is used only for this review and is not published or reused as
public proof without separate written permission. Support is limited to written
clarification during the fourteen-day recheck window.

## Excluded work

- Fix implementation or review of a second server, transport, added tool or
  resource, or test set beyond the limited recheck.
- Penetration testing, security certification, or a security or production-readiness guarantee.
- OAuth or authentication implementation, production deployment, SLA,
  performance guarantee, or ongoing monitoring.
- Production secrets, private data, destructive live operations, or external
  writes outside the exact authorization above.

## Fee, cancellation, and payment route

The fixed fee is **USD 500**. For cancellation after work starts, delivered work
is allocated as follows; only undelivered items are refunded:

- USD 100 — environment setup
- USD 150 — authority map
- USD 150 — protocol packet
- USD 100 — failure ledger and go/no-go report

Cancellation before private access or execution begins receives a full refund.
A direct-site client receives one reviewed Stripe request only after accepting
this record. A marketplace-origin contract, payment, revisions, and delivery
remain on that marketplace where its rules require it. There is no public
self-serve checkout for this service.

## Written acceptance

Client acceptance: `I accept MCP review scope [scope ID and version], including
the USD 500 fee, start conditions, handling terms, exclusions, recheck boundary,
and cancellation allocation.`

- Scope ID and version: `[identifier]`
- Client acceptance name and date: `[name, date]`
- Provider acceptance name and date: `[name, date]`

Any change is effective only when both sides accept a revised written scope.
