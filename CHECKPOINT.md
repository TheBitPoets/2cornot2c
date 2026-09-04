# Checkpoint operativo

- **Data/ora:** 2026-08-21T12:27:43+02:00
- **Obiettivo:** remediation CI stretta PR #720 / issue #704 per i quattro failure Linux deterministici di Quality #1713 sul candidate `63ebd333693c9d884413cb31c28280be5a17f297`.
- **Stato:** **COMPLETATO LOCALMENTE / BLOCKED SU CI QUEUED**. PR ancora `OPEN` e `DRAFT`; gate independent review sul nuovo HEAD **0/2**.
- **Criterio:** correzione test-only, exact four verdi su Python 3.12/3.11 Linux, regressioni security e full suite verdi, integrazione Ubuntu 24.04 verde, push fast-forward; CI exact HEAD deve ancora completarsi.

## Root cause e remediation

Quality #1713 ha prodotto sugli ambienti Python 3.12 e minimum 3.11 gli stessi quattro failure (`4 failed, 2427 passed, 17 skipped`):

1. `test_official_package_nginx_module_config_and_binary_are_accepted`;
2. `test_apt_closed_inventory_accepts_only_canonical_package_config`;
3. `test_ephemeral_systemd_surface_quarantines_and_exactly_restores_local_generator`;
4. `test_reviewed_script_digest_change_invalidates_executable_policy`.

Tre fixture behavior-bearing vivevano sotto pytest `tmp_path` (`/tmp/pytest-of-runner/...`) e raggiungevano il vero `_read_stable_trusted_file()`, che correttamente rifiuta l’ancestry world-writable `/tmp`. Il quarto test dipendeva dal vecchio ordine/messaggio systemd, mentre production ora fallisce prima sulla più forte assenza di package integrity del local generator.

Remediation esclusivamente in `tests/test_pilot_deployment.py`:

- helper test-only limitata a un exact allow-set di path sintetici, con lettura dei byte reali tramite descriptor `O_NOFOLLOW` e verifica identità pre/open/post; nessun digest mockato;
- helper applicata soltanto ai fixture nginx module, APT inventory e reviewed-script;
- asserzione systemd vincolata alle due categorie fail-closed ammissibili e al path del generator;
- test Linux separato sul vero `_read_stable_trusted_file()` che prova il rifiuto di ancestry `/tmp` world-writable.

**Production non modificata.** In particolare nessun cambiamento a `_read_stable_trusted_file()`, `_verify_trusted_ancestry()`, `_assert_trusted_metadata()` o al runtime trust model. Nessun aggiornamento della documentazione canonica necessario.

## Git e PR

- Worktree `F:/dev/2cornot2c-704`; branch `fix/oauth-log-redaction-704`.
- Base e merge-base invariati: `5472eef86568a4e7ce59ad34ba937220df27efd7`.
- Commit/push fast-forward: `ccb826a108910cc1c519fa74fadff33a69bb7100` (`test: isolate trusted-path runtime closure fixtures`).
- Unico file nel commit: `tests/test_pilot_deployment.py`.
- `CHECKPOINT.md` è localmente modificato e **UNSTAGED**, escluso dal commit; non stage/reset/clean/stash.
- PR #720 verificata dopo push: `OPEN`, `DRAFT`, head/base corretti.

## Verifiche locali

- Exact four, Linux Python 3.12: **4 passed**.
- Exact four, Linux Python 3.11 isolato: **4 passed**.
- Regressioni security mirate (nginx config/binary e inline module; APT inventory/hook; PATH shadow; stale digest; true world-writable ancestry; local/modified generator; SysV; boot-reachable unit; root timer ZERO UNKNOWN/CLOSED-EXECUTABLE): **43 passed**.
- Full Linux Python 3.12 + Node 20 + dependency set CI: **2426 passed, 23 skipped**.
- Full Linux Python 3.11 + Node 20 + dependency set CI: **2426 passed, 23 skipped**.
- Full Ubuntu 24.04.4 / Python 3.12.3 con nginx/logrotate/systemd/Node: **2428 passed, 21 skipped** (un test in più rispetto al candidate: il nuovo negative ancestry).
- Ubuntu 24.04 systemd integration canonica: **PASS**; include `nginx -t/-T`, logrotate `--debug`, real rotate/reopen FD, generator/SysV/unit integrity, scheduler ZERO UNKNOWN e rollback/recovery.
- `compileall`, shell syntax, Sphinx `-W`, course plan `--check`, `git diff --check`: **PASS**.
- Tentativo full 3.12 preliminare in immagine Python priva di Node non CI-equivalent: `2190 passed, 26 skipped, 233 failed`, tutti frontend per executable `node` assente; non ripetere senza Node. Rerun corretto sopra verde.
- Nessun container o processo temporaneo rimasto.

## CI one-shot e prossimo passo

Unica snapshot post-push su exact HEAD `ccb826a1`:

- 11 check totali, tutti `QUEUED` (Quality `python`, `minimum-python`, `windows-filesystem`, `mermaid-diagrams`; Docker; matrice uTUI);
- `mergeStateStatus=UNSTABLE` perché i check sono pendenti;
- nessun polling ulteriore eseguito.

**Prossimo passo:** in una nuova sessione verificare una sola volta l’esito CI dell’exact HEAD. Se Quality o altro check fallisce, leggere il failing job e restare BLOCKED. Se tutti i check sono verdi, dichiarare `READY FOR INDEPENDENT REVIEW`; non eseguire qui una independent review, non mark-ready, non mergeare. Gate resta `0/2`; ogni nuovo commit lo mantiene/azzera a `0/2`.

File minimi da leggere alla ripresa: `AGENTS.md`, `CHECKPOINT.md`; consultare il diff `5472eef8..ccb826a1` soltanto se necessario.

---

## Remediation Independent Review Round 1 H-01/H-02 — candidate 20ba430e

- **Data/ora:** 2026-08-21T18:50:22+02:00
- **Obiettivo:** chiudere H-01 logrotate same-line package hook e H-02 boot/SysV root execution graph della PR #720.
- **Stato:** **IMPLEMENTATO, VERIFICATO E PUSHATO / BLOCKED SU CI IN PROGRESS**. PR `OPEN` e `DRAFT`; gate independent review **0/2**; non mergeata e non mark-ready.
- **Topologia iniziale:** feature `ccb826a108910cc1c519fa74fadff33a69bb7100`; main autorizzato `ec60eaca11da481a8510ec67255abaf76ac5b23e`; merge-base `5472eef86568a4e7ce59ad34ba937220df27efd7`.
- **Main corrente:** `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0`, avanzato dopo il preflight soltanto in `doc/sphinx/index.rst`; nessun overlap. `git merge-tree --write-tree origin/main HEAD` PASS, tree `1dbc46f54d010c263bcf53526c62653898571396`.
- **Candidate:** commit/push fast-forward `20ba430ef8689fd33487d5e269de6b246e479ad1` (`fix: close root execution provenance graph`). Nessun rebase/merge/force push.

### Remediation

- H-01 **CLOSED**: inventario logrotate Noble chiuso per nome+SHA-256; parser layout-independent per `prerotate`/`postrotate`/`firstaction`/`lastaction` e compression execution; hook package/managed exact-byte ed execution closure transitiva.
- H-02 **CLOSED**: registry chiusa dei service con exact `FragmentPath`; tutti gli effective Exec* root analizzati; native executable package+byte-integrity; interpreter/trampoline/shebang richiedono policy; template `Accept=yes` exact-byte; SysV registry vuota e nuovi service/SysV `UNKNOWN`.
- Documentation canonica aggiornata in `doc/PILOT_DEPLOYMENT.md`.
- File PR modificati: `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_ubuntu_integration.py`, `tests/test_pilot_deployment.py`.
- `CHECKPOINT.md` resta local-only modified/unstaged e non è nel commit.

### Verifiche finali sull’exact source candidate

- Reproducer reali Ubuntu, eseguiti per primi: synthetic dpkg logrotate `{ postrotate` + helper unmanaged **REJECT/helper non eseguito**; package SysV + bare `review-helper` + `/usr/local` first candidate **REJECT/helper non eseguito**; unit invariata + binary package modificato **REJECT**.
- Nuovo package native service: **UNKNOWN REJECT**.
- Targeted deployment/security Python 3.12 e 3.11: **PASS**.
- Full Linux Python 3.12 + Node 20: **PASS**.
- Full Linux Python 3.11 + Node 20: **PASS**.
- Ubuntu 24.04/systemd 255 full integration: **PASS**, inclusi APT/e2scrub/motd/dpkg backup/timers/generator/SysV/logrotate/nginx/migration/recovery/rollback e real rotate/reopen.
- `compileall`, Bash syntax, Sphinx `-W`, course-plan `--check`, feature `git diff --check`: **PASS**.
- Full Windows 3.12 non canonico: due soli failure baseline/platform (`WinError 1314` symlink privilege e avvio diretto `.sh`); gate Linux canonico verde.
- Developer adversarial review: **nessun HIGH/MEDIUM aperto** dopo hardening exact fragment, unknown non-root service, interpreter/trampoline, Accept template bytes e activation target.
- Nessun container/processo temporaneo noto rimasto.

### PR e CI one-shot

- PR body aggiornato con candidate/main/merge-base/remediation/test; stale `0d430eb`, Docker #873, uTUI #772 e Quality #1700 rimossi.
- Unica snapshot exact HEAD `20ba430e`: 11 check; 5 `SUCCESS`, 6 `IN_PROGRESS`, 0 failure; `mergeStateStatus=UNSTABLE` per pending. Nessun polling.
- **Prossimo passo:** nuova sessione, una sola verifica CI exact HEAD. Se tutto verde: `READY FOR INDEPENDENT REVIEW`; se failure: ispezionare solo il job esatto e restare `BLOCKED`. Non mark-ready, non mergeare. Gate resta 0/2.
- File minimi: `AGENTS.md`, `CHECKPOINT.md`; diff feature `5472eef8...20ba430e` soltanto se necessario.

---

## Remediation Independent Review Round 1 H-03/H-04 — candidate db13ec01

- **Data/ora:** 2026-08-21T23:51:08+02:00
- **Obiettivo:** chiudere H-03 package identity takeover e H-04 missing-executable fill/interpreter identity della PR #720.
- **Stato:** **IMPLEMENTATO, VERIFICATO E PUSHATO / BLOCKED SU CI IN PROGRESS**. PR `OPEN` e `DRAFT`; non mark-ready, non mergeata; independent gate sul nuovo HEAD **0/2**.
- **Candidate precedente / review:** `20ba430ef8689fd33487d5e269de6b246e479ad1`; Independent Review Round 1 **BLOCKED** per H-03/H-04. La CI exact precedente era completamente verde prima del finding.
- **Candidate nuovo:** commit/push fast-forward `db13ec0113cda49bb18f09fa24459d10e1c7fdc1` (`fix: bind boot execution to reviewed identities`).
- **Main / merge-base:** `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` / `5472eef86568a4e7ce59ad34ba937220df27efd7`; nessun overlap security. `git merge-tree --write-tree origin/main HEAD` PASS, tree `175b1b4976abd779987e0472649b362ac9e38721`.

### Root cause e modello

- H-03: la vecchia registry promuoveva a trusted qualunque owner corrente con digest dpkg valido. Ora fragment, drop-in, executable, Accept template/executable e timer/runtime file legano l'exact **expected binary package identity**; `Replaces`, `Provides` e alias non concedono identità.
- H-04: i path Exec assenti venivano omessi con `allow_missing=True`. Ora ogni comando slot-aware dichiara `EXPECTED_PRESENT` o `EXPECTED_ABSENT`; una transizione absent→present o present→absent blocca.
- La registry contiene 44 service policy (43 fragment package + TheBitLab managed), 2 drop-in Noble revisionati, 55 Exec record (48 present, 7 absent), tutti i sette slot Exec*, exact effective argv/count/slot e SHA-256 revisionato dei fragment/unit semantics.
- Le classi `NATIVE_PACKAGE_BINARY`, `INTERPRETED_SCRIPT`, `REVIEWED_TRAMPOLINE` sono policy-driven; nessun basename conferisce trust. Native richiede expected package, bytes package-authoritative e no shebang; script/trampoline richiedono closure.
- Le due policy `Accept=yes` attestano expected package/template digest/executable e una probe instance con drop-in vuoti ed exact Exec slots. Gli otto timer legano timer/service SHA, expected packages e closure; SysV resta default-deny. Logrotate conserva inventario exact name+SHA e hook/compression closure.
- Primitive comune `_attest_expected_package_files()` separa presenza, owner atteso/stato installato, digest package, digest revisionato e ricontrollo owner/byte durante l'attestazione.
- Documentazione canonica aggiornata in `doc/PILOT_DEPLOYMENT.md`, inclusa policy fail-closed sugli update semantici e limite esplicito: nessuna analisi comportamentale ELF generale.

### Regressioni e verifiche

- Riproduzione vecchio HEAD: H-03 e H-04 entrambi **ACCEPT** con `.deb` reale package-valid e marker root provato separatamente; restore package pristine PASS.
- H-03 nuovo: real `.deb` `Replaces/Provides: systemd`, exact fragment revisionato e renamed Python sul path executable atteso: **unexpected package identity REJECT**, digest dpkg valido, marker assente durante gate, restore PASS.
- H-04 nuovo: `/usr/bin/kmod` baseline assente, real `.deb` lo riempie con renamed Python e digest valido: **unexpected presence REJECT**, marker assente durante gate, restore PASS.
- Expected-present executable rimosso: REJECT; Accept template foreign owner: REJECT; timer `fstrim` executable foreign owner: REJECT; pristine baseline: PASS.
- Vecchi H-01 same-line logrotate, H-02 SysV PATH shadow, modified native package executable, new package service, generator/package unit bytes: PASS fail-closed.
- Targeted deployment/security Python 3.12: PASS; Python 3.11: PASS.
- Full Linux Python 3.12.14 + Node 20.20.2: PASS.
- Full Linux Python 3.11.16 + Node 20.20.2: PASS.
- Ubuntu 24.04/systemd 255 integrazione completa distruttiva isolata: PASS; include real package matrix, 8 timer ZERO UNKNOWN, APT, e2scrub, motd, dpkg backup, nginx, logrotate input/rotate/reopen, migration, recovery e rollback.
- `compileall`, Bash syntax, Sphinx `-W`, course-plan `--check`, feature/worktree `git diff --check`: PASS.
- Developer adversarial review 15 punti: **nessun HIGH/MEDIUM noto**. Il primo wrapper canonico ha superato il timeout del tool ma ha continuato controllato fino a PASS e cleanup; il rerun finale diretto nello stesso harness Noble isolato ha completato PASS. Non ripetere per questo motivo.
- File nel commit: `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_ubuntu_integration.py`, `tests/test_pilot_deployment.py`.
- `CHECKPOINT.md` resta intenzionalmente local modified/unstaged e non è nel commit. Nessun container/processo temporaneo rimasto.

### PR, CI e prossimo passo

- PR body aggiornata con Round 1 BLOCKED, H-03/H-04 CLOSED, candidate/test/merge-tree correnti; PR verificata `OPEN` e `DRAFT`.
- Unica CI snapshot post-push exact `db13ec01`: 11 check, 10 `IN_PROGRESS`, 1 `QUEUED`, 0 failure; `mergeStateStatus=UNSTABLE` per pending. Nessun polling.
- **Prossimo passo:** nuova sessione, una sola verifica CI sull'exact HEAD. Se tutta verde, avviare una **fresh Independent Review Round 1** sul candidate `db13ec01`; se failure, ispezionare soltanto il job exact e restare BLOCKED. Non usare questa sessione come independent reviewer, non mark-ready e non mergeare. Gate resta `0/2`.
- File minimi alla ripresa: `AGENTS.md`, `CHECKPOINT.md`; review checkpoint precedente solo per contesto finding. Diff da esaminare in review: `5472eef86568a4e7ce59ad34ba937220df27efd7...db13ec0113cda49bb18f09fa24459d10e1c7fdc1`.

---

## Remediation Independent Review Round 1 H-05 — candidate d7d779f5

- **Data/ora:** 2026-08-22T10:33:21+02:00
- **Obiettivo:** chiudere H-05, same-name/same-version package che ridefinisce i byte native trusted della PR #720 / issue #704.
- **Stato:** **IMPLEMENTATO, VERIFICATO, COMMITTATO E PUSHATO / CI IN PROGRESS**. PR `OPEN` e `DRAFT`; non mark-ready, non mergeata; independent gate **0/2**.
- **Candidate precedente / review:** `db13ec0113cda49bb18f09fa24459d10e1c7fdc1`; fresh Independent Review Round 1 **BLOCKED** per H-05. H-01/H-02/H-03/H-04 restano CLOSED.
- **Root cause:** nome/versione package e manifest md5 del package corrente permettevano al package installato di auto-autenticare nuovi byte executable.
- **Candidate nuovo:** commit/push fast-forward `d7d779f54fa3c14d9c0fbb0773c0d3cbd41c5447` (`fix: pin reviewed boot executable identities`).
- **Main / merge-base:** `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` / `5472eef86568a4e7ce59ad34ba937220df27efd7`. Merge-tree PASS, tree `b183d436c19f6fb1daf89b2fa0b5cc11d369a11c`.

### Remediation e coverage

- Primitive comune `PackageFileIdentityPolicy`: path canonico + package atteso + presenza + integrità dpkg corrente + SHA-256 statico revisionato + execution class, nella catena stable-read e owner/integrity pre/post.
- Inventario statico Noble in `scripts/pilot_ubuntu_reviewed_executables.py`, incluso nella toolchain/pin: 108 file behavior-bearing, 98 native e 10 interpreted.
- Coverage: 44 service policy; 43 fragment package; 2 drop-in; 55 Exec (48 present/7 absent, 46 native records); 2 Accept executable; 10 timer Exec/8 target unici; 2 interpreter risolti; 53 runtime command; activator, 12 generator e nginx binary/module. **ZERO expected-present behavior executable non pinning**.
- Baseline: OCI Ubuntu 24.04 digest fissato nel Dockerfile, inventario derivato il 2026-08-22; `systemd=255.4-1ubuntu8.17`, revisioni complete documentate in `doc/PILOT_DEPLOYMENT.md`. Upgrade con byte diversi fallisce chiuso fino a review/commit; nessun auto-refresh runtime.
- Generator attestati prima del primo `daemon-reload` e di nuovo dopo, per evitare esecuzione da parte del gate prima del reject.
- File commit: `doc/PILOT_DEPLOYMENT.md`, `scripts/build_pilot_toolchain.py`, `scripts/pilot_toolchain_launcher.py`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_ubuntu_integration.py`, `scripts/pilot_ubuntu_reviewed_executables.py`, `tests/test_pilot_deployment.py`.
- `CHECKPOINT.md` resta intenzionalmente modified/unstaged e non è nel commit.

### Reproducer e verifiche

- Pre-fix `db13ec01`: real `.deb` `systemd=255.4-1ubuntu8.17` amd64, owner `systemd`, manifest valido, exact reviewed fragment/effective Exec, renamed Python root-capable: production gate **ACCEPT**, marker assente solo perché il gate non avviava il service; restore PASS.
- Post-fix exact same-name/same-version: **reviewed artifact digest REJECT**, root marker provato prima e assente durante gate; exact fragment/drop-in/sette slot invariati; restore PASS.
- Same-name higher version, expected-present malicious Exec, Accept `systemd-sysext`, timer `fstrim`, interpreter `bash`, external command `grep`, nginx binary e systemd generator: tutti **REJECT** con package owner/manifest validi; restore pristine PASS.
- H-03 foreign owner, H-04 expected-absent fill, expected-present removal, modified native, H-01 same-line logrotate, H-02 SysV PATH shadow, unknown package service: PASS fail-closed.
- Targeted Linux Python 3.12: **10 passed**; Python 3.11: **10 passed**.
- Full Linux Python 3.12.14 + Node 20.20.2: **2448 passed, 20 skipped**.
- Full Linux Python 3.11.16 + Node 20.20.2: **2448 passed, 20 skipped**.
- Ubuntu 24.04/systemd 255 destructive integration finale: **PASS in 2513 s**, inclusi H-01–H-05, APT/e2scrub/motd/dpkg backup/eight timer/nginx/logrotate, migration/recovery/rollback e real rotate/reopen. La precedente terminazione a 30 minuti era sotto la durata normale osservata, non un hang.
- `compileall`, Bash syntax, Sphinx `-W`, course-plan e feature/worktree `git diff --check`: PASS.
- Developer adversarial review 17 punti: nessun HIGH/MEDIUM noto. Il self-review non conta per il gate indipendente.
- Tentativi ambientali da non ripetere: full suite su bind read-only fallisce sui lock; container senza `--init` lascia zombie; eseguire 3.12/3.11 in parallelo causa timeout; usare copia writable sequenziale con Docker `--init`. La fixture `dash` non può essere installata malevola perché rompe i maintainer script dpkg; la regression valida usa il reale interpreter `bash` della closure e2scrub.
- Nessun container, image temporanea o processo noto rimasto.

### PR, CI e prossimo passo

- PR body aggiornato con Round 1 `db13ec01` BLOCKED, H-05 CLOSED, inventory/test/candidate correnti; PR verificata `OPEN`, `DRAFT`, HEAD esatto.
- Unica CI snapshot post-push exact `d7d779f5`: 11 check, 1 `SUCCESS`, 10 `IN_PROGRESS`, 0 failed. Nessun polling.
- **Prossimo passo:** nuova sessione. Verificare una sola volta la CI exact-head; se non rossa, affidare a un reviewer indipendente una **fresh Independent Review Round 1** dell'intero diff `5472eef86568a4e7ce59ad34ba937220df27efd7...d7d779f54fa3c14d9c0fbb0773c0d3cbd41c5447`. Non usare l'author come reviewer, non mark-ready e non mergeare. Gate resta `0/2`.
- File minimi: `AGENTS.md`, `CHECKPOINT.md`; poi diff feature e documentazione/policy indicati sopra soltanto quanto necessario.

---

## Remediation Independent Review Round 2 — temporal verify/use fence

- **Data/ora:** 2026-08-23T13:38:25+02:00
- **Obiettivo:** chiudere i tre HIGH del Fresh Independent Review Round 2 sul candidate `d7d779f54fa3c14d9c0fbb0773c0d3cbd41c5447`.
- **Review precedente:** Round 1 **CLEAN**; Round 2 **BLOCKED** per HIGH-01 generator ABA, HIGH-02 nginx executable TOCTOU e HIGH-03 late effective unit a quattro slot. H-01..H-05 restano CLOSED.
- **Stato:** **IMPLEMENTATO, VERIFICATO, COMMITTATO E PUSHATO**. PR #720 verificata `OPEN`/`DRAFT`; non mark-ready, non mergeata; nuovo gate independent review **0/2**.
- **Candidate nuovo:** `51e9e539eccba0bc873d5e4f9c6bee34dbd9aabd` (`fix: linearize reviewed boot trust through activation`), push fast-forward normale.
- **Main / merge-base:** `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` / `5472eef86568a4e7ce59ad34ba937220df27efd7`; merge-tree PASS `b94f1492e44dd10bcb6820cb87eb1b4086e79573`.

### Architettura temporal trust

- Nuovo modulo `scripts/pilot_trusted_activation_fence.py`: snapshot indipendenti su tmpfs dedicato nel mount namespace di PID 1; remount dell'intero superblock `ro,nodev,nosuid`; bind delle copie sui pathname; verifica mountinfo/device/RO; fresh static attestation solo dopo freeze; privileged use e runtime proof prima del release.
- Sessione base: executable/package/nginx/systemd e metadata dpkg `status/info`; sessione execution: `/etc` e tutte le source runtime systemd non generated. Generator output resta writable a PID 1 e viene attestato dopo reload.
- FD preaperti modificano soltanto inode originali nascosti; manifest underlying deve restare invariato. Source hardlink provenance resta visibile alla static policy anche se la copia ha `nlink=1`.
- Lock host-global per due activator e lock POSIX dpkg/APT come defense-in-depth. Ogni systemctl execution-bearing è strutturalmente rifiutato fuori execution fence; owner PID/nesting/fork stale validati.
- `setup|active` metadata root-only in `/run/thebitlab/pilot-activation-fence`; recovery SIGKILL valida mount/manifest e smonta soltanto device/token TheBitLab exact. Underlying divergente resta poisoned/fail-closed. Snapshot trattenute da namespace systemd restano RO dopo detach.
- Nginx usa una sola policy canonica a sette slot: empty exact `ExecCondition`, `ExecStartPost`, `ExecStopPost`; exact Noble `ExecStartPre`, `ExecStart`, `ExecReload`, `ExecStop`. Late check riattesta fragment SHA, drop-in exact, slot/path/argv/ignore-errors, config, executable e moduli.
- Lifecycle: manager writes con `--no-reload`; mask viene caricato prima del final stop non più contendibile; start resta disabled dentro fence; l'exact wants link è l'unico delta underlying consentito sotto persistence fence dopo runtime proof. Recovery e rollback usano gli stessi boundary.
- Runtime nginx persistente viene riattestato frescamente da `/proc/<pid>/exe` SHA/native + tmpfs RO namespace + unit/cgroup/listener, senza trust cache PID/digest.
- Limite dichiarato: nessuna protezione da kernel compromesso, ptrace/modifica memoria trusted process, sostituzione interprete running o rimozione intenzionale fence con capacità mount.

### Evidenze e verifiche finali

- Race reali Ubuntu/systemd: generator add/replace/ABA/write/remove sotto fence, secondo external daemon-reload, nginx atomic rename, nginx/module same-inode via FD preaperti, expected-absent fill e `ExecStartPost` drop-in attempt: mutation bloccata o inode originale nascosto; **nessun marker UID 0**, nginx A avviato.
- Mutation B prima della fence: fresh SHA/package/class reject; fragment same path byte mutation e unexpected drop-in reject; test individuali `ExecCondition`/`ExecStartPost`/`ExecStopPost` reject.
- SIGKILL reale durante setup e active fence: recovery PASS. Full crash matrix production, concurrent start, recovery e rollback PASS.
- Due activator reali e lock dpkg: serialization PASS.
- Full Ubuntu 24.04/systemd 255 distruttiva sul source candidato finale: **PASS**; include H-01..H-05, nuove race, APT/e2scrub/motd/dpkg backup/eight timer, generatori, migration, crash recovery, rollback, nginx/logrotate e real rotate/reopen.
- Linux Python 3.12.14 + Node 20.20.2: **2451 passed, 20 skipped**.
- Linux Python 3.11.16 + Node 20.20.2: **2451 passed, 20 skipped**.
- `compileall`, syntax di tutti gli shell tracked, Sphinx `-W`, course-plan `--check`, `git diff --check`: **PASS**.
- Developer adversarial review completa: nessun HIGH/MEDIUM noto. Structural registry invariata: 44 service, 55 Exec, 108 executable file identities revisionate, zero expected-present unpinned.
- File commit: `doc/PILOT_DEPLOYMENT.md`, `doc/PILOT_SENSITIVE_LOG_HANDLING.md`, `scripts/build_pilot_toolchain.py`, `scripts/pilot_toolchain_launcher.py`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_ubuntu_integration.py`, `tests/test_pilot_deployment.py`.
- `CHECKPOINT.md` resta intenzionalmente modified/unstaged e non è nel commit. Nessun container/processo temporaneo noto; artifact/log di test rimossi.

