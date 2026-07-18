# Configurazione globale Codex

Questa pagina spiega come portare su una nuova macchina la configurazione Codex usata per lavorare con GPT-5.6 Sol, reasoning ultra e sub-agenti.

## Cosa viene configurato

Il template sicuro e in [`config/codex/codex-system.config.toml`](../config/codex/codex-system.config.toml):

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "ultra"
service_tier = "default"

[agents]
max_threads = 6
max_depth = 1
job_max_runtime_seconds = 1800
interrupt_message = true
```

Il file [`config/codex/AGENTS.md`](../config/codex/AGENTS.md) aggiunge istruzioni globali per usare sub-agenti quando il lavoro e complesso, lungo o parallelizzabile.

## Cosa non contiene

Il template non contiene:

- token;
- API key;
- `auth.json`;
- path locali della macchina;
- configurazioni MCP personali;
- configurazioni plugin personali;
- segreti AI provider.

Questi dati restano nella macchina locale e non vanno committati.

## Installazione su Windows

Da PowerShell, nella root del repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_codex_system_config.ps1
```

Lo script:

1. crea `%USERPROFILE%\.codex` se manca;
2. fa backup di `%USERPROFILE%\.codex\config.toml`, se esiste;
3. applica `model`, `model_reasoning_effort`, `service_tier` e `[agents]`;
4. preserva le altre sezioni gia presenti nel `config.toml`, per esempio plugin, MCP e progetti trusted;
5. installa `%USERPROFILE%\.codex\AGENTS.md`;
6. fa backup di un eventuale `AGENTS.md` gia presente.

Per vedere cosa farebbe senza scrivere:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_codex_system_config.ps1 -WhatIf
```

Per sovrascrivere completamente `config.toml` con il template minimo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_codex_system_config.ps1 -Overwrite
```

Usa `-Overwrite` solo su una macchina nuova o quando vuoi eliminare consapevolmente la configurazione precedente.

## Installazione su Linux

Da Bash, nella root del repository:

```bash
bash scripts/install_codex_system_config.sh
```

Lo script installa in `$HOME/.codex`, fa backup dei file esistenti e preserva le altre sezioni gia presenti nel `config.toml`.

Per vedere cosa farebbe senza scrivere:

```bash
bash scripts/install_codex_system_config.sh --dry-run
```

Per usare una home Codex diversa, utile nei test o su macchine condivise:

```bash
bash scripts/install_codex_system_config.sh --codex-home /percorso/.codex
```

Per sovrascrivere completamente `config.toml` con il template minimo:

```bash
bash scripts/install_codex_system_config.sh --overwrite
```

Usa `--overwrite` solo su una macchina nuova o quando vuoi eliminare consapevolmente la configurazione precedente.

## Dopo l'installazione

Chiudi e riapri:

- VS Code;
- eventuale estensione Codex;
- Codex CLI;
- ChatGPT desktop app, se la stai usando.

Le app possono leggere `config.toml` all'avvio, quindi una sessione gia aperta potrebbe non vedere subito le modifiche.

## Note operative

`model_reasoning_effort = "ultra"` aumenta qualita e profondita sui task complessi, ma puo aumentare tempo e consumo.

I sub-agenti sono utili soprattutto per review, esplorazione codice, analisi log e test. Non conviene usarli sempre: per modifiche piccole un singolo agente resta piu veloce e piu controllabile.

La disponibilita effettiva di `gpt-5.6-sol` e del reasoning `ultra` dipende dall'account, dal piano e dalla superficie Codex usata.
