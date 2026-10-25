# Installazione manuale di VMware Fusion e della VM

Questa è la procedura di riserva per gli studenti quando l'installer automatico
non può completare il download della macchina virtuale.

## Compatibilità

La macchina fornita in questa directory usa Ubuntu 24.04 ARM64 e funziona
soltanto sui Mac con processore Apple Silicon. Non può essere avviata su Mac
Intel o su PC Windows.

Servono almeno 8 GiB di RAM e circa 20 GiB di spazio libero. La VM usa 4 GiB di
RAM, 2 CPU e un disco virtuale che può crescere fino a 64 GiB.

## 1. Scaricare e installare VMware Fusion

VMware Fusion non viene redistribuito insieme alla macchina virtuale. Ogni
studente deve scaricarlo dal portale ufficiale Broadcom:

1. apri la [guida ufficiale Broadcom](https://knowledge.broadcom.com/external/article/368734/download-desktop-hypervisor-workstation.html);
2. registra un account Broadcom Basic oppure accedi;
3. completa i dati richiesti per il controllo Export Compliance;
4. apri **My Downloads**, seleziona **Free Software Downloads available HERE**
   e cerca `Fusion`;
5. scarica la versione più recente compatibile con macOS e Apple Silicon;
6. apri il file DMG e trascina **VMware Fusion** in `Applicazioni`;
7. avvia Fusion una volta e accetta licenza, autorizzazioni e richieste di
   sicurezza di macOS.

Il DMG usato per il collaudo è
`VMware-Fusion-26H1-25388279_universal.dmg`. La sua impronta SHA-256 è:

```text
c1d373aa21be25674e3ecc518819e255785dea9d456d8747bcb0a2a59244bdf6
```

Il nome e il checksum servono soltanto per riconoscere quella specifica copia:
una versione più recente scaricata dal portale avrà un'impronta diversa.

## 2. Verificare la VM ricevuta

Il docente distribuisce questo file separatamente dal repository Git:

```text
2cornot2c-Ubuntu-24.04-ARM64.vmwarevm.zip
```

Dal Terminale, entra nella cartella che contiene il file e verifica l'impronta:

```bash
shasum -a 256 2cornot2c-Ubuntu-24.04-ARM64.vmwarevm.zip
```

Il risultato atteso per questa esportazione è registrato anche in
`SHA256SUMS`.

Non aprire il file se il checksum non coincide: scaricalo nuovamente o chiedi
una nuova copia al docente.

## 3. Caricare la VM in Fusion

1. fai doppio clic sul file ZIP e attendi la fine dell'estrazione;
2. sposta `2cornot2c-Ubuntu-24.04-ARM64.vmwarevm` in una cartella stabile, per
   esempio `~/Virtual Machines.localized/`;
3. fai doppio clic sul file `.vmwarevm`, oppure usa **File > Open** in Fusion;
4. se Fusion chiede se la macchina è stata spostata o copiata, scegli
   **I Copied It / Ho copiato la macchina**;
5. premi **Play**.

La sessione grafica accede automaticamente. Se vengono richieste le
credenziali, usa:

```text
utente: vagrant
password: vagrant
```

La macchina distribuita non contiene riferimenti alle cartelle del Mac del
docente e non configura cartelle condivise. Per conservare una copia del lavoro
anche sul Mac, crea una cartella personale e aggiungila da
**Virtual Machine > Settings > Sharing**.

Per spegnere la VM usa il menu di Ubuntu. Non chiudere Fusion forzatamente e
non distribuire una VM sospesa.

## Collaudo eseguito

Il pacchetto è stato estratto in una directory nuova e avviato con VMware
Fusion 26.0.0 build 25388279. Sono stati verificati:

- avvio come guest ARM64;
- disco consolidato e indipendente dalla box Vagrant originale;
- rete NAT e assegnazione dell'indirizzo IP;
- `vmtoolsd` attivo;
- login grafico LightDM e sessione XFCE;
- assenza di cartelle condivise e percorsi assoluti del Mac sorgente nella
  configurazione VMware.