### PR, CI e prossimo passo

- PR body aggiornato con Round 2 BLOCKED, root cause, remediation, race evidence, candidate e gate; PR resta `OPEN`/`DRAFT`.
- Unica CI snapshot exact HEAD: 11 check, **9 SUCCESS**, **2 IN_PROGRESS** (`Quality/python`, `Quality/windows-filesystem`), 0 failure. Nessun polling.
- **Prossimo passo:** nuova sessione e fresh **Independent Review Round 1** dell'intero diff `5472eef86568a4e7ce59ad34ba937220df27efd7...51e9e539eccba0bc873d5e4f9c6bee34dbd9aabd`. Prima verificare una sola volta che exact-head CI non sia rossa; se failure, ispezionare il solo job exact e restare BLOCKED. Non mark-ready e non mergeare. Gate 0/2; ogni commit lo mantiene/azzera.
- File minimi alla ripresa: `AGENTS.md`, `CHECKPOINT.md`, `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_trusted_activation_fence.py`; poi diff completo per la review indipendente.

---

## Fresh Independent Review Round 1 remediation — candidate 598f1905

- **Data/ora:** 2026-08-24T05:30:00+02:00
- **Candidate precedente:** `51e9e539eccba0bc873d5e4f9c6bee34dbd9aabd`.
- **Fresh Independent Round 1:** **BLOCKED**, gate `0/2` per R1-HIGH-01 dynamic-loader closure incompleta, R1-HIGH-02 recovery autorizzata da metadata forged, R1-HIGH-03 race generated-output/reload e R1-LOW-01 wants-link senza GID 0. H-01..H-05 non riaperti.
- **Riproduzioni pre-modifica:** preload `.so` eseguita due volte in `systemd-path` con `uid=0 euid=0`; forged v1 `root=/run/lock` ha smontato il foreign tmpfs e rimosso il sentinel; mutatore concorrente su `generator.early` + secondo reload ha caricato `ExecStartPost` e creato marker `uid=0 gid=0`.

### Remediation

- **HIGH-01:** bootstrap senza subprocess; base snapshot di executable e `/usr/lib`; alias usrmerge `/bin`, `/sbin`, `/lib`, `/lib64` convertite temporaneamente in exact bind frozen. Parser ELF puro Python e policy statica Noble separata: 98 root ELF, 1 PT_INTERP, 49 shared-library identity, 263 plugin/provider/NSS/gconv/nginx identity. `ld.so.cache`, `nsswitch.conf`, OpenSSL config pinnati; `/etc/ld.so.preload` obbligatoriamente assente prima del primo `systemd-path`. Tutti i subprocess dentro una trusted session richiedono closure ready. Runtime `/proc/<pid>/maps` prova nginx, loader, libc, libssl/libcrypto e moduli.
- **HIGH-02:** state schema v2 chiuso, token/root canonici e fasi planned/witnessed/sealed/active/teardown; tmpfs source kernel univoca `thebitlab-pilot-fence:<token>`, mount ID/parent/device/source/root/options; manifest immutabile nel tmpfs RO. Cleanup deriva i mount da mountinfo/source, non da target JSON; nessun `rmtree`; planned root senza witness resta intatto/manuale. Crash setup/active/teardown e mount ABA/foreign/symlink metadata falliscono sicuri.
- **HIGH-03:** source generator frozen, reload trusted con output writable, nested snapshot/seal RO su `generator.early`, `generator`, `generator.late`, quindi attestazione output + graph manager + Fragment/DropIn + seven slots e start mentre il seal resta attivo. Su systemd 255 il secondo reload reale torna 0 consumando lo stesso graph sealed; exact marker resta assente.
- **LOW-01:** symlink systemd e persistence manifest richiedono UID 0 **e GID 0**, oltre a target/path/parent exact.

### Evidenze finali

- Ubuntu 24.04/systemd 255 full distruttiva canonica: **PASS**; include preload/loader/libc/libssl/libcrypto/systemd-dependency/provider/module, nginx `-t/-T`, usrmerge, forged metadata/foreign tmpfs, SIGKILL base/execution/generated/teardown, generated-output in tutte tre roots, secondo reload, seven slots, H-01..H-05, due activator, dpkg contention, activation/recovery/rollback, secret-safe logging e real logrotate FD reopen.
- Linux Python 3.12 + Node 20.20.2: **2455 passed, 20 skipped**.
- Linux Python 3.11 + Node 20.20.2: **2455 passed, 20 skipped**.
- `compileall`, 15 shell tracked `bash -n`, Sphinx `-W`, course-plan e `git diff --check`: **PASS**.
- Developer adversarial review dei 34 punti richiesti: nessun HIGH/MEDIUM noto; exact marker preload/generated assenti dopo remediation; foreign mount ID/device/sentinel preservati.
- File production/test/doc: Dockerfile integration, due doc canonici, toolchain builder/launcher, fence, activation, integration, test deployment, nuovi `pilot_native_execution_closure.py` e `pilot_ubuntu_reviewed_native_code.py`.
- Nessun container/processo/log temporaneo rimasto. `CHECKPOINT.md` resta local-only **UNSTAGED** e non deve essere committato.
- **Candidate nuovo:** `598f1905462b5df0cb5f009ea79cffb7901545b8` (`fix: close privileged activation execution graph`), push fast-forward normale. PR verificata `OPEN`/`DRAFT`; gate `0/2`.
- Main / merge-base: `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` / `5472eef86568a4e7ce59ad34ba937220df27efd7`; merge-tree PASS `40a930675386a35096d310c00a8ff8801ac3a381`.
- PR body aggiornato preservando lo storico e registrando i tre exploit exact/remediation/evidenze.
- Unica snapshot CI exact HEAD: 8 `SUCCESS`, 3 `IN_PROGRESS` (`Quality/python`, `minimum-python`, `windows-filesystem`), 0 failure; nessun polling.
- **Prossimo passo:** fresh Independent Review Round 1 dell'intero diff `5472eef86568a4e7ce59ad34ba937220df27efd7...598f1905462b5df0cb5f009ea79cffb7901545b8`. Non mark-ready, non mergeare; ogni nuovo commit resetta il gate a `0/2`.

---

## Remediation Fresh Round 1 R1-HIGH-01A/B — BLOCKED

- **Data/ora:** 2026-08-24T20:40+02:00.
- **Previous/current candidate:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; Fresh Independent Review Round 1 **BLOCKED**; gate `0/2`.
- **Open:** R1-HIGH-01A e R1-HIGH-01B. **Preserved richiesti:** R1-HIGH-02, R1-HIGH-03, R1-LOW-01, H-01..H-05.
- **Root cause A:** lo shebang `/usr/bin/python3 -IB` carica interprete/loader/preload prima di qualunque statement Python; inoltre il launcher eseguiva un secondo Python.
- **Root cause B:** i 408 path risolti non coprivano alternative RUNPATH/default `glibc-hwcaps`; freeze di un file sconosciuto non conferisce trust.

### Riproduzioni e prototipo locale

- Pre-modifica exact canonical con `/etc/ld.so.preload`: constructor `thebitlab-pilot uid=0/euid=0` e `python3 uid=0/euid=0`, poi reject tardivo.
- Pre-modifica exact systemd RUNPATH v3: fence e `systemd-path` PASS, tre constructor `systemd-path uid=0/euid=0` da oggetti fuori dalle 408 identity.
- Prototipo non committato: bootstrap Go `CGO_ENABLED=0` statico; Stage 0 usa transaction/witness/manifest kernel della fence esistente, attesta Python/loader/tree/toolchain/pin e fa un solo child `-I -B`; handoff Stage 0→Stage 1 sigilla la seconda snapshot prima del release.
- Policy lookup prototipo: exact tree manifest Noble, parser bounded cache 1.1 (101 entry, zero hwcap), v2/v3/v4 CPU-portable, 735 candidate `EXPECTED_ABSENT` (245/livello), zero candidate dichiarate unpinned; environment `LD_*`/`GLIBC_TUNABLES` non inoltrato.
- Post-fix privilegiato mirato: build x86-64 statico, nessun PT_INTERP e nessuna dynamic section; canonical preload-before e sei timing constructor count 0; exact v3 e v2/v4/libc/libssl/libcrypto/Python/symlink marker 0; sei crash Stage 0 fail-closed/recovery con foreign `/run/lock` intatto.
- `tests/test_pilot_deployment.py`: **PASS** su Python 3.12 (skip platform previsti). Pycompile mirato e Bash syntax runner: PASS. `git diff --check`: PASS.

### Blocco integrazione obbligatoria

La full Ubuntu 24.04/systemd 255 non ha mai raggiunto exit finale:

1. timeout 8000 s durante esecuzione CPU-active dopo le race generated-output;
2. timeout 7200 s dopo ottimizzazione crash Stage 1 a fork reale;
3. timeout 6500 s dopo separazione della matrice Stage 0 completa dal run distruttivo.

Ogni run ha mantenuto verdi fino al punto osservato: exact preload/v3, closure counters, H-01..H-05, R1-HIGH-02 forged/foreign/crash, R1-HIGH-03 generated-output+second reload, R1-LOW-01 GID, two activators/package locks e input provenance. L'ultimo era ancora CPU-active dopo `disk mask vs PID1 cache`; nessun errore, ma **nessun FINAL PASS**. Tutti i container/image/processi temporanei sono stati rimossi. Non ripetere un quarto run identico: serve una decisione/profilazione architetturale separata sul costo snapshot oppure un runner Linux nativo sufficientemente veloce; non alzare soltanto il timeout.

### Git, PR e verifiche omesse

- Modifiche locali non committate: `.dockerignore`, Dockerfile, due doc, builder/launcher/fence/closure/activation/integration/runner, test; nuovi `scripts/pilot_static_bootstrap.go` e `scripts/pilot_ubuntu_loader_lookup_policy.py`.
- Nessun file staged; `CHECKPOINT.md` resta local-only **UNSTAGED**. Nessun commit/push/CI snapshot.
- PR #720 aggiornata con il Fresh Round 1 BLOCKED; verificata `OPEN`, `DRAFT`, HEAD ancora `598f1905`; entrambi gli HIGH restano OPEN.
- Python complete 3.12/3.11, compileall completo, tutti i Bash, Sphinx, course-plan e full integration finale **non eseguiti/non validi**, perché il gate distruttivo preliminare è bloccato. Non dichiarare candidate.
- Main/merge-base preflight invariati: `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` / `5472eef86568a4e7ce59ad34ba937220df27efd7`.

**Prossimo passo:** nuova sessione distinta per decidere come rendere il fence snapshot performante senza indebolire freeze/attest/use (profilazione su Linux nativo o primitive snapshot equivalente). Solo dopo un FINAL PASS riprendere matrici complete, docs finali, commit/push e fresh Independent Review Round 1. File minimi: `AGENTS.md`, `CHECKPOINT.md`, `scripts/pilot_static_bootstrap.go`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_ubuntu_integration.py`, `scripts/pilot_native_execution_closure.py`, `scripts/pilot_ubuntu_loader_lookup_policy.py`.

---

## Profiling architetturale execution fence — BLOCKED

- **Data/ora:** 2026-08-25T05:55:19+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; prototipo security precedente integralmente preservato e ancora **NON COMMITTATO**. `CHECKPOINT.md` resta **UNSTAGED** e non deve essere committato.
- **Stato finding/gate:** R1-HIGH-01A **OPEN**, R1-HIGH-01B **OPEN**, gate `0/2`; R1-HIGH-02/R1-HIGH-03/R1-LOW-01/H-01..H-05 restano CLOSED sulla sola evidenza precedente. PR #720 resta `OPEN`/`DRAFT`; nessun candidate nuovo.
- **Vincolo storico:** i tre run monolitici precedenti sono terminati senza risultato finale dopo circa `8000/7200/6500 s`, ancora CPU-active. Nessun quarto run identico è stato eseguito.

### Profiling privilegiato BEFORE

Modalità review-only: un singolo vero `preflight` privilegiato per misura, in container Ubuntu 24.04/systemd 255 effimero, usando i pause point test-only esistenti e i manifest immutabili delle transaction. Nessuna suite distruttiva. Due acquisizioni complete riuscite; un'acquisizione teardown intermedia è scaduta soltanto perché il profiler attendeva erroneamente una quarta fence Python (le fence sono tre), poi corretta concretamente. Container, image e processi rimossi.

Contatori manifest per transaction:

| Fase | wall costruzione osservato | CPU processo osservata | entry | file | byte copiati | target |
|---|---:|---:|---:|---:|---:|---:|
| Stage 0 | 3.254–9.813 s | 3.96–11.43 s | 4,154 | 3,486 | 139,116,955 | 6 |
| Stage 1 base | 6.075–25.120 s | 6.07–25.35 s | 4,547 | 4,001 | 142,200,346 | 16 |
| execution fence | 3.899–15.956 s | 3.88–15.92 s | 306 | 179 | 281,794 | 6 |
| generated-output seal | 1.841–7.508 s | 1.31–5.75 s | 4 | 0 | 0 | 3 |

Il secondo preflight segmentato ha misurato inoltre: attest/use/runtime-proof `45.343 s wall / 29.47 s CPU processo`; generated teardown `0.613/0.60 s`; execution teardown `9.648/9.63 s`; base+Stage-0 release `9.777 s wall`; totale `123.777 s wall / 121.857 s CPU figli`, rc 0. La variabilità Docker Desktop è elevata, ma byte/entry e dominante sono deterministici.

Root cause misurata:

- Stage 0 copia l'intero `/usr/lib` (2,850 file, 91,095,319 B), `/usr/bin` (335, 37,167,637 B), `/usr/sbin` (122, 10,572,205 B) e `/etc` (179, 281,794 B).
- Stage 1 ricopia **tutti** i 3,486 file/139,116,955 B Stage-0: `/usr/{bin,sbin,lib,local,lib64}` nella base e `/etc` nell'execution fence. Duplicati Stage0→Stage1: **3,486 identity / 139,116,955 B**.
- L'algoritmo Stage-0 esegue almeno 7 walk completi e 6 hash completi della snapshot durante costruzione, adozione e release: almeno 29,078 entry-walk (più 2,692 entry delle tree policy), 20,916 file/834,701,730 B hashati, più 2,386 file/~84.1 MB delle lookup-tree e file/toolchain singoli.
- Stage-1 base esegue 9 walk completi, copia 4,001 file/142,200,346 B e hasha gli stessi file 6 volte: 40,923 entry-walk, 24,006 file/853,202,076 B hashati.
- Execution fence: 2,448 entry-walk, 179 file copiati, 895 hash/~1.41 MB. Generated output ha zero payload; il suo costo è mount/state/attestazione, non byte copy.
- Un solo preflight legge quindi almeno ~1.78 GB per SHA, oltre a ~281.6 MB copiati. Top repeated-hash: `/usr/lib` ~1.09 GB, `/usr/bin` ~446 MB, `/usr/sbin` ~127 MB; `/var/lib/dpkg/info` è solo 3.19 MB copiati ma viene rihashato sei volte. Python runtime e package metadata sono entrambi ripercorsi/riletti; la stessa native identity è duplicata tra Stage 0 e Stage 1.
- Stage-0 runtime map reale al primo statement trusted: 19 file executable mapping, 18,926,832 B (Python, loader, libc/libm/libz/libexpat, OpenSSL, ffi/bz2/lzma e 8 extension Python). Import inventory iniziale: 169 moduli Python host, 4,265,452 B. Questi dati dimostrano che l'execution graph è molto più piccolo dell'albero copiato, ma non costituiscono policy appresa: gli hash accettati devono restare repository-static.

### Decisione architetturale

Target investigato: snapshot execution-graph sparse con exact expected-present object, Stage1 delta, one-pass source copy+SHA, manifest immutabile, exact-file mounts, sealed empty `glibc-hwcaps/{v2,v3,v4}` e bind anchor per componenti/alias usrmerge. Il costo previsto scende da 281.6 MB copiati a circa 23.2 MB Stage-0 expected-present più il delta Stage-1.

**Non adottato:** nell'attuale mount namespace globale di PID 1 non è stata trovata una prova sufficiente che exact-file mount + shared mutable parent impedisca parent rename/alias substitution/normal RUNPATH candidate insertion da directory FD preaperto. Rendere sparse globalmente `/usr/lib/x86_64-linux-gnu`, `systemd`, `gconv` o i namespace Python nasconde file a servizi non correlati e non ha prova di compatibilità. Un self-bind anchor impedisce rename del mountpoint, ma non impedisce modifiche underlying da alias/FD preaperti; un expected-absent normal/import candidate potrebbe diventare visibile. Copiare l'intera directory risolve questo punto ma ricade nel filesystem-tree snapshot misurato. Nessuna di queste scorciatoie è stata implementata.

Alternative ancora valide, da decidere architetturalmente:

1. Stage 0 in mount namespace privato, con loader invocato esplicitamente e runtime/import graph sparse, seguito da broker statico che costruisce/attesta Stage 1 nel namespace PID 1 senza gap; richiede nuovo contratto `setns`/handoff e recovery.
2. Requisito host fs-verity/IMA/dm-verity per code parent e package payload, più namespace hwcaps sparse e fresh kernel attestation; cambia il contratto di provisioning.
3. Snapshot globale delle sole lookup directory complete (`systemd`, `gconv`, Python package roots) con quiescing/compatibility proof di tutti i servizi; più semplice ma ancora potenzialmente ampio/disruptive.
4. Boot-scoped cache sealed soltanto dopo aver risolto il modello di namespace/path authority; non è una soluzione al problema di sicurezza e non va iniziata prima.

Il one-pass copy/hash e l'eliminazione dei rehash post-seal sono sicuri soltanto se la costruzione protegge directory enumeration, source identity/stability e snapshot da writer root fino al remount RO. Da soli riducono I/O ma non risolvono la duplicazione né il lookup namespace; non sono stati applicati isolatamente.

### Shard architecture pianificata, non implementata

A `bootstrap-loader`; B `fence-recovery`; C `systemd-generated`; D `historical-execution`; E `lifecycle+late-dlopen/worker`; F `logging`. Ogni evidence record deve contenere `scenario_id`, pristine/predecessor state, candidate SHA, OCI digest, toolchain/policy digest, Python/Node identity, result/skip e cleanup witness. Scenari stateful restano nello stesso shard. Aggregator canonicale deve rifiutare SHA/digest/policy divergenti, scenari mancanti/duplicati/conflicting, skip inattesi e cleanup invalido; solo esso può emettere la PASS completa. Nessuno shard/aggregator è stato ancora implementato o eseguito.

### Verifiche e prossimo passo

- Profiling privilegiato singolo preflight: PASS e root cause determinata.
- `git diff --check`: PASS prima dell'aggiornamento checkpoint.
- Targeted exploit, late dlopen/worker, shard, full destructive, Python 3.12/3.11 e doc matrix: **NON rieseguiti**; evidenza precedente non chiude R1-HIGH-01A/B.
- Nessun file production/test/doc modificato in questa fase; solo checkpoint aggiornato. Nessun commit/push.
- **Stato:** `BLOCKED — ARCHITECTURAL SECURITY DECISION REQUIRED`.
- **Prossimo passo:** scegliere esplicitamente tra namespace Stage-0 privato con broker statico e nuovo requisito di immutabilità host; poi prototipare la scelta con attacchi parent/alias/preopen/mount e microbenchmark prima degli shard.
- File minimi: `AGENTS.md`, `CHECKPOINT.md`, `scripts/pilot_static_bootstrap.go`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_native_execution_closure.py`, `scripts/pilot_ubuntu_loader_lookup_policy.py`.

---

## Private runtime architecture/security POC — BLOCKED al manager boundary

- **Data/ora:** 2026-08-25T08:43:25+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 invariata `OPEN`/`DRAFT`; gate `0/2`.
- **Decisione architetturale confermata:** `PRIVATE STAGE0 + STATIC STAGE1 BROKER`. **Host immutability (fs-verity/IMA/dm-verity) NON è un requisito baseline** e non è stata reintrodotta.
- **Stato:** **BLOCKED — PRIVATE-RUNTIME ARCHITECTURE FAILED al boundary di esecuzione systemd 255**. R1-HIGH-01A/B restano **OPEN**; R1-HIGH-02, R1-HIGH-03, R1-LOW-01 e H-01..H-05 restano **CLOSED** sulla precedente evidenza, non rieseguita dalla matrice monolitica.
- Nessun commit, push o aggiornamento PR. Tutto il prototipo precedente è preservato; `CHECKPOINT.md` resta **UNSTAGED**.

### POC implementato

- Nuovi file locali non committati: `scripts/pilot_private_runtime_poc.go` e `scripts/pilot_private_runtime_poc.py`; runner/Dockerfile supportano solo l'opzione mirata `--private-runtime-poc`.
- Un solo artifact Go CGO-free, statico, senza PT_INTERP/dynamic section funge da Stage0, server broker PID1, client sealed e broker N2.
- **S0:** tmpfs con source kernel exact `thebitlab-private-s0`, remount RO, mount namespace nuovo/private e `pivot_root`; root sintetico senza bind a code tree host. Copia one-pass FD stabile + SHA-256 simultaneo di tre tree policy Noble (`x86_64-linux-gnu`, stdlib 3.12, dist-packages), Python, config minima, toolchain pinned e broker statico. Loader interno esplicito con `--inhibit-cache`; hwcaps v2/v3/v4 expected-absent.
- **Handoff:** il bootstrap avvia prima dell'unshare un server dello stesso broker statico nel namespace PID1. Il client copiato in S0 invia soltanto il selettore token; il server riattesta state, token, manifest, source mount e RO prima di costruire S1. Il tentativo iniziale `setns` da runtime Go multithreaded è stato correttamente rigettato `EINVAL` e non va ripetuto.
- **S1:** delta RO tmpfs `thebitlab-private-s1`: nginx, due moduli, `start-stop-daemon`, tree config/share; nessun payload S0 ricopiato. Grafo execution nginx completo: 12 identity, 8 già in S0 (`9,327,384 B`) e 4 delta; duplicate copy `0`.
- **Composizione:** overlayfs read-only multi-lower `lowerdir=S1:S0`, nessun upper. Lower replacement, inserimento hwcaps, sibling manager, symlink/alias/path host non attraversano il root sintetico.
- **PID1 surface POC:** due exact mount/file source manager, `1,623 B` complessivi: drop-in N1 e unit N2; l'unit N2 è un exact file bind RO proveniente da S1.

### Sicurezza passata prima del blocco

- Exact `/etc/ld.so.preload` presente prima del launcher canonico: **ZERO marker**, Python eseguito dal loader S0.
- Exact hwcaps v3 wrapper e rappresentanti v2/v4: **EXPECTED_ABSENT reject, ZERO marker**.
- S0 root/mount RO e namespace/pivot witness: PASS.
- Parent rename, toolchain alias substitution, pre-opened host directory FD, host tree rename, nuovo normal candidate, nuovo hwcaps candidate, Python `.py` e native extension lazy replacement: root privato usa la copia reviewed; PASS.
- S1 lower/merged hwcaps e manager unexpected sibling: write bloccata `EROFS`; PASS.
- Overlay read-only costruito con successo sul kernel Ubuntu 24.04 Docker target.
- Non eseguiti dopo il blocker: complete nginx runtime maps/late dlopen, HTTP/TLS lifecycle completo, manager generated-output race matrix, loader/libc pre-build mutation e full destructive/shard matrix. Non usarli come evidenza di chiusura HIGH-01A/B.

### N1 e N2 — blocker concreto

- **N1 RootDirectory:** baseline e mutazioni host `nginx`/`libssl` avviano correttamente nginx. Dopo una barriera static ExecStartPre, mutare soltanto host `libcrypto.so.3` prima di `ExecStart` produce status `127`. Quindi systemd 255 consuma una closure dinamica host fra gli slot prima dell'exec nel RootDirectory. **N1 REJECTED**.
- N1 ha richiesto l'exact override manager-visible di `PIDFile` perché systemd 255 non cerca il PID file nel bind `/run` service-private; questo punto era stato risolto e non è il blocker finale.
- **N2 static broker:** l'exact unit RO punta come ExecStart al broker statico dentro S0. Il marker post-pivot del pristine ExecStartPre prova root `/`, digest S0 `libcrypto=1451acee...`; dopo la stessa mutazione host, il successivo static ExecStart non raggiunge il primo marker e systemd restituisce `127`. **N2 REJECTED**: il codice dinamico host è consumato prima che PID1 raggiunga perfino il target statico.
- Un tentativo reachability `Type=simple` era stato erroneamente considerato positivo perché `systemctl start` può tornare 0 prima dell'exec failure; la prova marker successiva lo ha corretto. Non riusare quel risultato.
- Non applicare retry casuali: proseguire richiede una nuova decisione esplicita su una primitive manager che eviti l'execution helper dinamico oppure su un fence globale della sua closure. Quest'ultimo rischia di riproporre il problema globale e non va introdotto implicitamente; host immutability resta fuori baseline.

### Microbenchmark AFTER

| Fase | wall | CPU | file copiati/hash | byte copiati/hash |
|---|---:|---:|---:|---:|
| S0 | 3.347458 s | 3.586061 s | 2,413 | 94,767,686 |
| S1 delta | 0.095517 s | 0.103109 s | 20 | 1,590,642 |
| overlay compose | 0.000270 s | — | 0 | 0 |
| manager fence | 0.000611 s | — | 2 source | 1,623 |

- S0 identity manifest: 2,414; S1 object identity: 20; present objects totali riportati: 2,434.
- Expected-absent loader candidates: 735 = 245 v2 + 245 v3 + 245 v4; copied bytes `0`; unpinned selectable `0`.
- BEFORE copy: `281,317,301 B`; AFTER unique copy: `96,358,328 B` → `2.92x` meno byte.
- BEFORE hash: `~1.78 GB`; AFTER hash: `96,358,328 B` → `~18.47x` meno I/O hash.
- BEFORE representative preflight: `123.777 s`; AFTER S0+S1+compose+manager build: `3.443856 s` → `~35.94x` sul build path. Il preflight end-to-end non completa per il blocker manager, quindi non dichiarare superato il performance gate complessivo; duplicate S0→S1 copy è comunque `0`.

### Verifiche, cleanup e prossimo passo

- Comando mirato: `bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-poc` → exit `2` atteso con report strutturato `BLOCKED`; nessuna suite monolitica avviata.
- Static build: due Go binary statici, zero PT_INTERP e zero dynamic section: PASS.
- Python `py_compile`, Bash `-n`, `git diff --check`: PASS.
- Full destructive, shard, full Python 3.12/3.11, Sphinx/course plan: non eseguiti, non pertinenti finché il POC è bloccato.
- Container/image temporanei e processi: rimossi; zero container attivi. Rimangono soltanto i due vecchi container Docker estranei già exited.
- **Prossimo passo:** decisione security architecture separata sul manager execution boundary. Non ripetere N1/N2 identici. Valutare con evidenza systemd 255 se esiste una primitive PID1 che esegua il broker statico senza helper dinamico host; in assenza, dichiarare incompatibile la baseline oppure autorizzare esplicitamente un nuovo modello. Non riaprire fs-verity/IMA/dm-verity implicitamente.
- File minimi: `AGENTS.md`, `CHECKPOINT.md`, `scripts/pilot_private_runtime_poc.go`, `scripts/pilot_private_runtime_poc.py`, `.pi-private-runtime-poc.log`; consultare gli altri file del prototipo soltanto se necessari alla decisione.

