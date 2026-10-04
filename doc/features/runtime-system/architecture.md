# Runtime System — Architecture

## Scopo

Fornire un boundary stabile tra Activity/Student Lab e meccanismo concreto di esecuzione.

## Responsabilità

Plugin discovery/loading, contratto runtime, dispatch, sandbox planning, metadata di authority/isolation e failure espliciti.

## Confini

Runtime System non definisce la pedagogia dell'Activity, non installa automaticamente provider di sistema e non decide il voto.

## Componenti

- `scripts/thebitlab_runtime_contracts.py`
- `scripts/thebitlab_runtime_plugins.py`
- `scripts/student_runtime.py`
- `scripts/thebitlab_runtime_sandbox.py`
- `scripts/student_runtime_cli.py`

## Contratti

`runtime_plugin.v1` e, per codice non fidato, `sandbox-plan.v1`.

## Policy fail-closed

Un runtime sandbox-capable viene eseguito nel broker previsto; un errore Docker/broker non deve produrre fallback silenzioso a process-only.

## Authority

I report distinguono backend richiesto, backend effettivo, `authoritative` ed `execution_isolation`.

## Evoluzione

Environment Requirement → provider primario → fallback esplicito → Agent/Live/Remote. Nessun ranking automatico iniziale.

## Invarianti

- runtime separato dall'Activity;
- isolation effettiva visibile;
- nessun silent fallback che riduca la sicurezza;
- provider concreto sostituibile.

## Documenti

- [runtime-plugin-contract.md](../../architecture/runtime-plugin-contract.md)
- [runtime-adapter-template.md](../../architecture/runtime-adapter-template.md)
- [RUNTIME_STUDENT_EXECUTION.md](../../RUNTIME_STUDENT_EXECUTION.md)
- [ADR ecosystem separation](../../architecture/adr-runtime-ecosystem-separation.md)
