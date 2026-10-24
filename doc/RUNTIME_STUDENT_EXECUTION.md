# Runtime plugin: policy di esecuzione studente

Le Activity che usano `extensions.thebitlab.runtime` possono offrire due percorsi tecnici:

- `run()` locale/process-only, utile per sviluppo del plugin e test controllati;
- `sandbox-plan.v1`, eseguito dal broker Docker TheBitLab e finalizzato sul processo trusted.

## Regola del flusso studente

`student_runtime.run_runtime_assignment()` applica una policy fail-closed:

1. carica e valida il runtime installato;
2. se il runtime dichiara `sandbox-plan.v1`, una richiesta storica con backend `local` viene
   promossa automaticamente a `docker`;
3. il broker esegue `prepare_sandbox -> container untrusted -> finalize_sandbox`;
4. se Docker, l'immagine pin-nata o il broker non sono disponibili, l'esecuzione fallisce;
5. non esiste fallback silenzioso a `plugin.run()` dopo un errore della sandbox.

Questo comportamento rende sicuri anche i chiamanti storici (`student_lab_runner`, TUI e
`student_runtime_cli`) che usavano `local` come valore predefinito prima dell'introduzione del
broker.

## Compatibilita con runtime legacy

Un plugin `runtime_plugin.v1` che non dichiara `sandbox-plan.v1` conserva il comportamento locale
esistente. In questo caso il report rimane `authoritative=false` e `execution_isolation=process-only`.

I nuovi runtime destinati a eseguire codice studente non fidato devono implementare
`sandbox-plan.v1`; il percorso locale non deve essere presentato come grading autorevole.

## Diagnostica nel report

Per i runtime sandbox-capable il report studente registra:

- `runtime.requested_backend`: valore ricevuto dal chiamante storico;
- `runtime.backend`: backend effettivamente usato;
- `runtime.metadata.authoritative`: `true` solo dopo finalizzazione trusted;
- `runtime.metadata.execution_isolation`: confine effettivo dichiarato da TheBitLab.

Questa distinzione rende visibile l'eventuale promozione `local -> docker` senza cambiare le API
delle Activity o il contratto `runtime_plugin.v1`.

## Sviluppo locale del plugin

Il percorso process-only resta disponibile agli sviluppatori tramite le API di basso livello
`thebitlab_runtime_plugins.run_runtime()` / `plugin.run()`. Non viene usato automaticamente dal
flusso studente per un runtime che offre il broker sandbox.