---

## Manager executor boundary POC — A NARROW MANAGER FENCE deciso

- **Data/ora:** 2026-08-25T10:15:42+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 invariata `OPEN`/`DRAFT`; gate `0/2`; nessun commit/push/candidate.
- **Stato:** **MANAGER BOUNDARY DECIDED — READY FOR INTEGRATION**. Selezionata **A NARROW MANAGER FENCE**; S0/S1 privati restano invariati. R1-HIGH-01A/B restano OPEN fino a late-dlopen, worker-respawn, shard finali e aggregator PASS. R1-HIGH-02/R1-HIGH-03/R1-LOW-01/H-01..H-05 non sono regrediti: nessun loro sorgente è stato modificato.

### Processo e grafo manager esatto

- Container reale Ubuntu 24.04, `systemd 255.4-1ubuntu8.17`, package `systemd`. PID1 conserva `/proc/1/fd/8 -> /usr/lib/systemd/systemd-executor` e fa `clone3(CLONE_VM|CLONE_VFORK|CLONE_CLEAR_SIGHAND)` seguito nel child da `execve("/proc/self/fd/8", ["/usr/lib/systemd/systemd-executor", "--deserialize", ...])`.
- Executor: `/usr/lib/systemd/systemd-executor`; SHA-256 `b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044`; ELF64 x86-64 PIE; PT_INTERP `/lib64/ld-linux-x86-64.so.2`; RUNPATH `/usr/lib/x86_64-linux-gnu/systemd`; nessun RPATH. Direct DT_NEEDED: `libsystemd-core-255.so`, `libsystemd-shared-255.so`, `libapparmor.so.1`, `libpam.so.0`, `libseccomp.so.2`, `libselinux.so.1`, `libc.so.6`.
- Traccia canonicale: PID1 spawn `1787645325.445837`; child PID 140 executor exec `1787645325.447607`; `ld.so.cache` open `1787645325.463788`; child loader apre `libcrypto.so.3` `1787645325.648760`; target `/usr/bin/sleep` exec `1787645325.998121`. Snapshot `/proc/140/exe` e maps pre-target: exact executor + loader + 23 librerie, 25 identità complessive.
- `libcrypto` è già mappata nel PID1 dal boot, ma la mutazione che causa exit 127 viene caricata nuovamente dal **dynamic loader del child systemd-executor**. `libsystemd-shared-255.so` ha un DT_NEEDED diretto su `libcrypto.so.3`; non è un late `dlopen` del PID1 né un altro helper.
- Grafo chiuso: 25 code identity, 59 archi DT_NEEDED ricorsivi, `19,435,072 B`; reviewed-present 25. Expected-absent manager-specific 27: 21 candidati hwcaps CPU-portable (7 direct SONAME × v2/v3/v4 nel RUNPATH systemd), 5 normali miss RUNPATH prima della cache e `/etc/ld.so.preload`. Selectable-but-unclassified: **0**. Cache Noble SHA-256 `cce0b33c762f0c8de876998628011571c731267320958a596784d53e8d21af1b`, 101 entry, zero hwcap entry.
- Prima del target la trace non apre/mappa NSS, gconv, PAM module o OpenSSL provider. Le directory NSS/gconv/PAM/provider sono comunque sotto la vista S0 opaca revisionata; config/cache `/etc` è nella vista Stage-M. Default OpenSSL è built-in nel caso canonico. Nessun locale/code-conversion object code-bearing è raggiunto pre-target.

### Stage-M selezionato e riuso S0

- Stage-M usa la stessa transaction/witness/manifest/recovery authority di `TrustedActivationFence`; non va introdotto uno state/cleanup alternativo. Il broker statico già esistente costruisce S0, poi Stage-M prima di qualsiasi richiesta PID1.
- Lookup projection finale: bind directory-level RO S0 su `/usr/lib/x86_64-linux-gnu`; alias `/lib` sostituito temporaneamente con vista directory RO S0; viste RO S0 su `/usr/lib64` e alias `/lib64`; snapshot RO Stage-M di `/etc`. L'executor è attestato tramite exact FD PID1/package/SHA. `/usr/lib/systemd` non viene nascosta: un primo POC troppo ampio su `/usr/lib` ha correttamente rotto `daemon-reload` (`sysinit.target` nascosto) ed è stato ristretto al lookup multiarch.
- La vista directory completa S0 rende opachi systemd RUNPATH, hwcaps, NSS, gconv, PAM e provider. `ld.so.cache`, loader config e assenza preload sono congelati dalla vista `/etc`. Non c'è overlay con lower host selezionabile.
- `MANAGER_REQUIRED`: 25 identity / `19,435,072 B`. Intersezione S0: 24 identity / `19,297,280 B`. Delta code: il solo executor `137,792 B`. Stage-M costruito conservativamente con executor + namespace `/etc`: 172 file / `411,319 B`; hash bytes `411,319 B`; nessuna ricopia delle 24 librerie S0.
- Misure su due costruzioni: wall `0.147–0.486 s`, CPU `0.147–0.463 s`; dato conservativo per report `0.486/0.463 s`. Mount: 5 proiezioni + 1 tmpfs transaction = 6. S0 run della sessione `2.309 s`, S1 `0.088 s`, compose `0.00039 s`; representative build Stage-M+S0+S1 `2.883 s` contro `123.777 s`, circa `42.9x`. La variabilità Docker impone di rimisurare nell'integrazione, ma il costo è accettabile.

### Attacchi e handoff

- Attacker con FD preaperti su host `/etc`, `/usr/lib/x86_64-linux-gnu`, `/usr/lib64` ha, dopo seal, creato lower `/etc/ld.so.preload`, sostituito lower loader e `libcrypto`, e inserito malicious `libsystemd-shared-255.so` in hwcaps v2/v3/v4. Viste Stage-M: preload assente, loader/libcrypto SHA pristine, hwcaps count zero; constructor preload e hwcaps marker entrambi **ZERO**.
- Parent `/usr` rename bloccato (`EXDEV`); unlink/substitution alias `/lib` e `/lib64` bloccati; preopened lower writer non emerge. Normal SONAME `libcrypto`, PT_INTERP e cache restano sealed. Dopo cleanup lower ripristinato esatto e alias usrmerge ripristinati.
- N2 start sotto tutte le mutazioni raggiunge il broker statico, pivot S0/S1 e nginx. Positive handshake sul cgroup: 9 PID e 11 mapping eseguibili, tutti presenti nei manifest S0/S1 con SHA runtime esatto, inclusi nginx, loader, libc, libssl, libcrypto e moduli. Nessun gap manager→target osservato.
- Il vecchio comando N2 `ExecReload` raggiunge il broker sealed e scrive il marker S0, ma nginx termina rc 1 per il PID-file vuoto nel POC; è un difetto applicativo del POC non attribuibile a Stage-M. Per isolare la proprietà, una unità separata con i sette slot canonici (`ExecCondition`, `ExecStartPre`, `ExecStart`, `ExecStartPost`, `ExecReload`, `ExecStop`, `ExecStopPost`) tutti sul broker statico S0 ha completato start/reload/stop sotto le stesse mutazioni: `224/94/101 ms`, marker preload/hwcaps ZERO. Questo prova la riattivazione/protezione per ogni fresh executor; l'integrazione deve mantenere Stage-M fino al positive target-map handshake e riattivarlo per ogni slot successivo.

### Verifiche, cleanup e prossimo passo

