# Ambienti didattici riproducibili

## Obiettivo

Fornire agli studenti un solo percorso supportato per sistema operativo:

| Host | Architettura guest | Provider | Artefatto |
| --- | --- | --- | --- |
| Windows 10/11 | amd64 | VirtualBox | box Vagrant Packer |
| macOS Apple Silicon | arm64 | VMware Fusion | box Vagrant Packer |

VirtualBox su macOS resta un fallback per il docente. L'ambiente Docker
interattivo sarà una milestone separata e non sostituirà il runner di grading.

## Prima iterazione

La prima iterazione usa come input la box multiarch `bento/ubuntu-24.04`.
Questo mantiene i Guest Tools specifici del provider già collaudati e permette
di concentrarsi su desktop minimale, toolchain, consumi e test. La versione
della box sorgente è fissata.

Packer esegue lo stesso provisioning sui due provider e produce artefatti
distinti:

- `2cornot2c-ubuntu-24.04-virtualbox-amd64.box`;
- `2cornot2c-ubuntu-24.04-vmware-arm64.box`.

Una futura iterazione potrà sostituire Bento con installazioni da ISO Ubuntu
senza cambiare gli script di provisioning o i criteri di accettazione.

## Contenuto della box

- Ubuntu 24.04;
- Xorg, LightDM e componenti XFCE selezionati senza il metapacchetto completo;
- login automatico dell'utente `vagrant`;
- GCC, GDB, Make, Git e Vim;
- VirtualBox Guest Additions oppure `open-vm-tools-desktop`;
- zram configurata;
- script di selezione della risoluzione VMware;
- health check locale.

## Responsabilità residue di Vagrant

Il Vagrantfile del corso continua a gestire:

- CPU e memoria della VM;
- cartelle condivise `lab` e `lab2`;
- clipboard e drag-and-drop;
- piccole correzioni compatibili con box già distribuite;
- health check dopo l'avvio.

Le installazioni costose e stabili devono invece passare progressivamente dal
provisioning Vagrant alla box Packer.

## Criteri di accettazione

Una box può essere pubblicata solo se:

1. il login grafico automatico arriva a una sessione utilizzabile;
2. GCC, GDB, Make, Git e Vim sono disponibili;
3. i Guest Tools del provider sono attivi;
4. `lab` e `lab2` possono essere montate da Vagrant;
5. tutti i laboratori C compilabili superano il controllo previsto dal repo;
6. la VM funziona con 2048 MB di RAM e due CPU;
7. il consumo a riposo viene registrato dopo almeno 60 secondi dal login;
8. la box e il suo checksum SHA-256 vengono pubblicati insieme;
9. la versione Ubuntu, della box sorgente e della toolchain sono tracciate.

Il target sperimentale è 1536 MB; non è un requisito di pubblicazione finché
desktop, compilazione e GDB non risultano stabili.

### Prima misura VMware arm64

La box costruita localmente il 27 luglio 2026 ha superato l'avvio con sessione
XFCE e cartelle condivise sia a 2048 MB sia a 1536 MB:

| RAM assegnata | RAM usata dopo l'avvio | RAM disponibile | zram usata |
| ---: | ---: | ---: | ---: |
| 2048 MB | 386 MB | 1569 MB | 0 MB |
| 1536 MB | 408 MB | 1045 MB | 0 MB |

Le misure sono indicative e precedono il carico dei laboratori. Il profilo
1536 MB resta sperimentale finché compilazione, GDB e sessioni prolungate non
superano gli stessi acceptance test del profilo da 2048 MB.

## Vincoli di build

- VMware arm64 viene costruita e testata su un Mac Apple Silicon.
- VirtualBox amd64 deve essere costruita su Windows o Linux amd64 con
  virtualizzazione hardware disponibile.
- I normali runner GitHub hosted non sono considerati idonei alle build
  annidate; servirà un runner self-hosted oppure una macchina di build.
- I file in `packer/output` sono artefatti locali e non entrano in Git.

## Versionamento

Le box seguono SemVer. Un cambio di Ubuntu o incompatibile incrementa la
versione major; nuovi strumenti incrementano la minor; correzioni a
configurazione e provisioning incrementano la patch.

Il Vagrantfile degli studenti deve fissare una versione approvata. Una nuova
box non modifica automaticamente VM già create: l'installer dovrà proporre
backup delle cartelle condivise e ricreazione controllata.
