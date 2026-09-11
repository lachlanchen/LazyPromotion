# Stateful PWA recovery specimen

This executed, project-owned fixture demonstrates three failure paths that are
easy to miss in an ordinary happy-path browser test:

1. an unsent draft survives a reload without creating a server write;
2. an interrupted write retries with the same id and produces one saved note;
3. logout and account switching hide the previous account's cached state.

The fixture is deliberately small and synthetic. It contains no AiMemo source,
customer data, production credentials, service worker, speech input, model
call, or private application route. It proves the recovery-test pattern, not
the reliability of an unknown customer PWA.

## Run

```bash
python -m pip install -r examples/stateful-pwa-recovery/requirements.txt
playwright install chromium
examples/stateful-pwa-recovery/run_suite.sh
```

The command writes JUnit XML and keeps a screenshot plus Playwright trace when
a test fails. Artifacts default to
`.local/proofs/stateful-pwa-recovery/`; a CI runner can choose its own path:

```bash
ARTIFACT_DIR="$PWD/test-results" examples/stateful-pwa-recovery/run_suite.sh
```

Run the same suite three times to expose order or retry flakiness:

```bash
examples/stateful-pwa-recovery/verify_three_runs.sh
```

## What a paid baseline would replace

For a real engagement, the first funded milestone replaces this fixture with
one customer-controlled staging PWA, one disposable non-privileged role, and
up to three agreed recovery journeys / twelve checkpoints. The written scope
must define data reset, permitted fault injection, acceptance, and retention
before credentials or source are shared.