- Eseguiti soltanto i test mirati richiesti: identity trace, loader/cache/libcrypto, preload, PT_INTERP, normal SONAME, hwcaps v2/v3/v4 `libsystemd-shared`, parent/alias, preopened writer, target-map handshake, reload e stop/seven-slot. Nessuna full suite/shard, late-dlopen o worker-respawn: restano blocker R1-HIGH-01A/B.
- Due errori POC non-security da non ripetere: strumenti tracing installati cambiano correttamente la tree policy S0; non lanciare binari dinamici tra unlink e mount alias PT_INTERP. Un tentativo `/usr/lib` broad ha fallito compatibility ed è stato ristretto come sopra.
- Hash dei 16 file del prototipo verificati identici prima/dopo. Solo `CHECKPOINT.md` aggiornato; tutto resta unstaged. Container, image e processi `pi704-*` rimossi; nessun processo temporaneo noto.
- **Prossimo passo:** integrare Stage-M nella transaction/recovery authority esistente e nel broker statico, attestare FD executor + graph statico, implementare acquire/handoff/reacquire per i sette slot, quindi rieseguire gli stessi targeted test. Solo dopo passare a late-dlopen/worker e shard/aggregator finali. Non commit/push/PR update finché non autorizzato.
- File minimi: `AGENTS.md`, `CHECKPOINT.md`, `scripts/pilot_private_runtime_poc.go`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_static_bootstrap.go`, `scripts/pilot_native_execution_closure.py`, `scripts/pilot_ubuntu_loader_lookup_policy.py`.

---

## Stage-M production integration — BLOCKED da mutable PID1 executor FD

- **Data/ora:** 2026-08-25T10:36:08+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 resta `OPEN`/`DRAFT`; gate `0/2`; nessun candidate, commit, push o staging.
- **Stato:** **BLOCKED — INTEGRATED STAGE-M SECURITY FAILURE**. R1-HIGH-01A/B restano OPEN. Il prototipo locale è stato preservato integralmente; nessun file production/test/doc è stato modificato in questa fase. `CHECKPOINT.md` resta UNSTAGED.

### Exploit esatto

- PID1 conserva un FD preaperto (`/proc/1/fd/8`) sull'inode host `/usr/lib/systemd/systemd-executor` e lancia ogni slot tramite quel FD. Un bind Stage-M RO sul pathname non sostituisce l'inode già referenziato dal FD.
- POC mirato Ubuntu 24.04/systemd 255: aperto un writer sull'executor prima del seal; creata una vista bind RO pristine sul pathname; il pathname è rimasto SHA-256 `b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044`, mentre una scrittura lower tramite il FD preaperto ha cambiato il contenuto visto da `/proc/1/fd/8` a `e4454552e86ff5254dcd196b3d4a0a0b3731efe99f56544f89c8023e8dbf68a0`.
- Controllo causale: `systemd-tmpfiles-clean.service` pristine partiva con rc 0 prima della mutazione; dopo la sola mutazione dell'inode del FD PID1, con pathname Stage-M ancora pristine, `systemctl start` ha restituito rc 1 e il processo ha terminato `status=2/INVALIDARGUMENT`, coerente con il payload statico sostituito consumato come executor.
- Ne consegue che attestare package/SHA del FD subito prima del comando non chiude il gap: un writer lower preaperto può mutare l'esatto oggetto che PID1 userà dopo VERIFY. Le proiezioni Stage-M proteggono loader, RUNPATH, PT_INTERP, cache/preload e librerie, ma non l'executor preaperto stesso.

### Autorità violata e impatto

- Violato il contratto fondamentale **nessun VERIFY → mutable USE gap** nella catena `PID1 → systemd-executor`.
- L'executor è la prima identità del graph manager; se è mutabile dopo attestazione, stato durevole, witness dei mount, sette slot e target handshake non possono rendere trusted l'esecuzione precedente al target.
- Il finding è architetturale e precede l'integrazione production; non è correggibile aggiungendo un'altra transizione di stato o un digest più tardo.

### Fallback e scope

- Nessun fallback conservativo in-scope è stato dimostrato per il **narrow manager fence** scelto. Chiudere richiederebbe almeno una primitive che faccia riacquisire a PID1 un executor sealed (con protocollo manager reexec/reopen e recovery verificato) oppure immutabilità dell'inode host/superblock. Entrambe riaprono una decisione architetturale esplicitamente vietata dal timebox; fs-verity/IMA/dm-verity resta fuori baseline.
- Scope/costo: redesign del manager execution boundary e nuove prove crash/recovery/compatibilità systemd, non una normale integrazione di Stage-M. Non inventare tale architettura silenziosamente.

### Verifiche e cleanup

- Due POC mirati; il primo ha provato divergenza pathname/FD e failure, il secondo ha aggiunto baseline positiva e diagnostica causale. Il primo tentativo harness senza `docker exec -i` non ha eseguito lo script e non costituisce evidenza.
- Container/image `pi704-executor-fd-check` rimossi; nessun processo temporaneo noto. Log build temporaneo rimosso.
- `git diff --check -- . ':!CHECKPOINT.md'`: PASS. Full matrix, shard, late-dlopen, worker, Python/docs non eseguiti perché il blocker precede questi gate.
- **Prossimo passo:** decisione esplicita del progetto sul blocker/timebox. Non proseguire con integrazione, nuova architettura, commit o test finali finché non autorizzato.
- File minimi alla ripresa: `AGENTS.md`, `CHECKPOINT.md`; per riprodurre la causa bastano la sezione corrente e l'identità `/proc/1/fd/* -> /usr/lib/systemd/systemd-executor`.

---

## Executor inode read-lease POC — PASS

- **Data/ora:** 2026-08-25T12:23:45+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 invariata `OPEN`/`DRAFT`; gate `0/2`; nessun commit, push, staging o aggiornamento PR.
- **Decisione:** **EXECUTOR INODE LEASE POC PASS — READY FOR STAGE-M INTEGRATION**. È soltanto la decisione prerequisite: nessuna integrazione production, nessuno shard A–F. R1-HIGH-01A/B restano **OPEN**; R1-HIGH-02/R1-HIGH-03 restano **CLOSED / non regrediti** sulla precedente evidenza.
- Il prototipo locale #704 è stato preservato integralmente. L’harness lease era esterno al worktree; il solo file repository aggiornato è questo checkpoint, che resta **UNSTAGED**.

### Autorità PID1 e ambiente exact

- Ubuntu 24.04, `systemd=255.4-1ubuntu8.17`; executor `/usr/lib/systemd/systemd-executor`; PT_INTERP `/lib64/ld-linux-x86-64.so.2`; SHA-256 exact `b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044`.
- Discovery dinamica su tutti i `/proc/1/fd/*`: un solo candidato unambiguous; in questo boot era FD `8`, link locator `/usr/lib/systemd/systemd-executor`, regular `0755 root:root`, size `137792`, device `0:87` (`st_dev=87`, `0x57`), inode `95402`. Open autorevole di `/proc/1/fd/8`, `fstat`, SHA e pathname package hanno coinciso al setup. Il numero 8 non è assunto stabile.
- Lo stesso exact FD/dev/inode e SHA è rimasto coerente attraverso due service start. Pathname e PID1 FD finali sono tornati exact reviewed.
- Filesystem executor: Docker `overlay`; Docker backing filesystem `extfs`. Test distinto su named volume reale `ext4` (`/dev/sde[...]`) ha confermato `F_RDLCK`, break, `O_NONBLOCK -> EAGAIN` e mmap writable con FD chiuso `-> lease EAGAIN`. Nessuna inferenza ext4 basata sul solo overlay.
- `/proc/sys/fs/lease-break-time=45 s`; deadline monotonic protetta `10 s`; margine conservativo `35 s`. Sysctl non modificato.

### Lease, capability e fail-closed

- `fcntl(F_SETLEASE, F_RDLCK)` sull’FD aperto dall’exact `/proc/1/fd/N`: **SUCCESS**; `F_GETLEASE=0/F_RDLCK` dopo acquire, prima spawn, durante use, dopo handshake e prima release. Hash eseguito attraverso l’FD leased, mai autorizzato dal pathname.
- Ogni errore acquire, stato diverso da `F_RDLCK`, candidato zero/multiplo, hash diverso, identity drift, break signal/pending state o deadline scaduta abortisce il POC. Nessun daemon-reexec, fs-verity, IMA o dm-verity necessario.
- Ambiente privilegiato integration: `CapEff=CapBnd=000001ffffffffff`, `CAP_LEASE` presente. Root Noble normale ha `CAP_LEASE`; la `logrotate.service` root corrente lo conserva nel bounding set e non usa `NoNewPrivileges`.
- Prova separata: root proprietario dell’inode ha acquisito la lease anche dopo `capsh --drop=cap_lease` (`CapEff=000001ffefffffff`), mentre `nobody` non proprietario ha ottenuto `EACCES`. Quindi il contratto corrente root + inode `root:root` non richiede broadening; `CAP_LEASE` diventa requisito esplicito se l’invoker non è owner. La unit applicativa non invoca questo boundary. Qualunque futura bounding/ownership incompatibile deve fallire chiuso, non essere ampliata implicitamente.

### Exploit precedente e writer preaperti

- Baseline service pristine rc `0`. Prima della lease: bind pathname pristine RO, mutazione dell’inode A tramite FD autorevole, chiusura writer, PID1 FD SHA cambiato a `0df54120dfc8aab59bc0c4da5069d6aed39868830d22b8891f60ab2e3e4328e5`, pathname rimasto reviewed, service rc `1`; restore exact riuscito. Prova quindi i byte alterati, non il solo `ETXTBSY` da writer aperto.
- Pre-open `O_WRONLY`: lease `EAGAIN`. Con protezione non dichiarata, `pwrite`, `write` e `ftruncate` indipendenti hanno mutato realmente A (SHA rispettivamente `0df541...` e `17f8e5...`) e ogni volta restore exact.
- Pre-open `O_RDWR`: lease `EAGAIN`. Dopo chiusura di ciascun writer, fresh acquire ha avuto successo e il fresh FD hash era exact reviewed.
- Mmap A (`O_RDWR` + `MAP_SHARED|PROT_WRITE`, FD conservato): lease `EAGAIN`; mapping capace di mutare, poi restore.
- Mmap B (stessa mapping, FD originale chiuso): lease ancora `EAGAIN`; mapping capace di mutare, poi restore. Quindi nessuna writable shared capability preesistente coesiste con uno stato dichiarato protetto, su overlay o ext4.

### Writer dopo lease, break e `F_GETLEASE`

- Independent root `O_WRONLY`, `O_RDWR`, `truncate` e creazione mmap C sono rimasti bloccati durante la lease; per almeno `0.25 s` nessun syscall ha completato e SHA è rimasto reviewed. Hanno potuto aprire/mutare soltanto dopo l’esplicito release di quel test, poi restore exact.
- `O_WRONLY|O_NONBLOCK` ha fallito immediatamente `EAGAIN`, zero mutazione. La nuova mmap non è stata creabile prima del release perché il necessario `O_RDWR` era bloccato.
- Ogni breaker ha generato notifica (`SIGIO=29` nei reacquire overlay; realtime configurato `38` nell’ext4 e nel rename direct test), con timestamp monotonic e leased FD noto. Su pending break `F_GETLEASE` è passato immediatamente a `2/F_UNLCK`: il POC tratta segnale **o** questo stato come authority invalid, non continua verso un target e rilascia soltanto nel percorso abort del test. Nessun forced break atteso entro la deadline; il budget 10 s resta 35 s sotto il break-time.

### Rename/path replacement

- Sotto lease su A: rename pathname away, regular inode B, restore, symlink B e scrittura di B non hanno cambiato il PID1 FD SHA. Il pathname finale ha ripreso inode A e SHA reviewed.
- Test direct sul nome away che identificava ancora exact dev/inode A: independent `O_WRONLY|O_NONBLOCK` ha ottenuto `EAGAIN`, signal `38`, `F_GETLEASE=F_UNLCK` pending e zero mutation; pathname ripristinato exact. Quindi i trick di path non aggirano l’autorità inode.

### Systemd use, S0/S1 e performance

- S0/S1 privati preesistenti costruiti e sigillati in `2.877968 s`; Stage-M ha proiettato RO la multiarch S0, `/usr/lib64` S0 e `/etc` snapshot (mount witness exact) in `0.000486 s` sotto lease. Snapshot `/etc` pre-costruita in `0.112558 s` prima dell’intervallo; nessun await/unprotected gap tra leased hash/coherence, Stage-M e start.
- Primo slot `Type=simple`: protected interval acquire→mapping handshake→release `1.272422 s`; target private nginx attivo, HTTP `404` valido come liveness, 9 PID e 11 mapping executable tutti presenti nei manifest S0/S1 e SHA-verificati via `/proc/<pid>/root` (nginx, loader, libc, libssl, libcrypto, due moduli inclusi).
- Dopo stop, secondo **fresh acquire/release** sullo stesso PID1 FD: `1.345978 s`, HTTP `200`, 9 PID, stessi 11 mapping reviewed. Entrambi gli start hanno conservato `F_GETLEASE=F_RDLCK`, executor SHA exact e dev/inode coherence fino al positive target-map handshake; nessun break pending.
- Due correzioni harness non-security da non ripetere: il vecchio N2 `Type=forking` non produceva il PID-file POC; il locator `comm=nginx` non riconosce l’invocazione loader-explicit con `comm=ld-linux-x86-64`. Lo slot finale usa cgroup systemd come autorità e mapping SHA. Un `404` dal default site è liveness nginx valida, non failure del boundary.

### Verifiche, cleanup e prossimo passo

- Matrice targeted: **PASS** su tutti i 15 success criteria richiesti. `git diff --check -- . ':!CHECKPOINT.md'`: PASS. Full suite, shard A–F e integrazione production: intenzionalmente non eseguiti/non avviati.
- Container, image, volume, harness e log temporanei del POC rimossi al cleanup finale; nessun processo/watch/server temporaneo previsto.
- **Prossimo passo:** nuova sessione distinta per integrare la lease dell’exact PID1 executor inode nella transaction/recovery authority Stage-M esistente, con deadline/break-abort e reacquire per slot. Prima dell’integrazione leggere `AGENTS.md`, questa sezione e le due sezioni Stage-M precedenti; poi `scripts/pilot_private_runtime_poc.go`, `scripts/pilot_trusted_activation_fence.py` e `scripts/pilot_static_bootstrap.go`. R1-HIGH-01A/B non si chiudono finché integrazione, late-dlopen/worker e shard aggregator non passano.

---

## Executor lease production transaction — milestone parziale

- **Data/ora:** 2026-08-25T13:14:31+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 non modificata, resta `OPEN`/`DRAFT`; gate `0/2`; nessun commit, push, staging o PR update.
- **Stato:** **PARZIALE, COERENTE E VERIFICATO**. La lease è integrata nel vero `trusted-systemd-execution`/TrustedActivationFence e nel lifecycle production corrente. L’architettura finale congelata non è ancora completa: S0/S1 privati restano nel POC locale e il production bootstrap/base fence conserva ancora la snapshot globale ampia precedente. Non dichiarare chiusi R1-HIGH-01A/B e non avviare shard/final suite.

### Implementazione production lease

- `ExecutorInodeReadLease` vive in `scripts/pilot_trusted_activation_fence.py`; holder unico è l’activator Python trusted, senza daemon aggiuntivo. Il FD è `O_CLOEXEC`, resta aperto/leased fino al terminal boundary e la morte processo lo rilascia nel kernel.
- Discovery dinamica bounded di `/proc/1/fd/*`, relazione exact `/usr/lib/systemd/systemd-executor`, regular file, dev/inode/size e SHA statico `b8424efa6f861031c04310fd7bfe485330bb74f53edae341803ffe3f487fd044`; alias FD dello stesso oggetto sono collassati, oggetti incompatibili falliscono, una rotazione durante discovery consente un solo restart e poi fail-closed.
- L’exact `/proc/1/fd/N` viene aperto read-only; discovery fstat/hash è solo locator. L’autorità deriva da `F_SETLEASE(F_RDLCK)`, `F_GETLEASE`, hash via `pread` del leased FD, reviewed SHA e fresh re-attestation PID1 dev/inode. `EAGAIN` da writer/mmap preesistente è errore esplicito, senza fallback pathname.
- Notifica break tramite realtime signal (`SIGRTMIN+4` su Linux), owner/signal FD configurati e ripristinati. `break_requested` o `F_GETLEASE != F_RDLCK` vietano ogni nuovo uso; un break pending in-flight mantiene fisicamente FD/lease fino a handshake o safe abort.
- Deadline monotonic unica `10.0 s`, iniziata prima di lease e Stage-M. Ogni launch execution-bearing riserva due secondi per handshake/abort; il timeout systemctl usa il budget residuo e non resetta il clock.
- `trusted-systemd-execution` persiste soltanto path/dev/inode/size/SHA/locator osservati nel proprio state+manifest immutabile. Non esiste e non è accettato alcun `lease_active`, break flag o lease metadata come recovery authority. Recovery stale continua a derivare cleanup da token/mount ID/device/source/target/RO/options/manifest kernel; un nuovo execution fence crea sempre una fresh lease.
- `_systemctl_result()` richiede pre-use authorization e post-use physical check per daemon-reload/start/stop/reload/restart e altre action execution-bearing. Start conserva la lease fino a effective seven-slot contract, cgroup e runtime map proof; reload e stop usano transaction/lease fresche.
- Failure/timeout in-flight non lancia un altro executor: il path minimo usa soltanto cgroup-v2 `cgroup.kill`, prova zero processi/listener e marca un safe abort terminale. `daemon-reload` non viene falsamente riconciliato tramite target kill.
- Crash seams aggiunte: dopo discovery, leased FD open, `F_SETLEASE` e hash; le seam Stage-M esistenti restano disponibili. La crash/attack matrix privilegiata non è ancora stata eseguita in questa milestone.

### Verifiche

- `tests/test_pilot_deployment.py` completo, Python 3.12 Windows: **PASS** con skip platform previsti. Nuovi contratti: durable observation-only, reviewed SHA fail-closed, break pending in-flight vs nuovo uso, pre/post systemd checks, lease-before-Stage-M ordering.
- `py_compile` mirato (`pilot_trusted_activation_fence.py`, activation, integration, test): **PASS**.
- Bash syntax runner: **PASS**.
- `git diff --check -- . ':!CHECKPOINT.md'`: **PASS**.
- Gate Ubuntu 24.04/systemd 255 mirato con vero entrypoint/toolchain installato: **PASS**. Include static preload zero marker, exact v3 zero marker, bootstrap crash representative, production boot graph, fresh Stage-M+lease start, cgroup/map handshake, fresh reload, fresh stop e cleanup. Executor osservato `dev=87`, `inode=95402`, SHA reviewed exact. Il conteggio FD non è hard-coded.
- Due failure harness risolti da non interpretare come security finding: il pristine nginx package ascolta solo 80 e non soddisfa la topologia candidate 80+443, quindi il gate usa l’esatto requisito richiesto cgroup+mapping; il primo cleanup non marcava il safe boundary del proprio daemon-reload, ora corretto. Run finale: `PASS: gate mirato production executor inode lease + Stage-M`.
- Container/image/processi temporanei e log locale del run finale: rimossi.

### Residuo e prossimo passo

1. Promuovere S0/S1 privati dal POC nell’autorità production ed eliminare il broad global Stage-0/Stage-1 baseline, senza cambiare l’architettura congelata.
2. Eseguire il targeted integrated gate completo: pre-open writer/mmap, post-lease writer/mmap, break before/in-flight/pre-handoff/post-handoff, preload/libcrypto/libsystemd v2-v4, PID1 FD movement, crash lease/Stage-M, handshake/reload/stop.
3. Solo dopo: late dlopen, worker respawn/USR1/future reload-stop, R1-HIGH-02/03, shard A-F, aggregator e full checks.
4. Aggiornare documentazione canonica soltanto dopo i gate; nessun commit/push/PR prima della candidate freeze.

- **File minimi alla ripresa:** `AGENTS.md`, questa sezione checkpoint, `scripts/pilot_trusted_activation_fence.py` (ExecutorInodeReadLease e SnapshotMountFence), `scripts/pilot_ubuntu_activation.py` (`_trusted_execution_fence`, `_systemctl_result`, abort), `scripts/pilot_private_runtime_poc.go`, `scripts/pilot_static_bootstrap.go`; integration helper solo quando si prepara il gate.
- **Comando mirato già verde:** `GITHUB_RUN_ID=lease-cleanup bash scripts/run_pilot_ubuntu_integration_container.sh --executor-lease-gate-only` (non rieseguirlo salvo modifica successiva pertinente).

---

## Private S0/S1 production integration — BLOCKED allo start handoff

- **Data/ora:** 2026-08-25T16:38:45+02:00.
- **HEAD remoto/locale:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; PR #720 resta `OPEN`/`DRAFT`; gate `0/2`; nessun commit, push, staging o PR update. Tutto il prototipo precedente è preservato e `CHECKPOINT.md` resta UNSTAGED.
- **Stato milestone:** **BLOCKED — PRIVATE RUNTIME PRODUCTION INTEGRATION FAILED**. R1-HIGH-01A/B restano OPEN. R1-HIGH-02/03, R1-LOW-01 e H-01..H-05 non sono dichiarati regrediti, ma il lifecycle completo non ha raggiunto mapping/reload/stop e quindi non fornisce nuova evidenza finale.

### Implementazione parziale

- Nuovo `scripts/pilot_private_runtime.go`: broker production CGO-free/statico derivato dal POC senza modificarne il file originale. Build S0/S1 one-pass+SHA con policy statiche, source tmpfs transaction-unique, manifest sealed, overlay RO `S1:S0` senza upper, zero overlap S0→S1, broker copied/sealed, root/mount ID/device/options manifest-bound, target `unshare`+`pivot_root`+explicit loader prima di nginx. Docker build strutturale: PASS, tre binari statici, zero PT_INTERP e zero dynamic section/deps.
- Lifetime deciso **B — intera vita del servizio**: S0/S1/merged restano vivi e immutabili per reload, late load e futuri worker; fresh operation riattesta state+manifest+mount witness. Teardown è ammesso solo a cgroup nginx vuoto, usa mount ID exact e preserva/fail-closed su mount ABA/foreign. Il drop-in è regular input attestato di Stage-M, non un tmpfs annidato: la prima variante nested non attraversava il bind non-recursive `/run/systemd/system` ed è stata corretta.
- `scripts/pilot_ubuntu_activation.py`: pin esterno separato del broker, parser state/manifest/mount, private unit contract per tutti gli Exec slot, mapping authority S0/S1, prepare prima di Stage-M, fresh reload/stop scaffolding e teardown post-stop. `scripts/pilot_ubuntu_integration.py` e runner hanno il gate dedicato `--private-runtime-gate-only` con build crash seams, write attacks, host mutation, preload/hwcaps, Python late import, handoff crash, lease break, reload/stop/teardown intent.
- Recovery build mirata **PASS** per `s0_during_construction`, `s0_after_seal`, `s1_during_construction`, `s1_after_seal`, `merged_after_creation`: next execution ha rimosso solo source/mount transaction-unique exact. RO S0/S1/merged e Python late import sono arrivati al gate prima del blocker; il report finale non è stato emesso, quindi non promuoverli a PASS milestone.
- Correzione lease non architetturale: `_pid1_executor_locator_observations()` ignora soltanto FD PID1 non-candidate scomparsi tra `readdir/readlink`; l’assenza dell’executor resta rilevata dal candidate-set. Contratto unitario aggiunto e suite verde.

### Blocker riproducibile e tentativi da non ripetere

- `GITHUB_RUN_ID=private-runtime-targeted{2,3} bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-gate-only` raggiunge S0/S1/merged seal e tutte le build crash recovery, poi `systemctl start nginx.service` non ritorna al caller entro il boundary; l’eccezione viene seguita dal safe-abort, che non prova zero processi/listener entro 2 s: `Safe abort executor non ha raggiunto cgroup/process/listener terminale`.
- Due cicli consecutivi hanno prodotto lo stesso blocker. Il terzo aveva ridotto il pre-safe-boundary al solo MainPID/cgroup/maps, senza progresso. **Non ripetere il gate identico.** Prima serve un diagnostic read-only/purpose-built che preservi l’errore originario prima che safe-abort lo mascheri e raccolga solo: rc/timeout systemctl, unit `ActiveState/SubState/MainPID/Result`, PID file host/runtime, cgroup.procs, processi/listener e journal ultime righe. Determinare se il target è attivo ma Type=forking/PIDFile non completa, se il broker resta alla barrier, o se ExecStart fallisce.
- Il primo gate production ha trovato e corretto due errori distinti già risolti: `loadS0` usava source non tokenizzata; self digest usava `O_NOFOLLOW` su `/proc/self/exe`. Un diagnostic separato ha provato prepare e autorità dentro Stage-M PASS dopo la correzione manager-drop.
- Nessun test positivo per post-seal host nginx/libcrypto/libssl/libc/module, preload/hwcaps target, lease-break handoff, mapping/HTTP, fresh reload/stop o teardown crash può essere dichiarato: erano nello stesso gate interrotto prima della prova positiva.

### Verifiche e stato finale

- `py -3.12 -m pytest -q tests/test_pilot_deployment.py -x`: **PASS** con skip platform previsti.
- `py -3.12 -m py_compile` activation/fence/integration/test: **PASS**.
- Docker Go build/gofmt/static ELF checks: **PASS**.
- `bash -n scripts/run_pilot_ubuntu_integration_container.sh`: **PASS**.
- `git diff --check -- . ':!CHECKPOINT.md'`: **PASS**.
- Full shard A–F, full matrices, late-dlopen/worker aggregator: non eseguiti come richiesto. S0/S1 metriche finali non acquisite dal report a causa del blocker; non usare i reference POC come misura production.
- Container/processi e log temporanei creati in questa sessione: rimossi. I log `.pi-*` preesistenti del prototipo sono stati preservati. Rimossa anche l’image buildcheck `pi704-private-runtime-buildcheck`; nessun container/image temporaneo noto.

### Prossimo passo

1. Nuova sessione: leggere `AGENTS.md`, questa sezione e la milestone lease precedente; poi soltanto `scripts/pilot_private_runtime.go` (`productionDropin`, `productionPrivateExec`), `scripts/pilot_ubuntu_activation.py` (`_systemctl_result`, safe-abort, private unit contract) e `_test_private_runtime_production_vertical_slice` nell’integration helper.
2. Costruire un diagnostic singolo che non ripeta il gate e renda osservabile la causa originaria start/PIDFile/barrier; correggere soltanto dopo evidenza.
3. Rieseguire prima un core start/maps/HTTP senza attacchi, poi il gate private mirato completo. Solo su PASS acquisire metriche, fresh reload/stop e crash finali; R1-HIGH-01A/B restano OPEN comunque.

## Private runtime start diagnostic

- **Data/ora e stato:** 2026-08-25T17:54:17+02:00; diagnosi **COMPLETATA** sullo stesso HEAD `598f1905462b5df0cb5f009ea79cffb7901545b8`. PR #720 resta `OPEN`/`DRAFT`, gate `0/2`, nessun commit/push/staging/PR update. `CHECKPOINT.md` resta UNSTAGED. Harness temporaneo in `scripts/pilot_ubuntu_integration.py` e flag runner `--private-runtime-start-diagnostic-only`; log ignorati `.pi-private-runtime-start-diagnostic{,-rerun}.log` preservati.
- **Clock esatto:** `systemctl` non ha emesso un proprio timeout e il job systemd aveva `TimeoutStartUSec=1min 30s`, `JobTimeoutUSec=infinity`. È scaduto il timeout esterno Python di `_systemctl_result`: **1.9719752160017379 s**, calcolato da `lease.deadline_remaining - 2 s`; argv esatto `['/usr/bin/systemctl','start','nginx.service']`, start `380636.284`, fine `380638.264`, rc assente, stdout/stderr vuoti. Owner: **LEASE DEADLINE** (clock C), non systemd/broker/harness. La lease decennale sarebbe scaduta a `380640.258910`.
- **Timeline monotonic:** T0 transaction `380610.973339`; T1 S0 sealed `380629.566369`; T2 S1 sealed non campionato nel brevissimo state intermedio ma positivamente bounded `>380629.566369` e `<=380629.854019` dal successivo `merged-sealed`; T3 merged ready `380629.854019`; T4 lease acquired `380630.258910`; T5 Stage-M sealed `380634.657573`; T6 start `380636.283999`; T7 executor non campionato prima del suo exec (systemd ne prova l'esecuzione con ControlPID/Exec records); T8 first broker/precheck `380636.446992`, target broker `380636.937393`; T9 nginx master/children `380637.478090`; T10 target executable mapping evidence `380637.391489` (non accettata come private safe boundary); T11 outer lease-derived timeout `380638.264496`; T12 safe-abort `380638.465513`; T13 safe-abort termina in errore `380640.493836`, teardown reale solo col container effimero.
- **Systemd transitions:** `inactive/dead` → `activating/start-pre` (`ControlPID=798`) → `activating/start` (`ControlPID=811`) → `activating/start` (`ControlPID=0`, `MainPID=0`, job 94 ancora running). `Result=success`; ExecStartPre PID 798 `code=exited,status=0`; ExecStart PID 811 `code=exited,status=0`; `ExecMainStatus=0`, `ActiveEnterTimestampMonotonic=0`. Il client attendeva quindi la readiness `Type=forking`/PIDFile dopo che ExecStart era già uscito con successo.
- **Ultimo journal event prima cleanup:** `[380637.425571] systemd[1]: nginx.service: Can't open PID file /run/thebitlab/pilot-private-runtime/runtime/run/nginx.pid (yet?) after start: No such file or directory`.
- **Process tree al failure snapshot `380638.455871`:** PID1 systemd PID 1; nessun systemd-executor o broker ancora vivo; nginx master PID 824, PPID 1, stato S; worker PID 825,826,827,828,829,830,832,833, PPID 824, tutti nel cgroup canonico `/system.slice/nginx.service`. È nginx già daemonizzato ciò che resta vivo mentre systemctl attende.
- **Broker lifecycle:** systemd ha eseguito il broker; `validateProductionRuntime()` è necessariamente passato prima dei due exec nginx; precheck PID 798 e start PID 811 hanno raggiunto mapping nginx e sono usciti `status=0`. Il broker non attende e non resta vivo: viene sostituito da nginx; nginx parent daemonizza, esce 0 e lascia master/workers. La private root **non persiste fino al target exec**.
- **Nginx lifecycle/PIDFile:** nginx è realmente partito. Configurato `PIDFile=/run/thebitlab/pilot-private-runtime/runtime/run/nginx.pid`: assente da PID1. Positivo dentro la root effettiva nginx: `/proc/824/root/run/nginx.pid`, bytes `824\n`, dev 100/inode 201; PID 824 esiste ed è nel cgroup canonico. Poiché root e mount namespace nginx coincidono con PID1, il file è il manager `/run/nginx.pid`, non il backing path private configurato. **PIDFile causal: YES**; il vecchio difetto POC non è in causa.
- **Namespace/mount:** PID1, broker osservato e nginx master/workers riportano tutti `mnt:[4026532474]`, root `/`; executor troppo transiente per essere campionato. Manager witness al failure: S0 mount 407 dev `0:92` tmpfs RO; S1 mount 408 dev `0:94` tmpfs RO; merged mount 411 dev `0:102` overlay RO `S1:S0`; manager `/run` mount 472 dev `0:100`. I mount S0/S1/merged restano vivi, ma nginx vede la mount tree manager e non il bind/pivot private previsto.
- **Lease/deadline:** executor FD dev/inode `87:95402`, `F_GETLEASE=F_RDLCK`, `break_requested=false` a acquire/start/T11. Remaining: Stage-M 5.601685 s; start 3.974943 s; outer timeout 1.994501 s; safe-abort 1.793409 s; poi 0 a T13. Lease valida, non rotta; il reserve command scatta mentre systemd attende una readiness impossibile. Il coupling anticipa il sintomo ma non è la causa primaria.
- **Safe handoff:** mapping nginx osservato, ma **safe executable handoff private S0/S1 = NO**: namespace/root/device non sono quelli sealed-private, quindi l'authority non può accettare T10. Di conseguenza non classificare questo caso come readiness che continua dopo un safe private handoff; è un handoff mount-namespace fallito seguito da readiness PIDFile impossibile.
- **Causa primaria:** **C — PRIVATE ROOT VISIBILITY**. `privateExec()` in `scripts/pilot_private_runtime.go` esegue `unshare(CLONE_NEWNS)`, bind, `pivot_root` e `syscall.Exec` da una goroutine Go senza `runtime.LockOSThread()`. Il mount namespace è per-thread: la goroutine può migrare su un thread nel namespace manager prima dell'exec. Evidenza congiunta: codice senza lock, nginx/PID1 nello stesso namespace, nginx vivo, PID file nel `/run` effettivo ma assente nel path backing configurato. Systemd non può acquisire MainPID e mantiene il job `activating/start`.
- **Minimal reproducer:** precondizioni: container Ubuntu 24.04 systemd effimero/pristine e prototipo corrente; unico comando `GITHUB_RUN_ID=private-runtime-start-diagnostic-rerun bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-start-diagnostic-only`. Transizione osservabile: ExecStart status 0 + master PID 824 nel cgroup, quindi journal PIDFile ENOENT e job 94 bloccato fino all'outer lease-derived timeout. Reproducer diagnostico **PASS**, original failure **YES**.
- **Correzione minima raccomandata (prossima sessione, non implementata):** bloccare la goroutine sul suo OS thread (`runtime.LockOSThread()`) **prima** di `Unshare` e mantenerla locked senza ritorno fino a `syscall.Exec`; fail-closed su ogni errore. Poi verificare nello stesso core start che nginx abbia namespace diverso da PID1, root/mount sealed, che `/proc/<main>/root/run/nginx.pid` e il backing PIDFile manager-visible siano lo stesso inode, e che systemd raggiunga `active/running` senza aumentare deadline né cambiare argv/mode systemctl. Nessun cambio architetturale richiesto.
- **Verifiche:** reproducer diagnostico corretto: PASS dopo una correzione harness-only (`path` JSON collision; primo collector non aveva snapshot). `py -3.12 -m pytest -q tests/test_pilot_deployment.py -x`: PASS con skip previsti (il primo tentativo con Python 3.10 falliva solo collection su `typing.Self`, non ripeterlo). `py -3.12 -m py_compile` integration+activation: PASS. `bash -n scripts/run_pilot_ubuntu_integration_container.sh`: PASS. `git diff --check -- . ':!CHECKPOINT.md'`: PASS. Full gate/matrices/shards A–F/aggregator non eseguiti. Nessun container/image temporaneo residuo.
- **Security state:** nessun nuovo finding separato assegnato. R1-HIGH-01A/B restano OPEN; R1-HIGH-02/03, R1-LOW-01 e H-01..H-05 restano CLOSED senza nuova prova di regressione. Il private runtime gate resta `0/2`.
- **Prossimo passo:** nuova sessione AUTHOR/FIX: leggere `AGENTS.md` e questa sola sezione; modificare esclusivamente il thread-affinity handoff in `scripts/pilot_private_runtime.go`, aggiungere l'asserzione namespace/PIDFile nel reproducer core, eseguire prima lo stesso diagnostic start una volta. Non aumentare la lease e non avviare ancora full gate/matrici finché il core start non è `active/running` con private root positiva.

## Private runtime thread-affinity correction

- **Data/ora, stato e Git:** 2026-08-25T19:14:01+02:00; **CORE START FIXED** sul branch `fix/oauth-log-redaction-704`, remote/working HEAD invariato `598f1905462b5df0cb5f009ea79cffb7901545b8`. Nessun add/commit/push/PR update; PR #720 resta `OPEN`/`DRAFT`, gate `0/2`; `CHECKPOINT.md` resta UNSTAGED. File di questa correzione: `scripts/pilot_private_runtime.go`, diagnostic in `scripts/pilot_ubuntu_integration.py`, test stretti in `tests/test_pilot_deployment.py`, questo checkpoint.
- **Correzione:** `privateExec()` ora chiama `runtime.LockOSThread()` immediatamente prima della prima mutazione thread-specific (`Unshare(CLONE_NEWNS)`) e mantiene lo stesso thread attraverso propagation private, bind, pivot root, root/namespace proof, preparazione loader e `syscall.Exec`. Nessun goroutine/channel handoff nella regione. `UnlockOSThread()` esiste solo nel ramo in cui `Unshare` fallisce e quindi il namespace non è mutato.
- **Failure path scelto:** modello B fail-closed, coerente col helper monouso. Dopo `Unshare` riuscito ogni errore ritorna direttamente a `main`, che termina il processo con `os.Exit(2)` senza unlock; il successo sostituisce l'immagine con `Exec`. Seam `private_exec_after_unshare`: PID 765, TID 771 prima/dopo, namespace `mnt:[4026532474]` → `mnt:[4026532479]`, rc 97; `/proc/765` e task directory assenti dopo wait, thread **non** restituito allo scheduler, nessun namespace/helper residuo.
- **TID/namespace proof start:** precheck broker PID 804/TID 811 e start broker PID 818/TID 821. In entrambi lo stesso TID è registrato a `before-unshare`, `after-unshare`, `after-root`, `before-exec`; namespace `mnt:[4026532474]` → `mnt:[4026532479]` e resta `mnt:[4026532479]` fino a Exec. PID1 `mnt:[4026532474]`; nginx master/workers `mnt:[4026532479]`: divergence **PASS**.
- **Root/mappings/cgroup:** nginx master PID 828, worker 829,830,831,832,833,834,836,837; tutti in `/system.slice/nginx.service` e nello stesso namespace private. Root `/proc/828/root` dev/inode `102:2`, identico al merged sealed `102:2`; mount `/` overlay dev `0:102`, RO, lowerdir esatto `S1:S0`, nessun upper. `/proc/828/exe` è il loader esplicito `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`; mapping iniziali attestati includono nginx, loader, libc, libssl, libcrypto e i due moduli dalla private authority. S0→S1 duplicate bytes resta 0.
- **PIDFile/systemd:** private `/proc/828/root/run/nginx.pid` e manager `/run/thebitlab/pilot-private-runtime/runtime/run/nginx.pid` contengono entrambi `828\n`, dev/inode `100:210`, mode 0644, uid/gid 0:0, timestamp identico: backing object **PASS**. `systemctl start nginx.service` blocking rc 0; `ActiveState=active`, `SubState=running`, `MainPID=828`, job completato e PIDFile riconosciuto.
- **Lease/safe handoff:** lease executor dev/inode `87:95402`, acquired `385673.453210`, deadline invariata `385683.453210`; Stage-M event `385675.213664`; systemctl invoke `385676.118320`, target executable mapping private stabilito `385676.508036`, systemctl completion `385676.514255`; proof completo safe handoff osservato `385677.212287`, marked `385677.213167`, remaining 6.240040 s, `break_requested=false`; lease rilasciata soltanto dopo boundary a `385677.724281`, pending false. Stage-M ed executor lease **PRESERVED**; deadline non è scattata.
- **Diagnostic:** comando canonico `GITHUB_RUN_ID=private-runtime-start-diagnostic-thread-affinity bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-start-diagnostic-only`: terzo run **PASS**. Primo run aveva già start `active/running` ma una assertion harness era mascherata dal secondary safe-abort; secondo ha isolato l'incompatibilità del detector package-exe `_nginx_processes()` col loader esplicito. Il proof core usa quindi l'esatto `cgroup.procs` + mapping/private authority senza cambiare policy/release production. Non ripetere i due harness failure; log temporanei pi: `pi-bash-a25424f4eb646210.log`, `pi-bash-54c1db76bdf7e527.log`; log verde `pi-bash-141cd630c065ad2f.log`.
- **Verifiche:** Docker builder `gofmt` + `CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build` statico: PASS nel diagnostic verde. Due nuovi test thread-affinity/fail-closed/positive handoff: PASS. `py -3.12 -m pytest -q tests/test_pilot_deployment.py -x`: PASS (skip previsti). `py -3.12 -m py_compile scripts/pilot_ubuntu_integration.py scripts/pilot_ubuntu_activation.py`: PASS. `bash -n scripts/run_pilot_ubuntu_integration_container.sh`: PASS. `git diff --check` mirato: PASS. Runner ha rimosso container e image; nessun processo temporaneo locale.
- **Security/gate state:** nessun cambio architetturale e nessun nuovo finding. Executor lease, Stage-M, runtime lifetime intero servizio, PRIVATE S0, PRIVATE S1 e overlay RO S1:S0 preservati. R1-HIGH-01A/B restano OPEN; R1-HIGH-02/03 restano CLOSED. S0/S1 sono soltanto **CORE START FIXED**, non final PASS; gate resta `0/2`.
- **Resta da fare (nuova sessione):** targeted security matrix: post-seal mutation, preload, hwcaps, late dlopen, worker respawn, fresh reload/stop, crash/lease-break, shard A–F e aggregator. Prima del matrix allineare soltanto il relativo harness di attribuzione processo al contratto loader+mapping private osservato; non ampliare authority o release criterion. File minimi iniziali: `AGENTS.md`, questa sezione, diagnostic/private mapping helper in `scripts/pilot_ubuntu_integration.py`; ampliare solo ai singoli shard richiesti.

---

## Targeted private-runtime security matrix — E PASS, full aggregator BLOCKED

- **Data/ora:** 2026-08-26T05:32:33+02:00.
- **Git/PR:** branch `fix/oauth-log-redaction-704`; local/upstream/remote HEAD invariati `598f1905462b5df0cb5f009ea79cffb7901545b8`; PR #720 `OPEN`/`DRAFT`; gate `0/2`; nessun add/commit/push/PR update. Tutto il worktree precedente e `CHECKPOINT.md` sono preservati unstaged.
- **Stato unità:** **BLOCKED**. La matrice private-runtime E e shard A/C sono PASS; B e D hanno completato i loro scenari nel run stateful; shard F e aggregator non sono raggiungibili perché la configurazione candidate non è integrata nell'autorità S1. Non creare un candidate verde.

### Thread affinity e runtime oracle

- Tutti i quattro path Go `Unshare(CLONE_NEWNS)` rilevanti sono ora pinned: production `stage0`/`privateExec` e POC `stage0`/`privateExec`. `LockOSThread()` precede immediatamente l'unshare; solo il failure dell'unshare esegue `UnlockOSThread()`; dopo successo ogni errore termina il helper senza unlock e il successo va a `syscall.Exec`. Test statico globale aggiunto.
- Forced post-unshare finale: PID 877/TID 882 stabile; namespace `mnt:[4026532474]` → `mnt:[4026532478]`; rc 97; processo/task directory rimossi; thread restituito allo scheduler **NO**.
- `_nginx_processes()` riconosce il target loader-explicit soltanto tramite cgroup canonico + root merged dev/inode + namespace distinto da PID1 + mapping closure revisionata. Nessuna classificazione per nome/argv.
- Mapping oracle: VMA exact `/proc/<pid>/map_files/<range>` con descriptor/hash stabile; per VMA overlay detached non riapribili, unico fallback ammesso è `/proc/<pid>/root/<lexical>` nella root private RO/namespace-attestata, mai il pathname host. Digest sempre legato al manifest S0/S1. PID1 executor locator accetta il solo exact relationship canonico anche col suffisso kernel ` (deleted)`, mantenendo fstat/SHA/alias/lease invariati; regressione H-05 package rotation PASS.

### Matrice targeted E — PASS

- Comando verde: `GITHUB_RUN_ID=private-runtime-security-matrix-e10 bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-gate-only`; rc 0; log `.pi-private-runtime-security-matrix-e10.log` ignorato.
- **Post-seal mutations:** same-inode su `libcrypto`, `libssl`, `libc`, modulo geoip e `_ssl`; rename-over nginx; delete/recreate modulo stream; symlink substitution `nginx.conf`; replacement same pathname/different inode. Start/respawn/reload o running-process proof hanno mantenuto namespace private, root `102:2`, mapping reviewed S0/S1. Risultato: **PRIVATE AUTHORITY PRESERVED**.
- **Preload/env:** `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `LD_DEBUG`, `LD_PROFILE`, `GLIBC_TUNABLES` forniti al broker; target environment li ha eliminati tutti. `PassEnvironment` vuoto, nessun loader env nella unit/nginx config, marker preload zero. Risultato: **BLOCKED**.
- **HWCAPS:** candidati host `glibc-hwcaps/x86-64-v2/v3/v4/libssl.so.3` creati post-Stage-M; marker zero; mapping effettive libssl/libcrypto/libc dalla private authority. Alternate host directories non sono nel `--library-path` privato. Risultato: **PRIVATE AUTHORITY PRESERVED**.
- **Late dlopen:** sorgente host `_ssl` e librerie mutate dopo S0 seal; processo Python private PID 897 ha caricato `_ssl.cpython-312-x86_64-linux-gnu.so`, libssl e libcrypto dalla root private, namespace `mnt:[4026532478]`; hostile loader env assente. Risultato: **PRIVATE AUTHORITY PRESERVED**.
- **Worker respawn:** master 956; worker 957 terminato; nuovo worker 976; cgroup `/system.slice/nginx.service`, namespace private, root `102:2`, 11 mapping reviewed inclusi nginx/loader/libc/libssl/libcrypto/due moduli. PASS.
- **Fresh reload:** master 956 invariato; old worker `958,959,961,962,963,964,965,976`; nuovi worker `1018–1021`; stessa namespace/root/mapping authority; PIDFile manager `100:273`, contenuto `956\n`. PASS sotto fresh Stage-M/executor lease e source-side library mutations.
- **Fresh stop:** PIDFile presente/equivalente fino al lifecycle; servizio `inactive` rc 3, cgroup vuoto; teardown crash `runtime_teardown` conserva state fail-closed, retry exact rimuove runtime; post-stop daemon-reload su fresh lease; zero runtime root/cgroup residuo. PASS.
- **Crash/lease:** S0/S1/merged five build seams PASS; handoff/before-exec/post-unshare failures fail-closed; executor holder crash after discovery/open/setlease/hash rilascia kernel lease e recovery exact; expired deadline REJECT; actual break request durante handoff osservata, safe boundary prima del release. Stage-M **PRESERVED**; executor lease **PRESERVED**.
- Metriche run: S0 2,413 file / 94,848,451 B, 2,414 identity, wall 1.092 s; S1 20 file / 1,590,642 B, 20 identity, wall 0.032 s; duplicate copy 0; matrix wall 50.244 s.

### Shard esistenti e aggregator

- Definizione canonica recuperata dal checkpoint: A `bootstrap-loader`; B `fence-recovery`; C `systemd-generated`; D `historical-execution`; E `lifecycle+late-dlopen/worker`; F `logging`. Evidence schema/aggregator era soltanto pianificato e non esisteva come runner nel repository; non sono stati inventati significati sostitutivi.
- **Shard A:** `GITHUB_RUN_ID=private-runtime-shard-a ... --bootstrap-adversarial-only` PASS: preload six timings zero constructors; hwcaps v2/v3/v4 + libc/libssl/libcrypto/Python/symlink reject/zero marker; six bootstrap crash seams/recovery; closure `735 expected-absent`, `0 unpinned`.
- **Shard B:** scenari nel full stateful run PASS prima del blocker: forged metadata/foreign tmpfs; base/native/execution/generated crash matrix; executor holder crash matrix; Stage-M/recovery invariants.
- **Shard C:** comando isolato `GITHUB_RUN_ID=private-runtime-shard-c-race-only ... --fence-race-only` rc 0; generated.early/generated/generated.late write/atomic/drop-in/remove + external second reload + executable/unit races PASS; zero `/etc/nginx` mount residuo; questo flag è un'estrazione dello scenario esistente, non una nuova semantica.
- **Shard D:** H-01/H-02 e H-03/H-04/H-05 exact package/root-marker regressions, expected-present/absent, boot inventory 44 service/55 Exec/108 reviewed executables e scheduler zero-unknown hanno PASS nel run stateful prima del blocker.
- **Shard E:** PASS completo come sopra.
- **Shard F:** **NOT RUN / BLOCKED**; la full non raggiunge runtime redaction/logrotate rotation dopo il blocker activation.
- **Aggregator:** **NOT RUN / BLOCKED**; non esiste ancora implementazione canonicale e manca F. Nessun output è stato manualmente reso verde.

### Blocker architetturale

- Full canonica: `GITHUB_RUN_ID=private-runtime-shards-bcdf-mount-witness bash scripts/run_pilot_ubuntu_integration_container.sh` (e run diagnostici precedenti) raggiunge B/C/D, poi `activation.activate(v2_bundle, state)` fallisce deterministicamente in `_finish_transition()` su `_remove_symlink('/etc/nginx/sites-enabled/default')` con `EROFS`.
- Causa: la base `TrustedActivationFence` monta l'intera `/etc/nginx` RO mentre la stessa transaction di activation deve mutarne i symlink. Subito prima, recovery/state e mount witness C sono puliti (`post-race /etc/nginx mount records []`), quindi non è residue del race.
- Vincolo aggiuntivo: `pilot_private_runtime.go` S1 accetta soltanto il digest tree nginx package pristine `026a3986...` (7 directory/13 file/3 link). La topologia candidate v2 modifica `/etc/nginx` e dipende da `/etc/thebitlab/current`; quindi rimuovere semplicemente `/etc/nginx` da `BASE_FENCE_DIRECTORIES` non integra la configurazione candidate nella private authority e riapre verify→use.
- Classificazione: **HIGH blocker — candidate configuration authority incomplete**. Minimo prossimo lavoro: progettare una transaction candidate-config privata/delta S1 che consenta le mutazioni activation su underlying controllato, sigilli e attesti config+symlink closure prima dell'uso, e mantenga il manager/helper boundary; poi rieseguire activation targeted, F e aggregator. Non usare policy permissiva, host fallback o rimozione della fence senza autorità sostitutiva.

### Finding/gate/test/cleanup

- R1-HIGH-01A original claim: shebang Python caricava `/etc/ld.so.preload` prima del fence; reproducer originale constructor root. Mitigazione/static bootstrap e matrix A/E: direct oracle zero marker/Python private. **Resta OPEN** perché full candidate/F/aggregator non completano.
- R1-HIGH-01B original claim: policy non copriva glibc hwcaps alternativi, exact RUNPATH v3 eseguiva constructor root. Mitigazione `735 expected-absent` + private root; direct A/E mappings/marker PASS. **Resta OPEN** per lo stesso blocker finale.
- R1-HIGH-02 e R1-HIGH-03: **CLOSED, non riaperti**; regressioni forged/recovery e generated race PASS. R1-LOW-01/H-01..H-05 restano CLOSED sui test eseguiti.
- Gate resta `0/2`: le due condizioni sono due fresh independent full-diff review round consecutivi senza finding sullo stesso HEAD; author matrix/test non avanzano il gate e ogni commit lo resetterebbe comunque.
- `tests/test_pilot_deployment.py`: **219 total, 184 PASS, 35 expected SKIP, 0 FAIL/ERROR** (Python 3.12, JUnit contato). Regressioni nuove: tutti i Go unshare pinned; PID1 executor deleted relationship; fresh-slot lease renewal solo senza break/pending; input attestors prima del manager use; map oracle private.
- Go `gofmt`/CGO-disabled three static builds, zero PT_INTERP/dynamic section: PASS in Docker A/E. `py_compile` mirato: PASS. Bash syntax runner: PASS. `git diff --check`: PASS. Full integration: BLOCKED come sopra; Python 3.11/full repo/Sphinx/course-plan non eseguiti dopo blocker.
- Cleanup finale: zero container con label integration; zero image integration; zero volume matching; zero processi nginx/helper/broker locali; container effimeri hanno rimosso mount/runtime/processi. Log `.pi-private-runtime-*.log` sono ignorati e non staged. Nessuna risorsa estranea cancellata.
- **Prossimo passo:** nuova sessione architetturale dedicata alla candidate config authority S1; leggere questa sezione, `BASE_FENCE_DIRECTORIES`/`verify_host_preflight`/`_finish_transition` in `scripts/pilot_ubuntu_activation.py`, `s1TreePolicies`/production build in `scripts/pilot_private_runtime.go`, e il contract bundle config. Non rieseguire la full invariata prima di una modifica concreta.

---

## Private S1 candidate configuration authority — PARTIAL PASS

- **Data/ora:** 2026-08-27T17:36:26+02:00.
- **Starting/final Git:** branch `fix/oauth-log-redaction-704`; local/upstream/remote HEAD invariati `598f1905462b5df0cb5f009ea79cffb7901545b8`; worktree intenzionalmente modified/untracked e tutto unstaged, preservato. Nessun commit/push. PR #720 verificata `OPEN`/`DRAFT`, exact HEAD, merge state `CLEAN`; gate indipendente `0/2`.
- **Stato:** **PRIVATE S1 CANDIDATE CONFIGURATION AUTHORITY: PARTIAL PASS**. L'autorità candidate e la matrice mirata sono PASS; full canonica non ha un exit finale, Shard F resta BLOCKED e aggregator non implementabile/eseguibile senza F. R1-HIGH-01A/B restano OPEN; R1-HIGH-02/03 restano CLOSED.

### Root cause, closure e architettura

L'originale `_remove_symlink('/etc/nginx/sites-enabled/default')` falliva `EROFS` perché `trusted-activation-base` esponeva il proprio snapshot RO di `/etc/nginx`. La base fence non è stata rimossa o resa writable. Le sole mutazioni durevoli nginx vengono applicate all'anchor lower con una API chiusa; `_accepted_underlying_manifest()` accetta soltanto stati parziali/finali composti da default pristine/assente e tre exact link candidate, così crash/recovery non autorizzano altri delta.

Closure completa recuperata dall'activation:

| Oggetto | Mutazione candidate | Autorità finale/prova |
|---|---|---|
| `/etc/nginx` package tree | normalizzazione static tree `026a3986...`; default rimosso | S1 tmpfs RO + manifest + mount witness |
| `modules-enabled/90-thebitlab-process-error-log.conf` | exact link current | S1 links manifest |
| `conf.d/thebitlab-log-format.conf` | exact link current | S1 links manifest |
| `sites-enabled/thebitlab.conf` | exact link current | S1 links manifest |
| `/etc/thebitlab/current` | exact link al deployment selezionato | candidate path + lock SHA nello state e manifest S1 |
| bundle v2 | 7 generated file + `deployment.lock.json`, inventario directory chiuso | expected lock SHA preflight + per-file digest lock + stable copy |
| certificato/chiave TLS | copia agli exact path selezionati dal manifest locked | stable FD copy + object SHA/device/size in S1 |
| `/etc/logrotate.d/thebitlab` | exact link current | S1 closure e replica host attestata |
| `/etc/systemd/system/thebitlab.service` | exact link current | S1 closure e replica host attestata |
| private nginx drop-in | exact generated bytes, zero sibling | drop-in SHA nello state S1; boot graph lo accetta solo con authority viva |

S0 resta base code/package revisionata. S1 parte da una copia candidate-normalized del tree package (supporta source host pristine o candidate solo dopo rinormalizzazione e confronto col digest statico), copia closure bundle/TLS, crea gli exact link, poi remounta l'intero tmpfs RO. L'overlay senza upper `lowerdir=S1:S0` è montato RO. `nginx -t/-T` viene eseguito dal broker dentro la root finale privata. La replica host dei link non è authority del runtime; master/reload risolvono `current` e include dentro S1.

**VERIFY → SEAL → USE:** Python preflight verifica renderer/manifest/lock; il broker statico seleziona l'exact candidate+lock, ricontrolla inventario/metadata/digest e copia via FD stabile; S1 e merged vengono sigillati e kernel-witnessed; Python riapre manifest/state e verifica il bundle copiato; `nginx -t/-T` gira nella root privata; soltanto dopo Stage-M/executor lease avvia il broker target. Mutable gap osservato: **nessuno**. External mutation post-seal resta fuori dalla root.

### Matrice candidate e lifecycle mirato

Comando finale verde: `GITHUB_RUN_ID=private-s1-candidate-5 bash scripts/run_pilot_ubuntu_integration_container.sh --private-runtime-gate-only`; seconda variante verde con nginx enabled durante il fresh stop: `GITHUB_RUN_ID=private-s1-enabled-stop ... --private-runtime-gate-only`.

- candidate same-inode site write, process config rename-over, format config delete/recreate, manifest symlink substitution, same-path/different-inode e `/etc/thebitlab/current` replacement: **PRIVATE CANDIDATE AUTHORITY PRESERVED**;
- host nginx.conf substitution e executable/module/library mutations: private authority preserved;
- fresh reload sotto tali mutazioni: master invariato, 8 nuovi worker, private namespace/root e 11 reviewed mapping PASS;
- initial start `active/running`, MainPID/cgroup/PIDFile private PASS; worker respawn, late `_ssl` dlopen, reload, enabled stop, teardown/retry PASS;
- preload/env (`LD_*`, `GLIBC_TUNABLES`) zero target propagation; hwcaps marker zero;
- Stage-M ed executor lease PRESERVED, break reale e expired deadline fail-closed;
- forced post-unshare: PID 884/TID 889 (run candidate-5), rc 97, namespace diverged, task/process gone, scheduler return NO. Tutti i quattro production/POC Unshare path restano pinned; unlock soltanto se Unshare fallisce.
- Metriche candidate-5: S0 2,413 file / 94,889,806 B / 2,414 identity; S1 30 file / 1,602,467 B / 30 identity; duplicate copies 0; matrix 51.993 s.

### Full integration, Shard F e aggregator

La full Ubuntu ha superato l'EROFS originale e ha provato activation candidate, private start, enabled stop e teardown. Finding same-family corretti lungo il percorso: exact private drop-in riconosciuto dal boot inventory e boot-reachable input attestor; reuse della stessa sealed candidate prima dello start; rimozione exact anche della directory drop-in vuota; TOCTOU chmod su `/etc/nginx` classificato PASS quando bloccato dal base RO.

Non esiste tuttavia un full FINAL PASS:

1. `full-1`: private drop-in directory non ancora classificata;
2. `full-2`: `_ensure_private_runtime(None)` rimuoveva erroneamente la candidate matching;
3. `full-3`: boot-reachable package input non riconosceva l'exact drop-in;
4. `full-4`: teardown lasciava la directory drop-in vuota;
5. `full-5`: integrazione tentava ancora chmod della base RO invece di accettare il blocco kernel;
6. `full-6`: prima della candidate, `daemon-reload` ha ricevuto soltanto `0.05 s` residui della lease ed è scaduto; safe abort ha correttamente rifiutato riuso. È variabilità/timing del boundary pre-candidate, non regressione candidate dimostrata. Non aumentare il timeout o indebolire la lease. Non ripetere ancora la full identica in questa sessione.

- Shard A/C e scenari B/D/E: stato storico PASS preservato; candidate matrix E aggiornata PASS.
- **Shard F:** BLOCKED, nessun run canonicale finale di logging/redaction/real logrotate raggiunto.
- **Aggregator:** contratto esiste soltanto nel checkpoint (evidence exact SHA/digest/policy, scenario completeness/uniqueness, cleanup; fail closed su missing/stale/malformed). Nessun runner canonicale repository e F manca; **NOT IMPLEMENTED / NOT RUN**, nessun green sintetico.

### Test/static/cleanup

- `tests/test_pilot_deployment.py`: **219 total = 184 PASS + 35 expected SKIP, 0 FAIL/ERROR** su Python 3.12.
- Candidate private-runtime gate: PASS due volte, inclusi mutation/reload e enabled stop.
- Go static build: tre artifact CGO-disabled statici; zero PT_INTERP e zero dynamic section: PASS.
- `py_compile` activation/fence/integration/test, Bash syntax runner, `git diff --check`: PASS.
- Python 3.11, full repository, Sphinx/course-plan: non rieseguiti perché full canonicale resta bloccata.
- Cleanup: zero container/image/volume integration, zero processo nginx/broker/helper locale, zero mount/runtime noto. Rimossa image buildcheck e artifact diff temporaneo. Log `.pi-private-*` ignorati restano non staged secondo policy.

### File di questa fase e prossimo passo

Modificati in questa fase: `scripts/pilot_private_runtime.go`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_ubuntu_activation.py`, `scripts/pilot_ubuntu_integration.py`, `tests/test_pilot_deployment.py`, `doc/PILOT_DEPLOYMENT.md`, questo checkpoint. Tutti fanno parte del più ampio prototipo unstaged già esistente; non separarli con reset/stash.

**Prossimo passo:** nuova sessione. Prima profilare/riprodurre una sola volta il residuo lease `daemon-reload` pre-candidate con un diagnostic stretto (non un settimo full), mantenendo deadline/break semantics. Se il diagnostic prova sola variabilità e il margine canonico è corretto, eseguire una sola full fixture fresca. Su FINAL PASS eseguire Shard F secondo il logging lifecycle esistente, poi implementare soltanto l'aggregator fail-closed già specificato e consumare evidence reali. Solo dopo rivalutare commit/push e fresh independent review round 1; gate resta `0/2`.

File minimi alla ripresa: `AGENTS.md`, questa sezione, `_systemctl_result`/lease timing in `scripts/pilot_ubuntu_activation.py`, il punto preflight full attorno a `scripts/pilot_ubuntu_integration.py:6050`; per candidate authority consultare `productionStage1Build`/`copyCandidateClosure` in `scripts/pilot_private_runtime.go` e la sezione canonica in `doc/PILOT_DEPLOYMENT.md`.

---

## Executor lease residual resolved; canonical Shard F architecture blocker

- **Data/ora:** 2026-08-27T20:55:40+02:00.
- **Starting/final Git:** branch `fix/oauth-log-redaction-704`; local/upstream/remote HEAD `598f1905462b5df0cb5f009ea79cffb7901545b8`; PR #720 `OPEN`/`DRAFT`; gate `0/2`. Worktree modified/untracked intenzionale preservato, tutto unstaged; nessun commit/push.
- **Stato:** **LEASE RESIDUAL RESOLVED / PRIVATE RUNTIME DEVELOPER GATE BLOCKED DA SHARD F**. Stop condition applicata: Shard F ha esposto un diverso conflitto architetturale; aggregator non implementato/eseguito e full senza FINAL PASS.

### Timing trace e root cause lease

Diagnostic test-only aggiunta tramite `--executor-lease-timing-diagnostic-only`, senza cambiare deadline o logging ordinario. Primo fixture exact pre-candidate PASS ma ha riprodotto la variabilità pericolosa:

| Stage | Duration | Lease remaining end | Dentro lease? |
|---|---:|---:|---|
| base fence build/seal | 16.573 s | — | NO |
| initial executor acquire | 0.018 s | 9.982 s | YES |
| Stage-M build/seal | 1.385 s | 8.596 s | YES |
| native closure + systemd-path bootstrap | 0.945 s | 6.396 s | Stage-M sì; executor-use lease non intrinseca |
| APT/e2scrub/motd/logrotate input attest | 3.578 s | 2.815 s | NO executor authority |
| toolchain/env/generator pre-attestation | 1.911 s | 0.904 s | Stage-M sì; nessun manager USE ancora |
| fresh exact-identity lease acquire | 0.009 s | 9.991 s | YES |
| pre-candidate daemon-reload | 1.153 s | 8.848 s | YES |
| daemon-reload safe boundary | <0.001 s | 8.848 s | YES |
| generated output attest/seal | 1.453 s | 7.394 s | Stage-M sì; no executor USE dopo boundary |
| remaining static candidate/preflight proof | ~37.5 s | lease poi scaduta ma nessun execution-bearing USE | NO executor authority |

- **Root cause:** caso **D con difetto di ordering/soglia**. La lease iniziale veniva correttamente acquisita prima della proiezione globale Stage-M, ma la condizione di rinnovo soltanto a `remaining <= 2.0 s`, combinata con la riserva fissa di 2 s, aveva una discontinuità: con circa 2.05 s restanti il daemon-reload riceveva `max(0.05, remaining-2)=0.05 s`; con meno di 2 s avveniva invece correttamente una fresh lease. Il log `full-6` prova exact call site `verify_host_preflight -> _attest_systemd_boot_surface -> daemon-reload`.
- **Remediation:** ogni azione `systemctl` execution-bearing riacquisisce ora, dopo Stage-M sealed/pre-use preparation, una fresh lease decennale sull'**identico durable record** PID1 executor della Stage-M. Writer nel gap, break/pending o identity drift fanno fail-closed; una identity diversa chiude la nuova lease e rifiuta. L'initial lease resta obbligatoria per costruzione/proiezione Stage-M. Nessuna safe boundary anticipata.
- **Deadline:** invariata `10.0 s`; break reserve invariata `2.0 s`; lease semantics e Stage-M preservate. Daemon-reload del diagnostic post-fix: 0.397 s, fresh remaining 9.603 s alla safe boundary. Esiste un solo daemon-reload execution-bearing nel preflight diagnosticato; i query `show/list-*` non sono execution-bearing.

### Regressione lease e candidate

- Unit mirati renewal/identity drift/execution pre-post/break/Stage-M: **5 passed**.
- Private runtime canonical targeted gate post-fix: **PASS**, 171.505 s. Include crash discovery/open/setlease/hash, expired deadline, actual writer break durante handoff, break_requested fail-closed, safe boundary prima release, S0/S1 crash, post-unshare failure, start/mapping, worker respawn, late dlopen, fresh reload, enabled stop e teardown retry.
- Stage-M: **PRESERVED**. Executor lease: **PRESERVED**. Deadline: **NON cambiata**.
- Candidate authority mirata resta PASS: config/link/bundle/TLS S1, hostile same-inode/rename/delete/symlink/current replacement e reload su private authority.

### Full canonical e Shard F blocker

Unica full Ubuntu fresca post-fix: `GITHUB_RUN_ID=private-runtime-final-full bash scripts/run_pilot_ubuntu_integration_container.sh` → **FAIL / no FINAL PASS**. Ha superato il precedente residuale e raggiunto: bootstrap/closure, H-01..H-05, scheduler, APT/e2scrub/motd/logrotate provenance, R1 closure/recovery/generated race, candidate activation, migration/runtime, TLS e worker lifecycle. Failure canonica al primo real rotate:

`logrotate --force --state <temp>/logrotate.state /etc/logrotate.d/thebitlab` → `Runtime root logrotate deve avere mode 0755` nel `firstaction`; nessun `.1`/FD reopen/post-rotation lifecycle è quindi attestato.

- **Conflitto exact:** il contratto logrotate `_ensure_logrotate_runtime_directory()` richiede `/run/thebitlab` root `0755`, child `logrotate` root `0700`; il service candidate canonico dichiara `RuntimeDirectory=thebitlab/app` e `RuntimeDirectoryMode=0700`. Nel lifecycle reale il parent condiviso non soddisfa più `0755`. Correggere richiede una decisione canonica sulla separazione/ownership dei runtime path, non un chmod permissivo nel helper.
- **Impatto:** Shard F non può provare rotate/reopen, retention e stale inactive lifecycle; classificato **MEDIUM security/availability blocker** (rotazione/retention sensitive log non operativa). Stop condition Shard F applicata; nessun redesign in questa sessione.
- **Definizione F esatta recuperata:** request matrix callback/upstream/unknown host/SNI/malformed/IPv6; marker secret assenti da tutti gli effective persistent log e service stream; metadata; logrotate `--debug`; real access+process inode rotation; snapshot transient authority; zero old FD/current FD reopened; post-rotation access e process lifecycle writes soltanto nei current; rotated files immutati; marker assenti anche dopo rollback; inactive service con stale `/run/nginx.pid` non usato come signal authority.

### Shard, aggregator e finding

- A: PASS corrente (full bootstrap/closure representative; canonical adversarial evidence precedente preservata).
- B: PASS nel full fino al blocker (forged metadata, foreign mount, crash/recovery e lease crash).
- C: PASS nel full (generator ABA/three output roots/second reload/races).
- D: PASS nel full (H-01..H-05, inventory/scheduler).
- E: PASS post-fix targeted; full ha inoltre raggiunto TLS/worker lifecycle.
- F: **FAIL/BLOCKED** al firstaction runtime-root mode, prima della real rotation.
- Aggregator: canonical evidence contract noto ma implementation **NOT PRESENT/NOT RUN**; correttamente non creato senza F reale. Missing/stale/conflicting evidence non è stato trasformato in PASS.
- R1-HIGH-01A: **OPEN**; R1-HIGH-01B: **OPEN**. R1-HIGH-02/03: **CLOSED**, regressioni full verdi fino al blocker. Gate `0/2`.

### Verifiche e cleanup

- Diagnostic timing before/after: PASS; log ignorati `.pi-private-runtime-lease-timing-{1,2}.log`.
- Full canonical: FAIL Shard F come sopra; log `.pi-private-runtime-final-full.log` ignorato.
- `py_compile` activation/integration, Bash syntax runner, diff-check mirato: PASS.
- Static unit mirati: 5 passed. Full `tests/test_pilot_deployment.py`, Python 3.11, Sphinx/course-plan e aggregator: non rieseguiti perché la stop condition precede il final gate.
- Cleanup: zero container/image/volume integration, zero nginx/broker/helper locale e nessun mount/runtime container (fixture rimossa). Restano solo log `.pi-private*` ignorati secondo policy.

**Prossimo passo:** nuova sessione architetturale separata per risolvere il conflitto canonico `/run/thebitlab` tra `RuntimeDirectoryMode=0700` e logrotate root `0755`, senza chmod opportunistico né indebolimento metadata. Prima recuperare il contract systemd/runtime-directory e il contract logrotate in `deploy/pilot/templates/thebitlab.service.template`, `scripts/pilot_ubuntu_activation.py:_ensure_logrotate_runtime_directory`, `doc/PILOT_DEPLOYMENT.md:147-149` e il failure log. Poi eseguire Shard F mirato; solo su PASS una nuova full fresca, aggregator reale, static final gate e commit/push. Non eseguire review indipendente, non mergeare.

---

## Shard F runtime-directory/logrotate authority — DEVELOPER GATE PASS

- **Data/ora:** 2026-08-28T06:26:20+02:00.
- **Starting SHA:** `598f1905462b5df0cb5f009ea79cffb7901545b8`; branch `fix/oauth-log-redaction-704`; remote URL `https://github.com/TheBitPoets/2cornot2c.git`; remote HEAD verificato invariato prima e dopo i gate. PR #720 resta `OPEN`/`DRAFT`; independent gate `0/2`.
- **Stato:** runtime authority, Shard F, full Ubuntu, aggregator e regressioni finali **PASS**. Commit/push ancora da registrare sotto; nessun merge/mark-ready.

### Root cause e systemd 255

- Root cause exact riprodotta col vero bootstrap statico pre-fix: `os.MkdirAll("/run/thebitlab/pilot-activation-fence", 0700)` creava implicitamente `/run/thebitlab` `root:root 0700` prima di systemd/logrotate. Il broker private-runtime aveva lo stesso pattern; il helper Python non era l'attore determinante. Logrotate rifiutava correttamente perché il parent non era l'exact `root:root 0755`.
- Esperimento isolato nell'exact OCI Ubuntu 24.04, `systemd 255.4-1ubuntu8.17`: fresh before parent/app assenti; during parent `0:0 0755` inode 149 e app user/group test `0700` inode 150; after stop parent stesso inode e app assente. Parent preesistente `0700` inode 152 non viene normalizzato da systemd. Con sibling logrotate, parent `0755` inode 156 e logrotate `0:0 0700` inode 157 restano identici durante/dopo start; app `0700` appare solo during e scompare allo stop.
- Systemd da solo segue una leaf `app` symlink precreata; perciò il launcher applicativo ora apre `/run`, parent e app via descriptor `O_NOFOLLOW` e attesta owner/group/mode/dev/inode prima dell'exec.

### Autorità e lifetime finali

| Path | Owner/mode | Writer/authority | Lifetime/scopo |
|---|---|---|---|
| `/run/thebitlab` | `root:root 0755` | contratto comune bootstrap/fence/private/logrotate, openat nofollow e inventory chiusa | boot/shared coordination; nessun file diretto |
| `app/` | `thebitlab:thebitlab 0700` | systemd nested RuntimeDirectory + launcher attestation | service application; rimossa allo stop |
| `logrotate/` | `root:root 0700` | trusted activator | boot/transient reopen; snapshot `0600` rimosso solo dopo successo |
| `pilot-activation-fence/` | `root:root 0700` | static bootstrap/TrustedActivationFence | lock/state/transaction activation |
| `pilot-private-runtime/` | `root:root 0700` | static broker | service nginx; S0/S1 tmpfs RO e overlay RO fino allo stop |
| `logrotate/reopen.json` | `root:root 0600` | firstaction atomic replace | schema v1, boot ID, time, exact path/dev/inode; metadata-only |

- Nessun `tmpfiles.d`: i trusted creator applicano lo stesso parent contract; systemd possiede soltanto app. Le root sintetiche S0/S1 sono `0755` **dentro** la private pivot root perché i worker `www-data` devono risolvere reopen/dlopen; restano nascoste dietro il host leaf `pilot-private-runtime 0700`. File/dir sensibili conservano mode propri.
- Attori tracciati: static bootstrap e Python fence su `pilot-activation-fence`; broker Go su `pilot-private-runtime`; systemd su `app`; activator logrotate su `logrotate/reopen.json`; recovery rimuove solo transaction/mount exact; private cleanup rimuove solo il proprio tree; stop app non rimuove parent/sibling.

### Attacchi runtime-directory

- Exact fixture targeted `--runtime-directory-authority-only`: parent symlink/regular/0700/chown/group-writable **REJECT**; unknown direct child **REJECT**; logrotate symlink/mode/chown **REJECT**; canonical stale child preservato; rename-away snapshot produce nuova authority vuota ma `_read_logrotate_snapshot` **REJECT**; app symlink **REJECT dal launcher**; fresh same-path/new-inode app canonical accettata come nuovo lifecycle; parent rename-over produce soltanto nuova authority canonical vuota e le authority precedenti non sono riutilizzate.
- Parent `0755` listing/traversal test: nobody non legge app state né snapshot; app owner legge app state ma non logrotate; root-only fence/private leaves non sono esposte. Parent/app/logrotate inode e stop/restart semantics provati.

### Shard F e root sintetica

- Primo residuale dopo parent fix: master root riapriva i nuovi inode, ma tutti gli 8 worker `www-data` conservavano gli old FD; diagnostica process-level safe mostrava `reopening logs` seguito da `EACCES` anche per `/dev/null`. Root cause: overlay synthetic `/` mode `0700`; gli FD iniziali erano ereditati dal master.
- Fix: S0/S1 tmpfs root e synthetic overlay root `root:root 0755`, mentre il mount host resta dietro runtime leaf `0700`; privateExec attesta exact metadata. Nessuna modifica lease/S1 writability/logrotate checks.
- Shard F isolato exact: request callback/upstream/unknown host/SNI/malformed/IPv6; audit path-only; secret markers assenti prima/dopo; metadata/ACL; debug; snapshot schema/boot/time/dev/inode; access+process real inode rotation; USR1; old FD zero/current FD >=1 per process/cgroup canonici; post-write solo current; rotated byte-invariant; rollback marker absence; stale PID/inactive no signal; retention state e cleanup: **SHARD F PASS**.

### Full, evidence e aggregator

- Fresh final exact-pushed-SHA runs: A `pr720-9db-shard-a` PASS; B+E `pr720-9db-shards-b-e` PASS; C `pr720-9db-shard-c` PASS; full D+F `pr720-9db-full-d-f` PASS. I quattro run pre-commit su `598f1905` restano soltanto evidenza diagnostica e non sono usati per autorizzare il candidate finale. Full include S1, lease, bootstrap, recovery/generated races, H-01..H-05, runtime/TLS/workers, real rotate/reopen/stale inactive e cleanup.
- Evidence schema `thebitlab.private-runtime-shard-evidence.v1`; exact candidate `9db361c918defbc0569b24af332b815e8617657b`, policy `e23f42ae924f142c2fd1deacf244cbd65f23734bfd8e01a9bad98c1f1cc62265`, toolchain `ci-9db361c918de` / manifest `646578dc2b1c4eef90f0189a87497858237148c9f3a44963e7b892f474a62aa1`, OCI `sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea`, Python 3.12.3 digest-bound, Node explicitly non-required, freshness e cleanup interno/esterno.
- `scripts/pilot_private_runtime_evidence.py` fail-closed: A–F exact, missing/stale/candidate/schema/duplicate/conflict/missing-cleanup/unknown-scenario/skip/required-node-unknown regressions PASS. Aggregator reale sui 4 log finali exact `9db361c9`: **PASS**, cleanup true.

### Finding, test e cleanup

- R1-HIGH-01A **CLOSED**: static bootstrap prima di Python + preload six-timing zero marker + private late load/full/F/aggregator.
- R1-HIGH-01B **CLOSED**: closed hwcaps v2/v3/v4/735 absent, private namespace/maps + full/F/aggregator.
- R1-HIGH-02 e R1-HIGH-03 **CLOSED**, regressioni recovery/generated full verdi. Nessun nuovo HIGH/MEDIUM aperto.
- `tests/test_pilot_deployment.py` Python 3.12: **232 total = 197 PASS + 35 expected SKIP, 0 FAIL/ERROR**; Python 3.11.15 uv isolated: stesso esito. Target: lease 5 PASS; candidate 1 PASS; logrotate/logging 43 PASS + 4 expected SKIP; thread-affinity 2 PASS; aggregator 11 PASS + authority 2 PASS.
- Go: 3 CGO-free static build PASS; PT_INTERP 0; dynamic sections 0. `py_compile` PASS; 15 shell Bash syntax PASS; Sphinx `-W` PASS; course plan check PASS; `git diff --check` PASS.
- Cleanup: integration container/image/volume zero; immagini Shard-F/buildcheck rimosse; venv uv/JUnit/temp binaries rimossi; nessun processo/mount/runtime noto; soli `.pi-private*.log` ignorati, non da stageare.

### Git/gate/prossimo passo

- Diff completo accumulato ispezionato; POC/diagnostic harness restano soltanto come riproduzioni security test-only intenzionali e non sono runtime command production (main production accetta solo `production-*`). `CHECKPOINT.md` resta local-only unstaged secondo la convenzione corrente.
- **Commit/push:** commit unico `9db361c918defbc0569b24af332b815e8617657b` (`fix: seal private runtime execution authority`), push normale fast-forward `598f1905..9db361c9`; remote HEAD verificato exact. PR #720 verificata `OPEN`/`DRAFT`, head exact; GitHub riporta `mergeable=CONFLICTING`, `mergeStateStatus=DIRTY` contro baseRefOid `5472eef8`. Non è stato eseguito rebase/merge/reset: il conflitto è un residuo da trattare separatamente dopo la fresh independent review, non invalida i gate runtime exact-HEAD ma blocca qualunque merge. `CHECKPOINT.md` resta il solo file local modified/unstaged ed è escluso dal commit.
- **Developer gate:** PASS. **Independent gate:** `0/2`.
- **Prossimo passo dopo push:** nuova sessione, fresh Independent Review Round 1 dell'intero diff contro merge-base sull'exact pushed SHA; non mark-ready e non mergeare.

---

## Current main integration e final developer re-attestation — candidate 35fa6608

- **Data/ora:** 2026-08-28T20:58:51+02:00.
- **Obiettivo/stato:** integrare `origin/main` prima della review indipendente e rigenerare il developer gate exact-SHA. **COMPLETATO / PASS**; PR #720 resta `OPEN`/`DRAFT`, non mark-ready e non mergeata; independent gate **0/2**.
- **Starting candidate:** `9db361c918defbc0569b24af332b815e8617657b`, developer gate precedente PASS. La review indipendente è stata differita perché GitHub riportava `CONFLICTING/DIRTY`; ogni merge avrebbe comunque invalidato round SHA-specifici.
- **Topologia iniziale:** branch `fix/oauth-log-redaction-704`; local/remote feature `9db361c9`; main `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0`; historical merge-base `5472eef86568a4e7ce59ad34ba937220df27efd7`.

### Main delta, preview e merge

- Commit main ispezionati: `dcb76f600fa951ba94fffbd355a6c13dfcbfb424` (runtime plugin sandbox), `ec60eaca11da481a8510ec67255abaf76ac5b23e` (student grading authoritative sandbox), `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0` (Romeo docs portal).
- 20 file incoming ispezionati: `.dockerignore`; `CHECKPOINT-runtime-sandbox.md`; sei doc runtime/sandbox e `doc/sphinx/index.rst`; assignment-runner Dockerfile; sei script grading/student/runtime/sandbox; cinque test correlati. Delta `1264 insertions/50 deletions`.
- Rilevanza: nuovo boundary Docker condiviso fail-closed, OCI digest, input containment/symlink rejection, no local fallback e authoritative finalize. Nessun import/dipendenza dal private-runtime; unico overlap reale `.dockerignore`, rilevante perché entrambi i build context sono allowlist chiuse.
- `git merge-tree` non mutante: unico conflitto `.dockerignore`. Feature intent: includere `pilot_static_bootstrap.go`, `pilot_private_runtime.go`, `pilot_private_runtime_poc.go`; main intent: includere `thebitlab_sandbox_boundary.py`. Risoluzione semantica: unione esatta delle quattro allowlist, senza `-X ours/theirs`.
- Tutti gli altri 19 blob incoming corrispondono byte-per-byte a main. Confronto contro entrambi i parent: nessuna sparizione main, nessun file private-runtime modificato, nessun test/assertion eliminato o indebolito; marker/unmerged entry zero.
- Strategia: merge normale `--no-ff`, nessun rebase/reset/stash/clean/force push. Commit `35fa66080d36018e56465f82ebc56dafc03ebcc7` (`merge: integrate current main into private runtime`), tree `e3ae7383903edefca0f64ec1803fbbd08188ca68`, parent `9db361c9` + `cdcdf4a6`.

### Preservazione CHECKPOINT

- Stato originale: solo `CHECKPOINT.md` modified/unstaged, hash working `6d56c4dfcd8ab7af1f62a2d40db2388639d5304d`; log `.pi-private*` ignorati.
- Copia byte-exact esterna temporanea `../.pi-pr720-checkpoint-before-9db361c9.md` e patch `../.pi-pr720-checkpoint-before-9db361c9.patch`, hash patch `a15c9b66fbe3fbbc4bd8e3f9b59fbb348a0b496f`; `cmp` PASS prima/durante/dopo merge e prima dell'append.
- Il checkpoint è rimasto fuori dall'indice/merge commit ed è stato poi solo appeso deliberatamente; i 130481 byte originali sono stati verificati come prefisso byte-exact del file finale prima di rimuovere le copie temporanee esterne. Evidenza persa: **ZERO**. Convenzione finale: checkpoint local-only unstaged.

### Incoming-main regression e fast gates

- Test grading/student/runtime/plugins/sandbox/runner Python 3.12: **127 total = 122 PASS + 5 expected SKIP, 0 FAIL/ERROR**.
- Assignment runner build canonico via `scripts/build_assignment_runner.py`: PASS; il nuovo helper è nel Docker context/image. Un primo `docker build` raw senza build-arg manifest ha prodotto APT URL vuoto/404: comando non canonico, non ripetere; il build canonico è verde.
- Merge-tree `git diff --check`, py compile/compileall, 15 Bash, conflict-marker scan e private pilot unit gate: PASS.
- Tre Go CGO-free statici: build PASS, PT_INTERP 0, dynamic section 0.

### Private-runtime exact-SHA re-attestation

- A exact `pr720-35fa-fresh2-shard-a`: PASS — static bootstrap/preload six timings, HWCAPS v2/v3/v4, crash/recovery, closure zero-unpinned.
- B+E exact `pr720-35fa-fresh2-shards-b-e`: PASS — forged/foreign mount, fence+lease crash/break/deadline, S0/S1/candidate authority, late dlopen, worker respawn, fresh reload/stop. Stage-M e deadline 10.0 s preservati.
- C exact `pr720-35fa-fresh3-shard-c`: PASS — generated early/normal/late, second reload, unit/executable races.
- Full D+F exact `pr720-35fa-exact-full-d-f-r2`: **FINAL PASS** — H-01..H-05, inventory/scheduler, S1, lease, loader/HWCAPS, runtime-directory, start/maps/respawn/reload/stop, crash/recovery/fence, TLS, logging/redaction, real rotate/reopen, stale/inactive, retention e cleanup.
- Shard F: request matrix, secret marker absent pre/post rollback, firstaction schema/boot/time/dev/inode, real access+process inode rotation, USR1, old FD zero/current FD canonical, post-write current-only, rotated bytes invariant, stale PID inactive, retention/cleanup: **PASS**.
- Tentativi non finali: A iniziale emise il sentinel `cccc…` perché `GITHUB_SHA` non era esplicito; escluso e rigenerato exact. Prima full exact terminò su timeout test-only Stage-1 `after_nginx_enable`; private code invariato, cleanup PASS, unico fixture successivo FINAL PASS. Il primo aggregate rifiutò correttamente A stale dopo la full >4h; A/B/E/C rigenerati senza estendere freshness. Un refresh C fallì chiuso su nesting race/restore; fixture successivo PASS e la full aveva già coperto lo scenario. Non usare log falliti/sentinel come evidence.

### Aggregator, findings e test finali

- Aggregator reale su quattro log finali: **PASS** per candidate `35fa6608`, shards A–F, policy `e23f42ae924f142c2fd1deacf244cbd65f23734bfd8e01a9bad98c1f1cc62265`, toolchain `ci-35fa66080d36`, manifest `cc3c1f28c2bfdbccf1668abbc95a3b77eed7bc574d29432fd487d48257b46e6b`, OCI `sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea`, Python 3.12.3 digest-bound, Node non-required, freshness e cleanup true.
- Negative aggregator: **11/11 PASS**; missing, stale, candidate mismatch, malformed/schema, duplicate/conflict, missing cleanup, unknown/missing scenario, skip e node identity fail-closed.
- R1-HIGH-01A/B/02/03: **CLOSED**. H-01..H-05 e altri sentinels storici: PASS. Nessun HIGH/MEDIUM/LOW nuovo aperto.
- `tests/test_pilot_deployment.py`: Python 3.12 **232 total = 197 PASS + 35 expected SKIP**; uv Python 3.11.15 stesso risultato; zero fail/error.
- Sphinx `-W --keep-going`: PASS su output esterno fresco. Il primo output nel vecchio `_build` era bloccato da ACL Windows su `searchindex.js`; nessun file cancellato. Course-plan `--check`: PASS. Final diff-check/compileall/Bash: PASS.
- Cleanup: zero container/image/volume integration o image `pi-pr720-*`; cleanup interno/esterno di ogni evidence run true; nessun processo/mount/runtime noto; `.pi-private-35fa*.log` ignorati e non staged.

### Git, PR e prossimo passo

- Push normale `9db361c9..35fa6608`; local, tracking e `ls-remote` coincidono su `35fa66080d36018e56465f82ebc56dafc03ebcc7`; `origin/main` è il secondo parent/ancestor.
- GitHub dopo push: PR #720 `OPEN`, `DRAFT`, `MERGEABLE`; `mergeStateStatus=UNSTABLE` soltanto perché gli 11 check del nuovo SHA sono queued/in-progress. BaseRefOid `cdcdf4a6`, head exact `35fa6608`. Non mark-ready, non mergeata.
- **Developer/main-integration gate: PASS. Private-runtime gate: PASS. Shard F: PASS. Aggregator: PASS. Independent gate: 0/2.**
- **Prossimo passo esatto:** nuova sessione completamente fresca, Fresh Independent Review Round 1 dell'intero diff `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0...35fa66080d36018e56465f82ebc56dafc03ebcc7`, fissando lo SHA. Prima verificare che HEAD remoto/PR non siano cambiati e che la CI exact-head non sia rossa; non mark-ready e non mergeare.

---

## PR720 — CI reviewed artifact baseline / reproducibility remediation — BLOCKED pre-candidate

- **Data/ora:** 2026-08-29T20:55:00+02:00.
- **Obiettivo:** spiegare e correggere il failure Quality #33201776482 `Reviewed artifact digest mismatch: /usr/bin/ps` senza indebolire H-05, quindi rigenerare un candidate attestato. **Stato: IMPLEMENTAZIONE E DETERMINISMO PASS / FULL DEVELOPER GATE BLOCKED DA INSTABILITÀ DOCKER DESKTOP.** Nessun commit/push/new candidate; PR #720 resta `OPEN`/`DRAFT`; independent gate `0/2`; non review, non mark-ready, non merge.
- **Preflight Git finale:** branch/local/upstream/remoto feature ancora `35fa66080d36018e56465f82ebc56dafc03ebcc7`; `origin/main=cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0`. `CHECKPOINT.md` preservato unstaged.

### CI blocker e causa provata

- Quality run `33201776482`, job `python`, Python tests **2507 passed / 17 skipped**; solo `Run effective Ubuntu deployment integration` fallito in `_attest_expected_package_files` su `/usr/bin/ps`.
- Baseline policy/cached: `/usr/bin/ps`, realpath uguale, `procps=2:4.0.4-4ubuntu3.2`, amd64, size `146424`, SHA-256 `8e86f498aa4aabfcea6c179d6181557140b4597f1c39bb94e2aba32158b58297`, md5 dpkg `ca10586df7dce4c505a957df0e37f4c9`, manifest coerente.
- Fresh CI/no-cache: `procps=2:4.0.4-4ubuntu3.3`, amd64, size `146424`, SHA-256 `26a77f641ef5d6799195675dc4d23fc8de4a0ca04e3955637faf0d84f87554fd`, md5 dpkg `7dda661724fb4aab55d851168ad4fd96`, manifest coerente. CI log prova download da `noble-updates` e upgrade OCI-installed `.2 -> .3`; Launchpad build `33471178`, source `procps 2:4.0.4-4ubuntu3.3`, pubblicato negli Updates il 2026-08-28.
- Cached build ha mostrato layer APT `CACHED`, `procps/libproc2-0=.2`, package inventory SHA `fb412411...`; fresh `--no-cache` ha installato entrambi `.3`, inventory SHA `91ff5266...`, e ha riprodotto localmente l'exact exception `/usr/bin/ps` prima di modifiche production. Host lint non entra nel Docker package namespace.
- **Root cause combinata A+B+D+E/F:** OCI immutabile conteneva `.2`, ma Dockerfile consultava mirror APT mobili senza versioni; cache locale mascherava il passaggio a `.3`; policy era stata revisionata contro `.2`. Il package sorgente ricostruito ha cambiato tutti i native procps, ma l'intersezione col closed reviewed runtime è `/usr/bin/ps`; il coupled `libproc2-0` ha cambiato `/usr/lib/x86_64-linux-gnu/libproc2.so.0.0.2` da `f2b9f2eb...` a `fe22f6fa...` e interseca la native closure. Gli altri executable procps mutati non appartengono all'inventario execution/runtime chiuso.

### Baseline scelta e implementazione locale

- **Option A:** conserva la baseline `.2` già revisionata. Snapshot ufficiale Ubuntu immutabile `20260822T000000Z`, che risolve exact `procps/libproc2-0=.2` e l'intero package set cached originale.
- Dockerfile ora parte una sola volta dall'OCI digest, configura esclusivamente `https://snapshot.ubuntu.com/ubuntu/20260822T000000Z`, mantiene `Signed-By` Ubuntu archive keyring, usa una trust anchor repository-static ISRG Root X1 (SHA file `22b557...`, fingerprint X.509 `96bcec...`) e non disabilita TLS peer/host. Tutti i package diretti sono version-pinned.
- Nuovo `deploy/pilot/ci/ubuntu-systemd-package-baseline.json`: OCI/snapshot/CA, exact richieste dei tre stage, count e SHA dell'intero inventario ordinato `binary:Package=Version`, artifact `/usr/bin/ps` e `libproc2`. Runtime 144 package SHA `fb412411...`; static builder 108 `a2449a48...`; reviewer builder 140 `8f2ba985...`; manifest SHA `35dba578...`.
- Nuovo attestor `scripts/pilot_ubuntu_package_baseline.py`: image/candidate manifest byte-equal, source snapshot exact, CA, arch, full package inventory, versioni dirette, owner/source/status, realpath/SHA e consistenza md5sums dpkg degli artifact.
- Runner sempre `docker build --pull --no-cache`, attesta label snapshot/manifest/inventory. Evidence schema shard v2 e aggregator legano `ubuntu_snapshot`, `package_baseline_sha256`, `package_inventory_sha256`; negative matrix estesa per policy/toolchain/snapshot/package baseline/package inventory mismatch. Documentazione canonica aggiornata.
- File intenzionali locali: `.dockerignore`, `.gitignore`, `deploy/pilot/ci/Dockerfile.ubuntu-systemd`, nuovi `deploy/pilot/ci/isrg-root-x1.pem` e `deploy/pilot/ci/ubuntu-systemd-package-baseline.json`, `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_private_runtime_evidence.py`, `scripts/pilot_ubuntu_integration.py`, nuovo `scripts/pilot_ubuntu_package_baseline.py`, `scripts/run_pilot_ubuntu_integration_container.sh`, `tests/test_pilot_deployment.py`. Nessuno staged.

### Determinismo, H-05 e test passati

- Due build indipendenti `--no-cache`: PASS. Entrambe: OCI `sha256:561618...`, snapshot `20260822T000000Z`, package manifest `35dba578...`, package inventory `fb412411...`, `/usr/bin/ps=8e86f498...`, `libproc2=f2b9f2eb...`, 418 path reviewed closure digest `e28f8557...`. Full package inventory snapshot = cached historical byte-for-byte.
- Pristine `_attest_systemd_boot_surface`: PASS. `/usr/bin/ps` alterato con owner/version uguali e md5sums dpkg aggiornato/coerente: **REJECT** exact `Reviewed artifact digest mismatch`; static SHA preservato.
- Full provisional ha provato prima del blocker: same-name/same-version e higher-version `procps` con `/usr/bin/ps` malicious package-valid entrambi REJECT; vecchie H-05 systemd/bash/grep/nginx/generator e H-01..H-04 REJECT/PASS attesi; loader/HWCAPS/recovery/generated races verdi fino al punto raggiunto.
- Linux full Python 3.12 + Node 20: **2509 passed, 20 skipped**. Linux full Python 3.11 + Node 20: **2509 passed, 20 skipped**. Incoming-main sandbox/regressions: PASS (122 pass/5 skip dalla matrice). Target baseline/aggregator/native/static: 19 pass. Bash syntax, py_compile e diff-check intermedi: PASS.
- Windows host full non canonico: 2451 pass/76 skip, due failure platform baseline (`WinError 193` launcher macOS e symlink privilege); Linux canonico sopra verde.

### Full gate bloccato e tentativi da non ripetere automaticamente

1. Canonical provisional full via runner ha superato package baseline, nuovi procps H-05, H-01..H-05, scheduler, loader/HWCAPS, recovery e generated race; più avanti `systemctl start nginx.service` è scaduto a `7.95 s` dentro lease invariata. Nessuna deadline/lease modificata.
2. Retry runner: nessuna integrazione avviata; BuildKit ha perso Docker Desktop con `rpc error ... EOF` durante apt snapshot.
3. Dopo restart esplicito Docker, full equivalente sull'immagine no-cache già attestata è terminato `137`; subito dopo la named pipe `dockerDesktopLinuxEngine` era nuovamente assente. Log si ferma durante matrice H-05. È il secondo crash del daemon/backend nella fase, non un artifact mismatch.

Stop condition repository applicata: non fare un altro retry identico senza decisione e remediation concreta dell'affidabilità Docker. Full FINAL PASS, Shard F fresh, A–F exact candidate, aggregator finale, static final, commit/push e CI **NON completati**. Nessun candidate creato. Le due immagini determinism e test image possono restare perché il daemon è down; nessun container era elencato prima del secondo crash, ma cleanup Docker finale non verificabile finché il backend non riparte. I log `.pi-private-baseline-*` sono evidenza locale ignorata; diagnostic JSON/TXT/temp source rimossi.

**Prossimo passo:** nuova sessione. Verificare remoto/branch/worktree; avviare e stabilizzare Docker Desktop, ispezionare risorse/backend e rimuovere soltanto immagini/container `pi-pr720-*` temporanei se necessario. Non ripetere il full finché non esiste una causa/remediation concreta dei due crash. Poi eseguire un solo full pre-candidate; su FINAL PASS completare static/docs, creare commit locale, rigenerare A–F e aggregator sull'exact SHA, quindi push e attendere Quality `python` exact-head. Gate resta `0/2`; non review, non mark-ready, non merge.

---

## Docker stabilization e pre-candidate gate — BLOCKED su fence race

- **Data/ora:** 2026-08-30T04:27:33+02:00.
- **Git/PR/remoto:** branch `fix/oauth-log-redaction-704`; local, upstream e remote feature invariati `35fa66080d36018e56465f82ebc56dafc03ebcc7`; remote main `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0`. PR #720 `OPEN`/`DRAFT`, `MERGEABLE/UNSTABLE`; Quality `python` resta rosso sul vecchio HEAD per `/usr/bin/ps`. Nessun file staged, commit, push, candidate, review, mark-ready o merge.
- **Stato:** **DOCKER BACKEND STABILIZZATO / PRE-CANDIDATE BLOCKED / NESSUN FINAL PASS**. Per contratto non sono state generate evidence A–F exact-candidate né eseguito l'aggregator candidate.

### Stabilizzazione Docker concreta

- Docker Desktop era tornato disponibile (`4.44.0`, Engine `28.3.2`, WSL2, 8 CPU/~8.2 GB VM), ma Windows aveva soltanto ~0.24–0.59 GB RAM e ~0.62–0.82 GB commit liberi su ~44.9 GB.
- Root cause host concreta: cinque PowerShell figli dello stesso `codex.exe`, bloccati da ~40 minuti in scansioni ricorsive read-only di `C:\Users\antonio`/`AppData`, consumavano insieme oltre 17 GB private commit. Terminati soltanto gli exact PID scanner dopo verifica parent+command line; parent Codex e processi estranei preservati.
- Dopo cleanup: ~6.7 GB RAM e ~15.2 GB commit liberi; Docker smoke su image baseline PASS, backend rimasto disponibile durante entrambi i gate; nessun OOM VM trovato nei log. Il panic Docker Desktop osservato era nel solo handler UI `POST /install/onboard`, non la causa del gate.
- Stato finale: Docker sano, zero container/image integration, zero scanner ricorsivi, nessun processo temporaneo noto. I due vecchi container estranei exited e l'image `pi-pr720-determinism-2:baseline` sono stati preservati.

### Pre-candidate gate e stop condition

1. Full unico post-stabilizzazione, log `.pi-private-baseline-pre-candidate-stabilized.log`: package baseline e H-01..H-05/race iniziali verdi; **FAIL** dopo 300 s sul crash seam Stage-1 `after_unit_reload_attestation`. Backend e container erano ancora vivi; runner ha poi completato cleanup. Nessun marker terminale PASS/evidence/cleanup candidate utilizzabile.
2. Remediation concreta test-only: in `scripts/pilot_ubuntu_integration.py` timeout per ogni child Stage-1 portato da 300 a 600 s e aggiunto timing per seam. Nessuna lease/deadline production o criterio PASS modificato. Static gate successivo: `py_compile`, `tests/test_pilot_deployment.py`, Bash syntax e `git diff --check` **PASS**.
3. Un solo full successivo consentito, log `.pi-private-baseline-pre-candidate-stabilized-r2.log`: **FAIL** prima della Stage-1, race `generated-output-during-generation` con `TrustedActivationFence: Nesting fence divergente`; restore ha fallito chiuso preservando la quarantine nel container effimero. Runner ha rimosso container/image; nessun residuo host.

Dopo due full senza progresso terminale è applicata la stop condition. Non ripetere un terzo full invariato e non trasformare pass parziali o SHA sentinel in evidence. La failure race è della stessa classe intermittente già osservata nel precedente refresh shard C, ma non è diagnosticata né corretta in questo worktree.

### Worktree, test e prossimo passo

- Modifiche baseline precedenti integralmente preservate, tutte unstaged; nuova modifica di questa sessione soltanto nel crash timeout/timing di `scripts/pilot_ubuntu_integration.py`, oltre a questo checkpoint. Nuovi baseline file restano untracked intenzionali.
- `git diff --check -- . ':!CHECKPOINT.md'`: PASS. Full FINAL PASS, static/docs final post-full, commit candidate, A–F exact SHA, aggregator e CI exact-head: **NON ESEGUITI/BLOCKED**.
- Log ignorati da preservare: `.pi-private-baseline-pre-candidate-stabilized.log`, `.pi-private-baseline-pre-candidate-stabilized-r2.log`, `.pi-pre-candidate-static-after-timeout.log`.
- **Prossimo passo:** nuova sessione diagnostica mirata, non un altro full. Riprodurre/isolare soltanto `generated-output-during-generation` (preferibilmente col flag shard C/fence race o harness purpose-built), raccogliere state/nesting/mount witness prima del restore e correggere solo su causa provata. Dopo test mirato PASS, decidere se mantenere la soglia Stage-1 600 s; quindi un solo full pre-candidate fresco. Soltanto su `FINAL PASS`: static/docs finali, commit locale exact candidate, A–F con `GITHUB_SHA` exact e run ID distinti, aggregator fail-closed, poi push/CI. Gate resta `0/2`.
- **File minimi:** `AGENTS.md`, questa sezione, `_test_trusted_activation_fence_races` in `scripts/pilot_ubuntu_integration.py`, nesting/state authority in `scripts/pilot_trusted_activation_fence.py`; ampliare soltanto se il diagnostic lo richiede.

---

## Generated-output / nested fence race — BLOCKED, real PID1 authority injection

- **Data/ora:** 2026-08-30T07:24:43+02:00.
- **Starting/final SHA:** local/upstream/remote `35fa66080d36018e56465f82ebc56dafc03ebcc7`; branch `fix/oauth-log-redaction-704`; PR #720 verificata `OPEN`/`DRAFT`; independent gate `0/2`. Stato precedente `SUSPENDED/BLOCKED`; worktree baseline e diagnostiche preservato, nessun commit/push/candidate.
- **Stato:** **BLOCKED — MODEL B REAL SECURITY BUG + secondary nested teardown masking**. Stop condition applicata: l’output hostile diventa graph effettivo di PID1 prima del reject e richiede un nuovo boundary architetturale; nessuna correzione parziale production.

### Reproducer stretto e timeline

Harness disposable test-only (rimosso dal worktree al termine), in fresh Ubuntu 24.04/systemd 255 container per tentativo, senza full integration: outer activation/base, outer execution/source freeze, vero `daemon-reload`, mutatore fork root, nested generated-output seal, attestation, teardown. Barriera esistente `fence_during_snapshot_copy`: il mutatore corre durante reload, si ferma al boundary reload→seal, poi crea una sola entry sotto la prima root già copiata (`/run/systemd/generator`) prima dei bind finali. Tre tentativi corretti fresh **3/3 REPRODUCED** (attempt 3/4/5); due calibrazioni precedenti non contano (copy instabile fail-closed pulita; root ordinata errata e cleanup pulito). Due log storici indipendenti avevano già lo stesso primary su `generator.early`/`generator`.

Timeline attempt 4, monotonic relativa:

| T | +s | PID/attore | Evento |
|---|---:|---|---|
| T0 | 0.000 | 106 activator | session richiesta |
| T1 | 12.887 | 106 | base ACTIVE |
| T2 | 16.115 | 106 | execution/source roots frozen ACTIVE |
| T3 | 16.139 | 695 external root mutator | race output avviata |
| T4 | 19.800 | 106 | daemon-reload ritorna; nested seal richiesto |
| T5 | 19.866 | PID1 query | graph già contiene hostile DropInPaths/ExecStartPost |
| T5.1 | 19.867 | 695 | scritture continue fermate |
| T5.2 | 20.311 | 695 | create post-copy `/run/systemd/generator/nginx.service.d/review704-postcopy.conf`, dev/inode `100/9061`, parent `100/4861`, uid/gid 0, mode 0644, non symlink; stesso mnt ns `mnt:[4026532474]` |
| T6 | 21.018 | 106 | generated-output child ACTIVE/RO |
| T7 | 21.703 | 106 | attestation REJECT `Fragment generated ambiguo per nginx.service`; marker absent |
| T8 | 21.867 | 695 | mutatore terminato rc 0 |
| T9 | 21.868 | 106 | teardown inner richiesto |
| T10 | 36.268 | 106 | primary underlying mismatch mascherato da nesting divergence |

Exact primary: `TrustedActivationFenceError: Underlying mutato durante fence; protezione lasciata attiva: /run/systemd/generator`. Unico call site letterale della divergence: `SnapshotMountFence.__exit__` dopo `_remove_transaction`, quando la transaction locale non è l’ultima in `state`. Call chain: generated child teardown rileva underlying mismatch e scrive poisoned; execution parent tenta comunque teardown, lo marca `teardown`/smonta e poi emette `Nesting fence divergente`; base ripete lo stesso errore. Il messaggio finale maschera quindi il primary e viola il LIFO fail-closed, ma non è la causa dell’iniezione.

### Autorità, outer/inner e semantica generated

| Surface | Classe | Writer/mutabilità | Attestazione |
|---|---|---|---|
| generator source roots e non-generated systemd/package code | A reviewed immutable source authority | frozen prima del reload; nessun writer durante use | static package/SHA, closed inventory, execution/base snapshots |
| `/run/systemd/generator{.early,,.late}` | B trusted generated output | PID1/systemd soltanto durante daemon-reload secondo il modello; derived authority | post-reload nested snapshot RO, generated provenance/graph/seven-slot late checks |
| original/hidden lower generated roots e host path writable pre-seal | C untrusted underlying host state | il fork root esterno riesce a scrivere durante reload/seal | deve restare non autorevole; mismatch mantiene poison |
| `state.json`, transaction tmpfs, immutable manifest, mount witness/token | D fence internal state | solo fence lifecycle | schema chiuso + mountinfo source/device/ID/options + manifest RO |

Canonical systemd model: le tre generated dirs sono intenzionalmente writable durante il solo trusted reload; gli output sono derived, non source authority; diventano stabili solo dopo reload + output seal + provenance/effective graph attestation. La fence attuale snapshotta output **solo dopo** generation. Nested activation/execution entry significa reference-count/reuse dello stesso owner PID; il generated seal è una child transaction distinta LIFO. Un secondo activator indipendente deve attendere/fallire bounded sul host-global lock (30 s), non confrontare una fase transitoria.

Attempt 4 outer/inner:

| Field | Outer execution | Inner generated | Must match? | Risultato |
|---|---|---|---|---|
| token/root | `106-480046…` / own transaction root | `106-7fa9e4…` / own root | no, anti-ABA per transaction | distinct corretto |
| phase | active | active | sì al punto T7 | match |
| mount namespace | `mnt:[4026532474]` | stesso | sì, PID1 namespace | match |
| tmpfs device / mount ID | `0:92` / 460 | `0:94` / 488 | no, independent snapshot authority | distinct corretto |
| RO state | ro,nodev,nosuid | ro,nodev,nosuid | sì | match |
| source inventory | `/etc` + 5 runtime source roots | N/A | no, A vs B | scoped correttamente |
| generated inventory | N/A | generator 6, early 2, late 2 records | no | child derived inventory presente |
| generation/epoch | nessun campo | nessun campo | non confrontabile | gap informativo, non primary |
| immutable/sealed/active manifest | own execution manifest | own output manifest | internally self-consistent | PASS prima teardown |
| underlying manifest | source lower invariato | `generator` contiene post-copy hostile delta | deve uguagliare sealed al teardown | **FAIL primary** |
| PID1-visible root | outer source snapshots | inner generated snapshots | categorie diverse | expected |
| generator source identity | reviewed source frozen (`systemd-debug-generator`, dev/inode `90/2160` nel run) | inherited | deve derivare dall’outer | PASS |
| generated output identity | N/A | PID1 aveva già caricato `/run/systemd/generator.early/.../review704.conf` | hostile non deve essere accepted | attestation REJECT, ma manager-visible |

### Mutator/oracle e root cause

- Mutatore attempt 4: PID 695, fork dell’activator root (uid/gid 0), stesso mount namespace di PID1/activator, target generated output; 8,859 scritture durante reload più exact post-copy create. Operazioni: mkdir/write/atomic replace, poi deterministic same-path create post-copy. Non tocca source authority.
- PID1 oracle prima del seal: `DropInPaths=/run/systemd/generator.early/nginx.service.d/review704.conf`; effective `ExecStartPost=/usr/bin/touch /run/review704-generated-output-marker`. Quindi systemd **ha visto e caricato** l’iniezione.
- Gate: REJECT prima di start; marker **assente in tutti i 3/3 tentativi**. L’eccezione da sola non è usata come prova: marker e graph effettivo sono entrambi registrati.
- Classificazione: **MODEL B**. Il test originale è inoltre temporalmente troppo ampio (continua a mutare durante il seal, non soltanto durante generation), ma non è un’interleaving impossibile: un mutatore esterno nello stesso namespace può farlo anche in produzione. Non è Model A/C/D/E. Stale state escluso da fresh tmpfs/container e precheck state/mount/actor absent.
- Sicurezza residua: la late attestation impedisce al trusted activator di eseguire il marker, ma il graph hostile è già autorità effettiva PID1; con transaction poisoned non esiste oggi un rollback manager sicuro prima che timer/attivatori non cooperanti possano usarlo. Sistemare soltanto LIFO/error preservation non chiude questo rischio.

### Timeout, matrix, cleanup e gate

- Run-1 `after_unit_reload_attestation` timeout: nessuna evidenza di causa comune; la race mirata completa il reject/teardown in ~36 s. Il timeout può essere indipendente o un altro waiter, ma non è diagnosticato.
- `300→600`: **REVERTED a 300** insieme al timing sperimentale. Un solo timeout non provava workload legittimo >300 s e l’aumento poteva mascherare sincronizzazione. Production executor deadline/lease/security timeout: **mai modificati**.
- Race matrix eseguita prima dello STOP: continuous mutation durante copy → fail-closed durante inventario e cleanup pulito; stable hostile generated snapshot → graph PID1 hostile, late REJECT, marker absent, teardown pulito; deterministic post-copy create → 3/3 primary mismatch + poisoned, marker absent. Storiche write/atomic/rename/delete/symlink/two-activator/crash restano evidenza precedente ma **non sono state rivalidate dopo una fix**, perché nessuna fix esiste. Tutta la matrice richiesta e targeted adjacent sono BLOCKED dalla stop condition.
- Cleanup per ogni reproducer: fresh container con `/run`/`run/lock` tmpfs; precheck zero state/mount/actor; per poison attesa witness `poisoned=true`, 3 transaction, 4 mount, marker false; poi rimozione exact container. Finale zero container/image targeted, zero mutatore/processo. Immagine baseline storica `pi-pr720-determinism-2:baseline` preservata.
- Un primo invocazione del flag canonico stretto ha emesso automaticamente un record shard-C con SHA sentinel `cccc…`; non è candidate evidence, non è stato aggregato/usato ed è escluso. Nessuna A–F exact candidate/aggregator/full run.
- Static finali dopo revert: `py_compile` activation/integration/fence PASS; Bash runner syntax PASS; `git diff --check` escluso checkpoint PASS.
- Package baseline `/usr/bin/ps`: implementazione locale precedente preservata ma **ancora pre-candidate/non full-gated**; blocker resta aperto. Full canonical/FINAL PASS non eseguito. PR Quality vecchio HEAD resta rosso per drift `/usr/bin/ps`.

### Git e prossimo passo

Worktree intenzionalmente modified/untracked come da sezione baseline; diagnostic script temporaneo rimosso, log `.pi-generated-output-reproducer-{1..5}.log` ignorati preservati. Nessun file production del fence modificato; unico cambiamento di questa fase oltre checkpoint è il revert della precedente sperimentazione timeout, che riporta quella porzione al candidate HEAD. Nessun staged/commit/push; remote invariato.

**Prossimo passo:** decisione/prototipo architetturale in nuova sessione per impedire che output external-writer diventi graph PID1 prima dell’accettazione. Requisiti minimi: writer/output authority distinguibile o generation isolata; rollback manager fail-closed prima di qualunque scheduler/use; nessun unbounded wait; host-lock/crash recovery/lease/source freeze/ABA/seven-slot preserved. Valutare esplicitamente una generation/output namespace controllata o una transazione manager equivalente; non accettare post-hoc cleanup, retry, sleep o semplice LIFO fix come chiusura. Solo dopo un exploit marker/automatic-trigger oracle negativo eseguire la race matrix e targeted adjacent; package baseline/full/A–F restano successivi.

File minimi: `AGENTS.md`, questa sezione, `doc/PILOT_DEPLOYMENT.md:217-225`, `scripts/pilot_ubuntu_activation.py:_attest_systemd_boot_surface/_seal_generated_systemd_output`, `scripts/pilot_trusted_activation_fence.py:SnapshotMountFence.__exit__`, `_test_trusted_activation_fence_races`, log attempt 4.

---

## Generated output authority redesign / physical PoC — BLOCKED su FUSE control-FD alias

- **Data/ora:** 2026-08-30T08:40:55Z.
- **Starting/final state:** branch `fix/oauth-log-redaction-704`; local/upstream/remote HEAD `35fa66080d36018e56465f82ebc56dafc03ebcc7`; PR #720 verificata `OPEN`/`DRAFT`, base `cdcdf4a6`; independent gate `0/2`. Worktree baseline e diagnostiche iniziali preservati byte-for-byte; nessun file production/test/doc modificato in questa unità, nessun add/commit/push/candidate/full/A–F/aggregator/merge.
- **Finding autorevole:** HIGH precedente confermato come requisito: hostile generated output non deve mai diventare graph effettivo PID1. Il MEDIUM teardown nesting resta separato e non è stato modificato.
- **Verdetto:** **GENERATED OUTPUT AUTHORITY POC: BLOCKED**. Il PoC FUSE raggiunge graph ostile zero, ma l’attore canonico duplica l’FD di controllo `/dev/fuse` del broker con `pidfd_getfd`; la writer authority resta quindi raggiungibile tramite un alias `/proc`/FD esplicitamente vietato. Stop condition applicata prima di production migration, crash/two-activator e fix nesting.

### Systemd 255.4 exact

- Source Ubuntu exact scaricata da Launchpad: `systemd_255.4.orig.tar.gz` SHA-256 `96e75bd08c57ad401677456fb88ef54a9f05bb1695693013bc6ecce839640fd5`; `systemd_255.4-1ubuntu8.17.debian.tar.xz` SHA-256 `4695ff34f83b1f7e6e02bf3cfac2e2a44ac76b6cfc5a38c0081bac6919d547bb`; entrambi verificati contro il `.dsc` exact. Le due patch Ubuntu che toccano `manager.c` non modificano il generator/reload path.
- `manager_reload()`: clear jobs/unit → `lookup_paths_flush_generator()` (`rm_rf(...REMOVE_ROOT|REMOVE_PHYSICAL)`) → lookup init → generator environment → `manager_run_generators()` → unit map free → enumerate → deserialize → `manager_coldplug()` → ready/return.
- `manager_run_generators()` crea normal/early/late, poi il system manager usa `(sd-gens)` con `FORK_NEW_MOUNTNS|FORK_MOUNTNS_SLAVE`; `/` è remount RO esclusi `/run`, `/proc`, `/sys`, `/tmp`, `/dev/shm`.
- Argomenti generator exact: normal, early, late. `execute_directories(...EXEC_DIR_PARALLEL...)` enumera una closure name-shadowed, avvia tutti i generator in parallelo e attende ogni PID prima del ritorno. Non esiste callback esterno fra ultimo generator e manager enumeration/load.
- Il PoC ha usato real PID1 `systemd 255 (255.4-1ubuntu8.17)`, exact `/usr/lib/systemd/systemd` SHA-256 `b472aadf808bef87c0eb203056a77cb64bd268b71b756306013a53de68a94173` e un representative generator statico revisionato.

### Threat actor exact

- UID/GID/groups `0:0/0`; `CapPrm=CapEff=CapBnd=000001ffffffffff`, cioè capability 0–40 incluse `CAP_SYS_PTRACE`, `CAP_SYS_ADMIN`, `CAP_LEASE`, `CAP_DAC_OVERRIDE`; `CapInh=CapAmb=0`; `NoNewPrivs=0`; seccomp mode 2.
- Stesso mount namespace di PID1 (`mnt:[4026532477]` nel run finale); proc `rw,nosuid,nodev,noexec,relatime`, nessun `hidepid`; `ptrace_scope=1`, bypassabile dalla capability presente.
- Può chmod/chown/create/truncate/rename/replace/link, mount/remount, bind alias e `setns`. Test namespace privato semplice: `/proc/<generator>/root` write **PASS**, `/proc/<generator>/fd` write **PASS**, `setns` write **PASS**; quindi Option A namespace-only è **FAIL**.
- Esclusioni mantenute: kernel compromise, modifica memoria del trusted process e deliberate fence removal tramite mount administration. Nessuna capability è stata rimossa o ridefinita nel PoC.

### Architetture valutate

| Design | Writer isolation | PID1 compatibility | Alias risk | Verdict |
|---|---|---|---|---|
| A — private mount namespace | no: proc root/fd e setns fisicamente scrivibili | teorica | critica | **FAIL** |
| A — in-memory FUSE per-operation | path/data mutations negate; first PID1 read gated | unit legittima caricata su real reload | broker `/dev/fuse` FD duplicabile | **FAIL/BLOCKED** |
| B — pre-generate/seal/adopt | richiede ancora una costruzione B non aliasabile | systemd 255 non ha adopt API; ogni reload flush+regenerate | mount-root/error-ignore sarebbe trick non supportato | **REJECTED/UNPROVEN** |
| C — post-load manager barrier | nessuna barriera hard esterna | manager enumera/deserializza/coldplugga prima di restituire | timer/path/socket/restart/D-Bus non onorano il lock | **FAIL** |
| D — kernel/LSM o broker fuori dal PID namespace dell’attore | potenzialmente sì | non baseline corrente | richiede nuovo platform boundary | **DECISIONE ESTERNA** |

### Selected disposable PoC e authority proof

- Representative generator statico, no PT_INTERP/PT_DYNAMIC, SHA-256 `90d807cec564c465d47b49dd754cdd3a7ea6897ed94d4e1127e43d1971c7b220`; exact path/name/argv; exact 12-key environment e valori; lineage `generator → sd-exec-strv → sd-gens → PID1`; underlying systemd SHA exact. Output capability chiusa al solo `normal/review704-legit.service` e ai byte unit exact.
- Broker FUSE statico, no PT_INTERP/PT_DYNAMIC, SHA-256 `cb8012b7cda6422bf2df8ef4c99acaeddeff9a1e33e700de77fd5ad5bf6221d9`; tree interamente in memoria, nessun backing filesystem alias; normal/early/late sono bind di subroot della stessa authority.
- Il broker autorizza ogni mutation dal PID FUSE corrente, non da UID/DAC; valida exe SHA, parent chain, argv, environment e path/content capability. Prima lettura PID1 dopo generation blocca, chiude inventario e contenuto, passa a sealed, poi rilascia la syscall.
- Timeline monotonic finale: broker begin `49438.242730741`; generation authority open `49440.901339184`; first PID1 graph read blocked `49442.420460826`; seal begin `49442.424898114`; seal complete `49442.424915017`; first PID1 graph read released `49442.424917017`. Nessun byte unit è stato restituito a PID1 prima del seal.

### Matrici e manager oracle

- Pre-seal: 29 mutation negate attraverso normal/early/late, direct path, hidden path, alternate bind, same-inode write/truncate, rename/unlink, mode/owner, preopened dir FD, proc root, proc FD, setns, standalone timer/path/socket/service e drop-in su scheduler attivi.
- Post-seal: altre 13 mutation negate: create/write/truncate/atomic replace/unlink/rename/mkdir/symlink/hardlink/chmod/chown, preopened dir FD e hidden alias. Closed inventory finale: tre directory + un solo regular legittimo root:root 0644, SHA-256 `799b41b489a740041ef9a35cf48f66d2485c8d5c790b1d30c2ec04f27bf94ba5`.
- Manager hostile: nginx `FragmentPath=/usr/lib/systemd/system/nginx.service`, `DropInPaths=` vuoto, `ExecStartPost=` vuoto; quattro scheduler service senza drop-in; hostile service/timer/path/socket tutti `LoadState=not-found`; dependency count hostile `0`; hostile marker **ABSENT**.
- Legitimate: `review704-legit.service` loaded da `/run/systemd/generator/review704-legit.service`, exact ExecStart; start reale PASS e marker legittimo **PRESENT**.
- Timer/path/socket/restart fixture erano attivi prima del reload e hanno prodotto eventi trusted; un caller indipendente ha emesso real `systemctl start nginx.service` durante la finestra. Le fixture aggressive hanno poi raggiunto alcuni start-limit, ma nessuna ha visto graph hostile. Questo conferma che tali superfici consumano il graph e non costituiscono una barriera Option C.

### Alias blocker exact

- `/proc/<generator>/fd/4` direct write è stato negato dal PID-aware broker. Tuttavia `pidfd_open(generator)+pidfd_getfd(...,4)` ha restituito **SUCCESS**, dimostrando la duplicabilità degli FD del trusted writer; il write avrebbe ancora attraversato FUSE e sarebbe stato attribuito all’attore.
- Più grave: broker PID 174, FUSE FD 3; `pidfd_getfd` ha restituito **SUCCESS** e l’apertura `/proc/174/fd/3` è riuscita. L’FD duplicato è la connessione FUSE completa: consente a un mutatore con le capability dichiarate di leggere/rispondere al protocollo kernel, non soltanto di invocare un path mediato. È writer/control authority esterna al controllo del broker.
- Non è process-memory modification né deliberate unmount; ricade direttamente nella matrice `/proc/pid/fd` richiesta. Rendere non-dumpable non basta contro `CAP_SYS_PTRACE` nello stesso user namespace. Il PoC è quindi **BLOCKED** anche se il particolare payload path-level è stato negato.

### Residuo e cleanup

- Crash phases, two activators e port production: **NOT RUN**, perché il prerequisite writer isolation è fallito. Nessuna candidate è stata creata.
- MEDIUM nesting teardown: invariato; primary deve restare underlying generated-output mutation e parent LIFO, ma il fix è rimandato fino a un’architettura HIGH valida.
- Package baseline `/usr/bin/ps`: remediation locale deterministica preservata, ancora pre-candidate/non full-gated; blocker separato aperto.
- Evidence concise esterna: `F:/dev/.pi-generated-authority-final-attack-results.log` SHA-256 `92c19096fa2faedb2ea45a44f393b6f6cea53578f79f8721c0431a9527550634`; broker timeline `F:/dev/.pi-generated-authority-final-broker.log` SHA-256 `9213b989d8ee8f0eb74160584f1635dec024fc1029ebd149c00fc7ac796d3d90`. Disposable source/binaries restano fuori dal worktree in `F:/dev/.pi-generated-authority-poc`; exact source in `F:/dev/.pi-systemd-255.4-source`.
- Tutti i container/processi/mount PoC e l’image builder sono rimossi. La sola image storica preesistente `pi-pr720-determinism-2:baseline` è preservata. `git diff --check -- . ':!CHECKPOINT.md'` PASS.
- Git finale coincide con lo stato iniziale salvo questo append al checkpoint: HEAD/remote `35fa6608`, nessun staged/commit/push; PR `OPEN`/`DRAFT`; gate `0/2`.

**Prossimo passo:** decisione architetturale separata. Non portare FUSE in production e non ripetere la matrice path-level. Serve una primitive per-operation la cui control authority non sia duplicabile dall’attore exact, oppure un nuovo platform boundary esplicitamente approvato (kernel/LSM o broker realmente fuori dal PID/user namespace dell’attore) senza indebolire il threat model. Solo dopo un nuovo PoC che includa `pidfd_getfd` negativo/non-authoritative si può riprendere HIGH, poi MEDIUM nesting, package baseline e gate finali.

File minimi alla ripresa: `AGENTS.md`, questa sezione, le tre sorgenti systemd exact esterne (`manager.c`, `exec-util.c`, `generator-setup.c`) e i due evidence log; consultare production fence/activation soltanto dopo la decisione sulla primitive.

---

## Stock systemd generator orchestrator / seal-adopt PoC — PASS

- **Data/ora:** 2026-08-30T10:34:42Z.
- **Starting/final Git:** branch `fix/oauth-log-redaction-704`; local/upstream/remote feature `35fa66080d36018e56465f82ebc56dafc03ebcc7`; PR #720 `OPEN`/`DRAFT`; independent gate `0/2`. Worktree pre-candidate package-baseline e checkpoint integralmente preservato; nessun file production/test/doc modificato, nessun add/commit/push/candidate/merge.
- **Verdetto:** **STOCK SYSTEMD GENERATOR ORCHESTRATOR POC: PASS**. Nessun PID1 custom e nessun Yama/LSM/threat-model change. Il precedente finding FUSE control-FD resta autorevole e non è stato indebolito: questa architettura non usa FUSE né authority segreta.

### Semantica e inventario exact

- Noble exact `systemd 255.4-1ubuntu8.17`. Search priority: `/run`, `/etc`, `/usr/local/lib`, `/usr/lib` system-generators; basename first-wins; zero-length o `/dev/null` in prior directory masks lower. Probe fisica empty mask: lower marker ABSENT; rimozione empty: PRESENT. `/etc/.../systemd-gpt-auto-generator -> /dev/null` maschera il package artifact.
- Undici inner generator package selezionati: cryptsetup, debug, fstab, getty, hibernate-resume, integritysetup, rc-local, run, system-update, sysv, veritysetup. Exact path/SHA in `F:/dev/.pi-generator-orchestrator-poc/selected-generators.tsv` (SHA file `c958d13f85131a8c460d4cf1454c6e21a225329819d916200787ef3825385dcd`).
- Stock usa `EXEC_DIR_PARALLEL|EXEC_DIR_IGNORE_ERRORS|EXEC_DIR_SET_SYSTEMD_EXEC_PID`, aspetta tutti, argv normal/early/late, cwd `/`, umask `0022`, soli FD 0/1/2 osservati, environment chiuso di 12 chiavi. Il sandbox `(sd-gens)` è un mount namespace slave e remounta `/` RO salvo `/sys,/run,/proc,/dev/shm,/tmp`.
- Reload exact: flush generated roots, generator, free map, enumerate, deserialize, coldplug. Flush `rm_rf(REMOVE_ROOT|REMOVE_PHYSICAL)` ignora errori. SAFE-EMPTY tmpfs RO su normal/early/late sopravvive fisicamente al flush; daemon-reload rc 0 e roots vuote/RO.

### Architettura provata

- Sole source entry: orchestratore statico SHA `ef469fdfe1906c6151b559a369ff27135985b359f22802ef4ebd0b94126418f7`, zero PT_INTERP/dynamic section; 12 mask `/dev/null`; source tree e lower snapshot RO/closed.
- Un tmpfs transaction-specific contested con `normal/early/late`; tutti gli 11 generatori exact lanciati in parallelo con environment, `SYSTEMD_EXEC_PID`, PDEATHSIG, RLIMIT, cwd, umask, stdio ed exit handling stock-equivalent.
- Helper non-secret nel mount namespace PID1: apre una volta l'exact mount staging e registra mount ID/device/source; remount superblock RO attraverso stable dir FD; normalizza e prova ogni alias nel namespace autorevole VFS+superblock RO; inventory FD-relative/no-follow completa; crea detached handle soltanto dopo PASS con `open_tree(OPEN_TREE_CLONE)` e adotta ogni subroot atomicamente con `move_mount(F_EMPTY_PATH|T_EMPTY_PATH)`.
- Nessun FD/token/socket conferisce unchecked adoption: pre-seal espone soltanto staging pubblicamente RW; post-seal e detached mount handles riferiscono soltanto output attestato RO. Caller arbitrario può causare solo valid output, old/safe output o DoS.
- Attestazione pristine chiusa: sole due symlink package getty/remount e relative directory; early/late vuote; tipo/topologia/mode/uid/gid/target esatti. Ogni regular/drop-in/unit execution authority è vietata in questo stato reviewed e fallisce chiusa.

### Evidenze

- Stock vs orchestrated: tree normal byte/topology-equivalent, early/late empty; `getty.target Wants=console-getty.service`, `local-fs.target Wants=systemd-remount-fs.service`; tutti gli 11 child rc 0.
- Hostile staging: service con tutti i sette Exec, timer/socket/path/mount/automount/target, drop-in, wants, same-inode, atomic, unlink/recreate, symlink/hardlink, metadata, dirfd/openat, bind alias, `/proc/root`, `/proc/fd` e `setns` scritti con successo; superblock/alias sigillati RO; inventory REJECT; adottato NO. PID1: nginx DropInPaths/ExecStartPost vuoti, hostile unit/scheduler `not-found`, dependencies 0, marker ABSENT, old validated stock ancora visibile.
- Seal: O_RDWR preaperto rende remount `EBUSY` e quindi DoS sicuro/no adoption. Dopo seal riuscito, pre-open RO file/dir FD e path/alternate bind non possono write/create/truncate/rename/unlink/chmod/chown/symlink/hardlink (`EROFS`).
- SIGKILL orchestrator a 12 seam: before staging; inner run; after last child; before/during seal; post-seal/pre-attest; during attest; post-attest/pre-adopt; dopo prima/seconda/terza adoption; post-adoption/pre-exit. Ogni daemon-reload rc 0 ma output sempre OLD VALIDATED o NEW VALIDATED, graph hostile `not-found`, marker ABSENT. Partial proof device: `NEW/OLD/OLD`, `NEW/NEW/OLD`, `NEW/NEW/NEW`.
- Non-cooperating root daemon-reload senza PREPARED: rc 0, orchestrator exit fail-closed, stesso device/output validated, graph stock, marker absent.
- Source attacks: remove/replace orchestrator, add run/lower generator, mask replacement, lower rename, absent fill e same-name visible write DENIED. Writer preaperto ha mutato solo lower hidden; SHA PID1-visible reviewed invariato.
- Evidence canonica PoC esterna: `F:/dev/.pi-generator-orchestrator-poc/REPORT.md` SHA `6d2a713a9d034516493e87a66449f42853b2d39e4948d8881032c3d5c43c09cd`; attacked log SHA `5d0104e5326a56da1fca0febc1827223751f57f61a9e79fb992db2a5b71fb48a`; kill matrix SHA `7733b96e43d5f35caf7555171e55e652ef81408b961c869523a213dc69f406ff`; partial adoption SHA `9bceaa38036cd23c2d36b0a84f1073cac2a5260f06647b95f4c9716685146e51`.

### Cleanup, blocker residui e prossimo passo

- Zero container/image PoC disposable, zero mutator/helper/mount/staging/safe/adopt residuo; Docker healthy, zero container running. Image storica preesistente `pi-pr720-determinism-2:baseline` preservata.
- MEDIUM nested teardown invariato e ancora visibile; non corretto. Package baseline `/usr/bin/ps` preservata localmente e ancora pre-candidate. Full canonical, A–F e aggregator non eseguiti. Gate `0/2`; DO NOT MERGE.
- **Next:** nuova sessione AUTHOR/PORT per portare il meccanismo provato nella TrustedActivationFence senza broad rewrite, integrare semantic attestation production per gli stati supportati, poi completare package baseline e gate developer. Solo dopo candidate/push e fresh independent review.
- **File minimi:** `AGENTS.md`, questa sezione, report esterno; poi `scripts/pilot_trusted_activation_fence.py`, `_attest_systemd_boot_surface/_seal_generated_systemd_output` in `scripts/pilot_ubuntu_activation.py` e gli attuali test race, ampliando soltanto per il port.

---

## PR720 — production generator orchestrator port / targeted security gate — PASS

- **Data/ora:** 2026-08-30T17:41:01+02:00.
- **Starting/final immutable remote SHA:** `35fa66080d36018e56465f82ebc56dafc03ebcc7`; branch `fix/oauth-log-redaction-704`; local/upstream/remote feature coincidono. PR #720 `OPEN`/`DRAFT`, `MERGEABLE/UNSTABLE`; independent gate `0/2`. Nessun commit/push/candidate/mark-ready/merge.
- **Obiettivo/stato:** portare il PoC stock-systemd seal/adopt nella production TrustedActivationFence e chiudere gate mirato, cross-root e nested teardown. **PRODUCTION GENERATOR ORCHESTRATOR TARGETED GATE: PASS.** Full canonical, A–F candidate e aggregator non eseguiti.
- **PoC authority:** `F:/dev/.pi-generator-orchestrator-poc/REPORT.md`, SHA-256 `6d2a713a9d034516493e87a66449f42853b2d39e4948d8881032c3d5c43c09cd`; architettura FUSE precedente resta rifiutata e non è stata portata.

### Worktree/hunk inventory e separazione

- Inventario iniziale prima di modifiche: tutti gli hunk di `.dockerignore`, `.gitignore`, `deploy/pilot/ci/Dockerfile.ubuntu-systemd`, `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_private_runtime_evidence.py`, `scripts/pilot_ubuntu_integration.py`, `scripts/run_pilot_ubuntu_integration_container.sh`, `tests/test_pilot_deployment.py` e i tre untracked `deploy/pilot/ci/isrg-root-x1.pem`, `deploy/pilot/ci/ubuntu-systemd-package-baseline.json`, `scripts/pilot_ubuntu_package_baseline.py` erano `PACKAGE_BASELINE`; `CHECKPOINT.md` era `CHECKPOINT`; zero `ORCHESTRATOR_PORT/OTHER_EXISTING/GENERATED/DIAGNOSTIC` dirty path.
- Stato finale `PACKAGE_BASELINE` esclusivo: `.gitignore`, `scripts/pilot_private_runtime_evidence.py`, i tre untracked baseline. `ORCHESTRATOR_PORT` esclusivo: `scripts/build_pilot_toolchain.py`, `scripts/pilot_static_bootstrap.go`, `scripts/pilot_toolchain_launcher.py`, `scripts/pilot_trusted_activation_fence.py`, `scripts/pilot_ubuntu_activation.py`, nuovi `scripts/pilot_systemd_generator_orchestrator.go/.py`. `CHECKPOINT`: questo file.
- File misti con hunk baseline preesistenti + hunk orchestrator separati: `.dockerignore`, `deploy/pilot/ci/Dockerfile.ubuntu-systemd`, `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_ubuntu_integration.py`, `scripts/run_pilot_ubuntu_integration_container.sh`, `tests/test_pilot_deployment.py`. Nessun hunk package-baseline è stato rimosso, riscritto o promosso; i shared file hanno ricevuto sole aggiunte/modifiche architecture-specific.
- Nessun file staged. **CHECKPOINT COMMIT BLOCKED BY MIXED WORKTREE HUNKS**: non usare `git add -A/.`; preservare tutto per la successiva unità package-baseline/final gate.

### Production source/build e inventory selection

- Nuova source authority statica Go: `scripts/pilot_systemd_generator_orchestrator.go`; canonical source SHA-256 `69916ddab297cf3f2935d7be60c9c7f9f89515d73805ee694c85e3dd986d23e8`.
- Build pinned Noble Go 1.22: `CGO_ENABLED=0 GOOS=linux GOARCH=amd64`, `-trimpath -buildvcs=false -ldflags='-s -w -buildid='`; artifact SHA-256 `7e5c3d164975a8def99a815477a3db440821557e9543452eed60bcc32a96308f`. Build cached e build indipendente `--no-cache` hanno prodotto lo stesso SHA. `file`: static stripped; PT_INTERP assente; dynamic section assente.
- Coordinatore production reviewed: `scripts/pilot_systemd_generator_orchestrator.py`, incluso nel manifest chiuso toolchain, launcher e static bootstrap.
- Sole selected entry: `/etc/systemd/system-generators/thebitlab-generator-orchestrator -> /usr/sbin/thebitlab-systemd-generator-orchestrator`. Dodici mask exact `/dev/null` in `/etc`: gli 11 inner più `systemd-gpt-auto-generator`. Nuova entry inattesa, expected-absent fill, missing expected, mask/orchestrator drift: fail-closed.
- Undici inner exact, package identity `systemd=255.4-1ubuntu8.17:amd64`, classe `parallel-ignore-child-exit`, presenza obbligatoria: `systemd-{cryptsetup,debug,fstab,getty,hibernate-resume,integritysetup,rc-local,run,system-update,sysv,veritysetup}-generator`; path e SHA sono in `SELECTED_GENERATORS` e duplicati/verificati nella source Go.
- Equivalenza stock: tutti i child vengono avviati prima del primo wait; argv normal/early/late transaction-specific; cwd `/`; umask `0022`; ambiente exact 12 chiavi; soli stdio non-CLOEXEC; `SYSTEMD_EXEC_PID` del child; PDEATHSIG; child exit ignorato. Differenza deliberata: launch failure dopo inventory PASS blocca adoption invece di essere ignorata.

### Safe output, staging, seal, manifest, adoption

- Provisioning esplicito installa SAFE-EMPTY filesystem-RO sui tre target prima della fase operativa ostile. Production reload rifiuta di iniziare se i root correnti non sono già RO e conformi alla closed policy.
- Un tmpfs dedicato per token pubblico contiene `normal/early/late`; generator e attacker scrivono soltanto staging. Transaction token/socket/FD non sono segreti né bearer capability.
- Helper forkato nel namespace PID1 apre stage una volta, lega mount ID/device/source/inode, remounta l'intero superblock RO da FD stabile, normalizza tutte le alias VFS e richiede `ro` sia mount sia superblock. Writer O_RDWR preaperto produce `EBUSY`, no adoption, vecchio graph invariato.
- Inventory FD-relative/no-follow lega root class, topology, type, mode, uid/gid, SHA regular, symlink target; hardlink, nested mount/cross-device, special object e regular/drop-in/unit fuori policy sono rifiutati. Baseline closed: normal con sole due symlink getty/remount e directory; early/late vuote.
- Detached `open_tree` handles sono creati soltanto dopo PASS; `move_mount` usa exact target FD. Nessun `attest path A → reopen pathname`.
- Bundle ID pubblico lega selected inventory, source policy, package-baseline placeholder/current identity, tre manifest, combined effective graph, seal/alias evidence e adoption order. Manifest content e mount source/token distinguono bundle/generazioni anche con byte uguali.
- Recovery rimuove soltanto staging canonicale già detached, FD-relative/no-follow e senza mount nested; adopted clone resta valida. Cleanup hostile/reject e retry fisico PASS.

### Cross-root generation consistency

- Precedence exact: `generator.early → generator → generator.late`; adoption inversa: `late → normal → early`.
- Prefissi fisicamente raggiungibili: `OLD/OLD/OLD`, `OLD/OLD/NEW`, `OLD/NEW/NEW`, `NEW/NEW/NEW` nell'ordine early/normal/late. Tutti vengono costruiti e passano la stessa closed generated-contribution/effective-graph policy **prima** del primo move.
- Fixture sintetica multi-root: OLD early seleziona un guard che override un normal ostile; NEW normal cambia guard; NEW late aggiunge dependency. OLD e NEW exact passano; il prefisso OLD-early/OLD-normal/NEW-late non revisionato viene rifiutato prima dell'adoption. Test unitario PASS; prova che la strategia B blocca, non presume indipendenza.
- Matrice fisica production 12 seam registra mount ID/device/root/manifest dei tre root e combined graph SHA `63f111e05eb50a5622dab2b856a925b802b632f66c85fe324bea68e1bee38871`. Dopo prima adoption cambia solo late; dopo seconda normal+late; dopo terza tutti. Ogni manager oracle hostile `not-found`, marker absent.

### Attacchi fisici mirati

- Hostile staging finale: **115 cicli di scrittura riusciti** con nginx drop-in, tutti sette Exec slot, service/timer/socket/path/mount/automount/target e wants. Seal completato, closed attest REJECT, adoption NO. PID1: tutti i sette hostile `not-found`; nginx `DropInPaths=''`, `ExecStartPost=''`; marker ABSENT.
- Post-seal: create/write/truncate/atomic replace/unlink/rename/mkdir/symlink/hardlink/chmod/chown/fchmod/fchown/openat e preopen RO file write tutti negati (`EROFS`, solo write su FD O_RDONLY `EBADF`). Held O_RDWR: `EBUSY` safe availability failure.
- Direct invocation: wrong argv rc 2; exact argv senza PREPARED rc 1; nessun generic mount/helper CLI. Request arbitraria può al massimo far attestare/adottare exact valid output o DoS. State/token/replay non autorizzano pathname/mount arbitrari.
- Non-cooperating root `daemon-reload`: rc 0 stock semantics, orchestrator senza PREPARED fallisce chiuso, mount/root/effective identities invariati, hostile graph assente.
- Source/mask race: add `/run`, remove/replace orchestrator, remove/replace mask, add/rename lower, gpt/expected-absent fill, same-name package replace/write/unlink tutti denied dalla source fence; preopened lower può toccare solo hidden lower. H-03/H-04/H-05 restano chiusi.
- Due activator reali + dpkg lock: host-global bounded serialization PASS; nessun mixed staging/bundle, deadlock o cleanup residuo.
- 12 seam: before staging; during inner generation; after child exit; before/during seal; after seal; during/after attestation; before first move; after first/second/third move. Ogni effective graph prevalidato, manager hostile assente, marker absent.

### Nested teardown MEDIUM e regressioni storiche

- Il vecchio nested `trusted-systemd-generated-output` non è più nel production path. Fix generico `SnapshotMountFence.__exit__`: verifica LIFO **prima** di validation/teardown parent; se un child poisoned resta in cima, parent non viene rimosso; con eccezione primaria in propagazione restituisce `False` e non emette `Nesting fence divergente` mascherante.
- Regressione exact: primary `Underlying mutato durante fence; protezione lasciata attiva: child`; child e parent retained; `_remove_transaction(parent)` non chiamato; poison retained. PASS.
- H-01/H-02 / R1 preload+hwcaps: gate fisico `--bootstrap-adversarial-only` PASS, static bootstrap crash matrix PASS, 735 hwcaps expected-absent, closure selectable non pinnata zero.
- H-03 exact foreign Replaces/Provides known FragmentPath: REJECT + pristine restore PASS. H-04 exact `/usr/bin/kmod` expected-absent package-valid fill: REJECT + restore PASS. H-05: systemd same/higher, Accept, timer, procps same/higher, bash, grep, nginx e systemd-generator malicious package-valid bytes tutti REJECT; root marker absent; pristine PASS.
- Generator ABA, nginx binary/module preopen TOCTOU, second daemon-reload e late nginx seven-slot Exec contract: physical PASS.

### Test/static/cleanup

- Final dedicated physical command: `GITHUB_SHA=35fa... GITHUB_RUN_ID=pr720-production-orchestrator-final2 bash scripts/run_pilot_ubuntu_integration_container.sh --generator-orchestrator-gate-only` → **PASS**. Zero `PRIVATE_RUNTIME_SHARD_EVIDENCE`; un solo cleanup witness container/image absent. Non è A–F candidate evidence.
- Physical bootstrap targeted: PASS. Physical production orchestrator transactions, hostile graph, EBUSY, post-seal, direct invocation, noncooperating reload, 12 seam, source/mask, two activators, H-03/04/05: PASS.
- `tests/test_pilot_deployment.py` Python 3.12: **240 total = 205 PASS + 35 expected SKIP**, zero failure/error. Include source/inventory/prefix fixture/LIFO regression.
- `py_compile` production/integration/toolchain/baseline modules, Bash syntax runner, `git diff --check` escluso checkpoint: PASS.
- Go no-cache static build, source SHA, deterministic artifact SHA, PT_INTERP e dynamic-section checks: PASS.
- Docker finale: zero container/image `thebitlab-pilot-ubuntu-systemd-integration` o `pi-pr720-orchestrator`; processi/helper/mutator temporanei zero. Image storica `pi-pr720-determinism-2:baseline` preservata.
- Full canonical, A–F candidate, aggregator e independent review: **NON ESEGUITI**. I record shard C emessi automaticamente durante diagnostiche preliminari col vecchio flag sono stati rimossi e non sono evidence candidate; il run finale dedicated ne emette zero.

### Findings, package baseline, Git e prossimo passo

- HIGH nuovi: 0. MEDIUM nuovi: 0. LOW nuovi: 0. INFORMATIONAL aperti: 0. Generated output authority HIGH: CLOSED. Nested teardown MEDIUM: CLOSED.
- Package baseline: remediation `/usr/bin/ps` e hunk correlati **PRESERVED / STILL PRE-CANDIDATE**. I test H-05 procps hanno ripristinato pristine ma non costituiscono package-baseline finalization o candidate PASS.
- Commit/push: nessuno. Decisione: **CHECKPOINT COMMIT BLOCKED BY MIXED WORKTREE HUNKS**. Remote feature invariato `35fa6608`; PR resta OPEN/DRAFT; gate `0/2`; DO NOT MERGE.
- **Next work unit:** `PACKAGE BASELINE FINALIZATION + FRESH FULL CANONICAL DEVELOPER GATE + A–F + AGGREGATOR + NEW CANDIDATE SHA + EXACT-HEAD CI`. Leggere inizialmente questa sezione, l'inventario hunk e i soli file baseline/shared pertinenti; non rifare il PoC né il gate orchestrator salvo una modifica che lo invalidi.


---

## PR720 — current main integration + package baseline rebind — PRE-CANDIDATE PASS

- **Data/ora:** 2026-08-30T19:28:25+02:00.
- **Starting feature/local/remote:** `35fa66080d36018e56465f82ebc56dafc03ebcc7`; old integrated main `cdcdf4a6c9a3b1e28cc0a9702ca4f69a521849b0`; frozen current main `29c90735a842738c67b798e97b2e5b00696b5e25` (67 commit). PR #720 OPEN/DRAFT; independent gate `0/2`.
- **External dirty evidence:** `F:/dev/2cornot2c-704-evidence/pr720-dirty-35fa6608-20260830T163933Z`; 19 modified/untracked files, zero staged; `CHECKPOINT.md` original SHA-256 `99e99dbd7c32fcf6436c73bbf7625da77ffb61e94a261c2ba66e823ed9052851`; binary patch SHA-256 `1a58f6d02793d14e2b659f0f1c03388410dab63cae2a0d51b6f07a3cdc2a0ea8`. Exact base checkout + byte copies reproduced all size/SHA and identical porcelain-v1-z; temporary reconstruction removed. Original canonical worktree `F:/dev/2cornot2c-704` remains untouched.

### Incoming delta e integrazione

- Delta inventory: 44 path, 7066 insertions/63 deletions. Grading core 11; assignment-runner Dockerfile 1; toolchain identity 2; CI/publication 6; shared/tests 22; docs 2. P2 function, P3 object, P4 filesystem, combined dispatch/image, publication and release-lock semantics preserved.
- Exact rehearsal: detached ephemeral local-only commit `f4030543713d67a5dc81ebf46dcd8ee5dfa2be3f`; normal `--no-ff --no-commit` merge; zero conflicts/unmerged index. It was never candidate/pushed and its worktree was removed.
- Final integration worktree: `F:/dev/2cornot2c-720-current-main`, local branch `integration/pr720-current-main-29c90735`; normal merge commit `d32aa9d9269875f91202dd4dde7ad019d8e38b05`, parents exact `35fa6608` + `29c90735`.
- Dirty snapshot was then applied with 19/19 exact size/SHA. Pre-commit comparison: 15 files remain byte-exact; only `.dockerignore`, `doc/PILOT_DEPLOYMENT.md`, `scripts/pilot_systemd_generator_orchestrator.py`, `tests/test_pilot_deployment.py` have intentional adaptation; missing snapshot paths zero. `.dockerignore` is the semantic union of all private-runtime/generator inputs and all six P2/P3/P4 profile/worker inputs.

### Current-main runner authority e coupling

- Assignment runner manifest: `thebitlab.grading-toolchain-build.v1`, version `2026.08.3`, platform `linux/amd64`, Debian base `sha256:7b140f...`, snapshot `20260713T000000Z`; combined P2/P3/P4 worker inventory present.
- Published lock: source revision `23bc1d36c7eb8c1b10a11cbde5f226ce7554f85e`; immutable GHCR `ghcr.io/thebitpoets/2cornot2c-assignment-runner@sha256:c0594df833925044831463a9ee631aba2688929951a7dbcb53612b86d221ed51`.
- Publication contract: PR validates contracts/build/Docker Student Lab; publish job main-only; automatic push trigger only on `docker/assignment-runner/toolchain.json`; immutable release evidence required.
- Coupling decision: OAuth activation does not execute/incorporate assignment-runner bytes. Pilot `TOOLCHAIN_FILES`, policy digest and private-runtime aggregator are a separate Ubuntu domain. They bind candidate, pilot policy/toolchain, Ubuntu OCI/snapshot/package identities, not the Debian assignment lock. This boundary is now canonical in `doc/PILOT_DEPLOYMENT.md`; no ambiguous `latest` introduced.

### Deterministic Ubuntu package baseline

- OCI: `ubuntu@sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea`; source `https://snapshot.ubuntu.com/ubuntu/20260822T000000Z`; archive signatures remain required; reviewed ISRG X1 certificate SHA-256 `22b557...`.
- Baseline manifest SHA-256 `35dba57876cd9e9daee5a8f251fffa4e5e820c6edee95637533c4aadb45b05fb`; runtime package inventory 144 entries, SHA-256 `fb412411b0c438b04a3633b0135ef1300c77ec0e3fcebf1bf006ddd6737c2c26`; all direct packages exact-version pinned.
- Two independent snapshot-index acquisitions: 20 apt-list files, exact set identity `5697f5502a9249c8dbb76acaba6c067d074e355cc179c69befb2b5afa9e582a5`, files/digests identical. Full inventory is external evidence `snapshot-index-identity-[12].json`.
- `/usr/bin/ps`: realpath `/usr/bin/ps`; owner/source `procps`; version `2:4.0.4-4ubuntu3.2`; architecture `amd64`; status `ii `; size 146424; SHA-256 expected=actual `8e86f498aa4aabfcea6c179d6181557140b4597f1c39bb94e2aba32158b58297`; class `NATIVE_PACKAGE_BINARY`. `/usr/lib/x86_64-linux-gnu/libproc2.so.0.0.2` expected=actual `f2b9...`.
- Complete behavior-bearing comparison: the selected deterministic baseline reproduces the old reviewed bytes exactly. Across 418 repository-reviewed native/package files and 11 selected generators, changed reviewed closure is empty; policy hashes did not accept newer bytes. The only finalization change is binding orchestrator audit identity to exact baseline manifest `35dba...` instead of a timestamp placeholder/environment override.
- Determinism build 1: local image ID `sha256:1cd69b...`; build 2 `sha256:4b1c50...` (non-behavior build metadata differs). Both have identical OCI/source/versions, package inventory, ps identity, four static artifact hashes and behavior closure SHA-256 `b0e21e1d946a0b8e796af8d4f6ec87ab31c22609d019cd6383fa9c51f44af0a6`. **CANONICAL PACKAGE BASELINE: PASS.** No dynamic/generated trust.

### Regressioni e H-05

- Current-main Linux Python 3.12: 132/132 P2/P3/P4 contract/worker/dispatch/redaction/integration/build/lock/release/workflow tests PASS. Linux Python 3.11: 132/132 PASS. Windows run had one informational CRLF-only P4 byte-count mismatch; authoritative Linux run PASS.
- Combined runner build PASS: version `2026.08.3`, local image `sha256:87e3ffd...`, exact Debian snapshot/packages, all six P2/P3/P4 profile/worker files. Legacy+P2+P3+P4 Student Lab Docker: 12/12 PASS. Build/lock/release focused subset: 29/29 PASS.
- Pilot deployment full before final negative expansion: Python 3.12 and 3.11 each 205 PASS + 35 expected SKIP. Package/aggregator focused after explicit wrong-toolchain-ID, wrong-OCI and cleanup-false cases: 19/19 on each version.
- Physical H-05 after current-main: systemd same/higher, Accept, timer, procps same/higher, bash interpreter, grep runtime command, nginx binary and systemd generator all package-valid malicious bytes REJECT; pristine reviewed baseline PASS; marker absent. H-03 foreign Replaces/Provides REJECT; H-04 expected-absent kmod fill REJECT.

### Production orchestrator re-attestation e static

- Fresh no-cache command: `GITHUB_SHA=d32aa9d... GITHUB_RUN_ID=pr720-current-main-orchestrator bash scripts/run_pilot_ubuntu_integration_container.sh --generator-orchestrator-gate-only` → **PASS**. This is targeted pre-candidate evidence, not A–F candidate evidence.
- Selected source/masks, direct invocation/confused deputy, non-cooperating reload, EBUSY safe failure, 15 post-seal classes, two activators/dpkg lock, nested teardown, H-01..H-05, generator ABA, nginx TOCTOU and late seven-slot Exec remain closed. SIGKILL 12/12 PASS; hostile staging 115 successful writes → attest REJECT → adoption NO → hostile PID1 graph zero → marker ABSENT.
- Static: 277 Python files py_compile PASS; 15 tracked Bash files syntax PASS; Sphinx 8.2.3 `-W --keep-going` PASS; course-plan check PASS; `git diff --check` PASS.
- Four production Go binaries enumerated: `thebitlab-pilot-activate` SHA `a4337348...`, `thebitlab-private-runtime` `35258408...`, PoC `a1fd9115...`, generator orchestrator `7e5c3d16...`; each CGO-free/static, PT_INTERP=0, dynamic section=0.
- Cleanup: all current-session pilot/determinism/assignment-runner/Python test images removed, zero running/current-session containers, Sphinx/pytest/uv debris removed. Historical `pi-pr720-determinism-2:baseline` preserved.
- Findings: new HIGH 0, MEDIUM 0, LOW 0. Full canonical/A–F/Shard F/aggregator exact-candidate gate still pending. Gate remains `0/2`; DO NOT MERGE.
