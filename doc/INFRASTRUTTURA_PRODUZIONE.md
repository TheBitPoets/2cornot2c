# Infrastruttura di produzione TheBitPoets — Guida completa

> Documento operativo e didattico: cosa abbiamo costruito, perché, e come
> rifarlo da zero. Scritto per chi vuole capire ogni passaggio, non solo
> ripeterlo. Ultimo aggiornamento: 4 agosto 2026.

---

## Indice

1. [L'architettura finale in uno sguardo](#1-larchitettura-finale-in-uno-sguardo)
2. [I tre provider e i loro ruoli](#2-i-tre-provider-e-i-loro-ruoli)
3. [Teoria: i mattoni da capire](#3-teoria-i-mattoni-da-capire)
4. [Cronologia completa dei lavori](#4-cronologia-completa-dei-lavori)
5. [La catena di una richiesta web, passo per passo](#5-la-catena-di-una-richiesta-web-passo-per-passo)
6. [Costi](#6-costi)
7. [Operazioni di routine](#7-operazioni-di-routine)
8. [Checklist "come rifare tutto da soli"](#8-checklist-come-rifare-tutto-da-soli)
9. [Dove sono le cose (mappa dei file e dei segreti)](#9-dove-sono-le-cose-mappa-dei-file-e-dei-segreti)
10. [Prossimi passi](#10-prossimi-passi)

---

## 1. L'architettura finale in uno sguardo

```
                        INTERNET
                            │
        ┌───────────────────┼────────────────────────┐
        │                   │                        │
  thebitpoets.net     thebitpoets.com          www.thebitpoets.net
  (apex e www)        (apex)                        │
        │                   │                        │
        └─────────301───────┴─────────301────────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │     CLOUDFLARE       │  ← bordo (edge): DNS, DNSSEC,
                  │  - DNS autoritativo  │    TLS verso i browser, redirect,
                  │  - DNSSEC            │    protezione DDoS
                  │  - TLS edge          │
                  │  - Redirect Rules    │
                  └─────────┬───────────┘
                            │
              ┌─────────────┴──────────────┐
              │                            │
   www.thebitpoets.com           app.thebitpoets.com
              │                            │
              ▼                            ▼
   ┌──────────────────┐      ┌──────────────────────────────┐
   │ Cloudflare Worker │      │  VPS Hetzner thebitlab-prod-1 │
   │ (sito statico:    │      │  91.98.123.183 — Debian 13    │
   │ logo + citazione) │      │  nginx (TLS Full strict)      │
   └──────────────────┘      │   → porta 8000: app Python    │
                             │   (TheBitLab, in arrivo)      │
                             └──────────────────────────────┘

   OVH = solo registrar (domini) + record DS (DNSSEC) + email (MX)
```

**Principio guida**: ogni componente fa una cosa sola e la fa bene.
OVH registra i nomi, Cloudflare gestisce DNS e traffico web, Hetzner ospita
il server applicativo. Ciascuno è sostituibile senza toccare gli altri.

---

## 2. I tre provider e i loro ruoli

| Provider | Ruolo | Dashboard | Cosa gestiamo lì |
|---|---|---|---|
| **OVHcloud** | Registrar domini + email | https://www.ovh.com/manager | Rinnovi `thebitpoets.com`/`.net`, record DS per DNSSEC, MX email |
| **Cloudflare** | DNS, edge, hosting statico | https://dash.cloudflare.com | Zone DNS, DNSSEC, redirect, SSL/TLS, Worker (landing), certificati origine |
| **Hetzner Cloud** | VPS (server vero) | https://console.hetzner.cloud | Server `thebitlab-prod-1`, backup, fatturazione |
| **GitHub** | Codice e release | https://github.com/TheBitPoets | Repository, classroom box releases, GHCR runner grading |

Account Hetzner (anagrafica/pagamenti): https://accounts.hetzner.com

### Perché questa separazione

- **OVH come solo registrar**: il registrar è chi detiene legalmente il nome a
  dominio. Non è obbligato a fornire anche DNS o hosting. Separare i ruoli
  significa poter cambiare DNS/hosting senza trasferire il dominio.
- **Cloudflare al centro**: DNS anycast velocissimo, DNSSEC semplice,
  certificati edge automatici, protezione DDoS, redirect e hosting statico
  gratuiti. È il "cancello d'ingresso" di tutto il traffico.
- **Hetzner per il compute**: ottimo rapporto prezzo/prestazioni in datacenter
  UE (GDPR), addebito orario, backup integrati.

---

## 3. Teoria: i mattoni da capire

### 3.1 Dominio, registrar, zona DNS

- **Dominio** (`thebitpoets.com`): un nome registrato presso un **registrar**
  (OVH) che lo affitta annualmente dal registry (Verisign per `.com`/`.net`).
- **Zona DNS**: l'insieme dei record che descrivono il dominio (chi è il web
  server, chi gestisce la posta...). Vive su dei **nameserver autoritativi**.
- **Delega**: nel pannello registrar dici "i nameserver di questo dominio sono
  X e Y". Da quel momento il mondo chiede i record a quei nameserver, non più
  a OVH. Noi abbiamo delegato entrambi i domini a Cloudflare
  (`jule.ns.cloudflare.com`, `sonny.ns.cloudflare.com`).

### 3.2 I record DNS che usiamo

| Record | Significato | Nostro esempio |
|---|---|---|
| `A` | nome → IPv4 | `app.thebitpoets.com → 91.98.123.183` |
| `AAAA` | nome → IPv6 | (Cloudflare li genera per i proxied) |
| `CNAME` | nome → altro nome (alias) | — |
| `MX` | chi riceve la posta | `mx1/2/3.mail.ovh.net` |
| `TXT` | testo (SPF, verifiche) | SPF per l'email OVH |
| `NS` | nameserver autoritativi | i due di Cloudflare |
| `SOA` | metadati della zona | automatico |
| `DS` | impronta della chiave DNSSEC, nel parent | registrato in OVH |
| `DNSKEY` | chiave pubblica DNSSEC, nella zona | pubblicata da Cloudflare |

**TTL** (Time To Live): per quanto i resolver possono tenere in cache un
record. Quando cambi un record, i vecchi valori possono sopravvivere in cache
fino alla scadenza del TTL — ecco perché alcune verifiche richiedevano attese
o davano risultati diversi tra PC locale e resolver pubblici.

### 3.3 DNSSEC

DNS classico non ha autenticità: un attaccante potrebbe falsificare risposte.
**DNSSEC** firma crittograficamente i record della zona.

Catena di fiducia:

1. Cloudflare firma la zona e pubblica la chiave pubblica (`DNSKEY`);
2. l'impronta della chiave (`DS`) va registrata **nel dominio genitore**
   (`.net`/`.com`) tramite il registrar — è il tassello che collega la fiducia
   del parent alla nostra zona;
3. i resolver validanti (Google, Cloudflare) verificano le firme e rispondono
   con il flag `AD` (Authenticated Data) = `true`.

Se manca il DS nel parent, la zona è firmata ma nessuno può validarla:
è esattamente lo stato "Pending" che abbiamo visto finché non abbiamo
registrato il DS in OVH.

### 3.4 TLS/HTTPS e le modalità SSL di Cloudflare

HTTPS = HTTP dentro un canale cifrato e autenticato da un **certificato**
rilasciato da una Certification Authority (CA) fidata.

Quando Cloudflare fa da proxy, ci sono **due tratti** di connessione:

```
browser ──(1)──> Cloudflare ──(2)──> server origine
```

| Modalità | Tratto (1) | Tratto (2) | Valutazione |
|---|---|---|---|
| Off | HTTP | HTTP | da non usare mai |
| Flexible | HTTPS | HTTP | cifra solo metà strada: accettabile solo come tappa temporanea |
| Full | HTTPS | HTTPS senza verifica certificato | meglio, ma l'origine potrebbe essere un impostore |
| **Full (strict)** | HTTPS | HTTPS **con verifica** del certificato origine | ✅ la nostra meta |

Per Full (strict) serve sull'origine un certificato valido per il nome:
- **Let's Encrypt** (CA pubblica gratuita, rinnovo ogni 90 gg) — richiede di
  poter installare il certificato sull'hosting;
- **Cloudflare Origin Certificate** (gratuito, 15 anni, fidato solo da
  Cloudflare) — perfetto quando l'origine sta solo dietro Cloudflare.

Sul nostro vecchio hosting OVH condiviso non si potevano installare
certificati personalizzati e HTTPS non era nemmeno attivo: per questo la
strada fu "Flexible temporaneo → nuova origine → Full (strict)".

### 3.5 Redirect 301 vs 302

- **301 / 308 = permanente**: browser e motori di ricerca aggiornano i propri
  riferimenti; è la scelta per canonicalizzare domini (`.net` → `.com`).
- **302 / 307 = temporaneo**: "per ora vai lì", nessuna canonicalizzazione.

Il vecchio OVH faceva un 302 verso `www` (inutile ai fini SEO e sicurezza);
le nostre Redirect Rules Cloudflare fanno **301 preservando percorso e query**
(`concat("https://www.thebitpoets.com", http.request.uri.path)` + preserve
query string).

### 3.6 Edge, origine e proxy inverso

- **Edge**: i datacenter Cloudflare sparsi nel mondo, primo punto di contatto
  del traffico. TLS edge, cache, WAF, DDoS protection.
- **Origine**: il server che produce davvero le risposte (la nostra VPS).
- **Nuvola arancione (Proxied)**: il record DNS risponde con gli IP
  Cloudflare; il traffico passa dall'edge, che inoltra all'origine.
- **Nuvola grigia (DNS only)**: il record risponde con l'IP reale; Cloudflare
  fa solo DNS, il traffico va dritto all'origine (niente TLS edge, niente
  protezione).

### 3.7 VPS, SSH e chiavi asimmetriche

- **VPS** (Virtual Private Server): una macchina virtuale Linux affittata in
  un datacenter, con IP pubblico, su cui hai controllo totale.
- **SSH**: protocollo cifrato per amministrarla da remoto.
- **Chiave asimmetrica** (ed25519): coppia di file.
  - **privata** (`id_ed25519`): resta sul tuo PC, protetta da passphrase;
    chi la possiede può entrare → mai condividerla, mai incollarla in chat;
  - **pubblica** (`id_ed25519.pub`): si installa sul server
    (`~/.ssh/authorized_keys`) → sicura da condividere.
- **Passphrase**: cifra la chiave privata sul disco. Se qualcuno ruba il file,
  senza passphrase non può usarla.
- **ssh-agent**: programma che sblocca la chiave una volta e la riusa per le
  connessioni successive, senza ridigitare la passphrase.
- Attenzione ai **filesystem**: NTFS (Windows C:) supporta i permessi per
  file; **exFAT** (il nostro disco E:) no — OpenSSH rifiuta chiavi private su
  filesystem "troppo permissivi". Per questo la copia di lavoro sta su C:.

### 3.7bis SSH da Windows: configurazione completa (come l'abbiamo fatta noi)

Questa è la procedura esatta eseguita sul PC Windows, con i comandi e gli
errori incontrati, per poterla rifare su qualunque macchina.

#### a) Generare la coppia di chiavi

In PowerShell (utente normale):

```powershell
ssh-keygen -t ed25519 -f E:\.thebitlab-secrets\hetzner\id_ed25519 -C "thebitlab-hetzner"
```

- `-t ed25519`: algoritmo moderno (più corto e sicuro di RSA);
- `-f`: percorso del file chiave;
- `-C`: commento identificativo (finisce nella chiave pubblica);
- alla richiesta `Enter passphrase`: digita una passphrase robusta **e
  conservala nel password manager**. Non si vede mentre la digiti.

Risultato: due file
- `id_ed25519` — **privata**, mai condividerla;
- `id_ed25519.pub` — **pubblica**, da incollare nei provider (Hetzner, ecc.).

Per vedere/copiare la pubblica:

```powershell
Get-Content E:\.thebitlab-secrets\hetzner\id_ed25519.pub
```

#### b) Il problema exFAT e la copia protetta su C:

OpenSSH rifiuta chiavi private leggibili da altri. Il disco E: è exFAT e
**non supporta i permessi**: `ssh-add` fallisce con
`WARNING: UNPROTECTED PRIVATE KEY FILE!`.

Soluzione: copia di lavoro su C: (NTFS) con permessi restrittivi:

```powershell
# copia
New-Item -ItemType Directory -Force C:\Users\antonio\.thebitlab-secrets\hetzner
Copy-Item E:\.thebitlab-secrets\hetzner\id_ed25519* C:\Users\antonio\.thebitlab-secrets\hetzner\

# permessi: solo il proprietario, niente ereditarietà
icacls C:\Users\antonio\.thebitlab-secrets /inheritance:r /grant:r "$env:COMPUTERNAME\$env:USERNAME:(OI)(CI)F"
icacls C:\Users\antonio\.thebitlab-secrets\hetzner\id_ed25519 /inheritance:r /grant:r "$env:COMPUTERNAME\$env:USERNAME:F"
```

Verifica:

```powershell
icacls C:\Users\antonio\.thebitlab-secrets\hetzner\id_ed25519
# deve mostrare una sola riga: NOMEPC\antonio:(F)
```

#### c) ssh-agent: sbloccare la chiave una volta sola

In PowerShell **come Amministratore** (solo la prima volta):

```powershell
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
```

Poi (anche da utente normale, e **dopo ogni riavvio del PC**):

```powershell
ssh-add C:\Users\antonio\.thebitlab-secrets\hetzner\id_ed25519
# Enter passphrase: ...
# Identity added: ...
```

Da questo momento tutte le connessioni SSH usano l'agent: niente più
passphrase finché non riavvii (o finché non fai `ssh-add -D` per svuotare).

Comandi utili dell'agent:

```powershell
ssh-add -l    # elenca le chiavi sbloccate
ssh-add -D    # rimuove tutte le chiavi dall'agent
```

#### d) La prima connessione e known_hosts

```powershell
ssh thebitlab@91.98.123.183
```

Alla primissima connessione SSH mostra l'impronta (fingerprint) del server e
chiede conferma: rispondendo `yes` il server viene registrato in
`C:\Users\antonio\.ssh\known_hosts`. Alle connessioni successive nessuna
domanda; se un giorno l'impronta cambiasse inaspettatamente, SSH avvisa con
un grosso warning (possibile attacco man-in-the-middle — oppure server
reinstallato: in quel caso si rimuove la riga da known_hosts e si riaccetta).

Per evitare la domanda interattiva negli script:

```powershell
ssh -o StrictHostKeyChecking=accept-new thebitlab@91.98.123.183
```

#### e) Copiare file da/verso il server (SCP)

```powershell
# locale -> server
scp C:\percorso\file.pem thebitlab@91.98.123.183:/tmp/

# server -> locale
scp thebitlab@91.98.123.183:/etc/nginx/nginx.conf C:\percorso\
```

#### f) Errori tipici incontrati e soluzioni

| Errore | Causa | Soluzione |
|---|---|---|
| `Accesso negato` su `Set-Service` | PowerShell non elevato | Esegui come amministratore |
| `UNPROTECTED PRIVATE KEY FILE` | chiave su exFAT/senza ACL | copia su NTFS + `icacls` come sopra |
| `Permission denied (publickey)` | chiave non nell'agent o utente sbagliato | `ssh-add -l` per verificare; controlla che la pub sia in `authorized_keys` sul server |
| root rifiutato dopo hardening | `PermitRootLogin no` | previsto: usa `thebitlab@` |

### 3.8 Hardening di un server

Principio: **ridurre la superficie d'attacco**.

- aggiornamenti applicati + automatici di sicurezza (`unattended-upgrades`);
- utente non-root con `sudo` (il root SSH viene disabilitato);
- SSH: solo chiavi, niente password, pochi tentativi (`MaxAuthTries 3`);
- firewall (`ufw`): tutto chiuso tranne 22 (SSH), 80 e 443 (web);
- `fail2ban`: banna temporaneamente gli IP che tentano login a ripetizione;
- backup automatici del provider (snapshot settimanali).

### 3.9 nginx come reverse proxy

nginx sta "davanti" all'applicazione Python:

```
Cloudflare → nginx:443 (TLS, security headers) → 127.0.0.1:8000 (app Python)
```

Perché non esporre direttamente l'app?

- terminazione TLS in un componente maturo e aggiornabile;
- header di sicurezza (HSTS, X-Frame-Options...) in un punto solo;
- l'app resta in ascolto solo su localhost: non raggiungibile dall'esterno
  nemmeno per errore;
- in futuro: più app dietro lo stesso nginx, rate limiting, cache.

### 3.10 Cloudflare Workers (siti statici)

La landing `www.thebitpoets.com` è un insieme di file statici (HTML, CSS,
immagini). Cloudflare li distribuisce dai propri datacenter ("Worker con
static assets", evoluzione di Pages): nessun server da mantenere, HTTPS
incluso, costo zero. È la scelta giusta per contenuti che non cambiano a ogni
richiesta. Il **backend TheBitLab invece non può vivere lì**: è un processo
persistent e stateful (SQLite, sessioni, grading Docker), mentre i Workers
sono funzioni stateless con limiti di CPU di millisecondi.

---

## 4. Cronologia completa dei lavori

### 4.1 Migrazione DNS a Cloudflare (fatta in sessioni precedenti)

- Creati gli account/zona Cloudflare per `thebitpoets.com` e `.net`.
- Cambiati i nameserver in OVH → delega a Cloudflare.
- `.com`: zona attiva, DNSSEC attivo (DS registrato in OVH).
- `.net`: delega convergente ma DNSSEC e redirect mancanti → completati in
  questa sessione (vedi 4.3 e 4.4).

**Perché**: un solo pannello DNS moderno, DNSSEC gestito, edge gratuito.

### 4.2 Stato iniziale di questa sessione

Verifiche con resolver pubblici (DoH verso `cloudflare-dns.com` e
`dns.google`):

- `.net`: NS Cloudflare OK, ma record A ancora verso OVH `213.186.33.5`,
  niente DNSSEC, redirect 302 temporaneo e `www` che rispondeva 200 con la
  pagina OVH "Site en construction";
- `.com`: DNSSEC attivo, ma SSL su Flexible e record A verso OVH placeholder.

### 4.3 Redirect canonici

1. Regola `canonical-com-apex-to-www`: host `thebitpoets.com` → 301 verso
   `https://www.thebitpoets.com` + percorso, query preservata.
2. Regola `canonical-net-to-com`: host `thebitpoets.net` o
   `www.thebitpoets.net` → 301 verso `https://www.thebitpoets.com` + percorso,
   query preservata.
3. Attivate le nuvole arancioni sui record A di `.com` e `.net` (apex e www),
   lasciando DNS-only MX/TXT/ftp.
4. Verifiche: 301 corretti su HTTP e HTTPS, percorso e query preservati,
   server `cloudflare` nelle risposte.

**Perché www come canonico**: l'host che serviva contenuto era `www`;
l'apex fa da "rimbalzo". SEO e certificati diventano semplici.

### 4.4 DNSSEC per .net

1. Abilitato DNSSEC nella zona `.net` su Cloudflare → stato *Pending*
   (chiavi pubblicate, DS mancante nel parent).
2. Lettura dei parametri DS da Cloudflare (Key Tag, Flag, Algorithm,
   Public Key).
3. In OVH → `thebitpoets.net` → scheda **Record DS** → inserito il record
   (senza mai copiare valori in chat: contengono materiale della chiave).
4. Dopo pochi minuti: DS presente nel parent, `AD=true` su Google/Cloudflare
   DNS, nessun SERVFAIL.

### 4.5 Landing page www.thebitpoets.com

- Discussione di design su bozze HTML reali (`E:\thebitpoetslogo\mockups\`):
  dark/light, animazioni (gocce CSS, spray reveal via tracciati SVG generati
  con potrace — conservata come v5 per il futuro).
- Scelta finale: **v6** — sfondo chiaro, logo nero, citazione Ginsberg in
  dissolvenza. Zero JavaScript, `prefers-reduced-motion` rispettato.
- Asset ottimizzati: WebP + PNG (400/521px), favicon ICO/PNG
  (`E:\thebitpoetslogo\site\`).
- Deploy: Cloudflare **Workers & Pages → Create → Upload assets** → progetto
  `thebitpoets` → URL iniziale `thebitpoets.a-caristia.workers.dev`.
- Custom domain `www.thebitpoets.com`: richiesta la rimozione del vecchio
  record A `www → 213.186.33.5`, poi collegamento riuscito.
- SSL/TLS `.com`: **Full (strict)**.
- Verifiche finali: 200 su www, 301 da apex `.com` e da tutto `.net`,
  DNSSEC OK su entrambe le zone.

### 4.6 VPS Hetzner

1. Account su https://accounts.hetzner.com + metodo di pagamento;
   progetto `thebitlab` in https://console.hetzner.cloud.
2. Chiave SSH ed25519 **con passphrase** generata su Windows
   (`E:\.thebitlab-secrets\hetzner\`), poi copiata su
   `C:\Users\antonio\.thebitlab-secrets\hetzner\` con ACL NTFS restrittivi
   (solo il proprietario) perché E: è exFAT e OpenSSH rifiuta chiavi su
   filesystem senza permessi.
3. `ssh-agent` di Windows attivato (servizio automatico) e chiave aggiunta:
   passphrase digitata una sola volta.
4. Server: **CX23** (2 vCPU / 4 GB / 40 GB — CX33 4/8 non disponibile in
   nessuna location; resize futuro possibile), Debian 13, location Nuremberg,
   backup settimanali attivi, chiave SSH registrata come default.
   IPv4 pubblico: **91.98.123.183**.

### 4.7 Hardening del server

- `apt update && upgrade` + reboot (kernel cloud).
- Utente `thebitlab` (sudo NOPASSWD per automazione), stessa chiave SSH.
- `/etc/ssh/sshd_config.d/90-thebitlab-hardening.conf`:
  `PasswordAuthentication no`, `PermitRootLogin no`, `MaxAuthTries 3`.
  Verificato: login root rifiutato, login thebitlab OK.
- `ufw`: default deny incoming, allow outgoing; aperte 22/80/443 (v4+v6).
- `fail2ban` attivo; `unattended-upgrades` attivo.
- Docker CE + compose plugin installati dal repository ufficiale Docker;
  `hello-world` OK; utente nel gruppo `docker`.

### 4.8 app.thebitpoets.com: DNS, certificato origine, nginx

1. Record A `app.thebitpoets.com → 91.98.123.183`, inizialmente **DNS only**
   (grigio) per poter lavorare sull'origine.
2. **Cloudflare Origin Certificate** (SSL/TLS → Origin Server → Create):
   copre `*.thebitpoets.com` + apex, scadenza 2041. Salvato localmente e
   copiato via SCP sul server in `/etc/ssl/thebitlab/` (chiave `600` root).
3. nginx installato; sito `/etc/nginx/sites-available/thebitlab.conf`:
   - 443: TLS con cert origine, HSTS, header di sicurezza, proxy verso
     `http://127.0.0.1:8000` (dove vivrà l'app Python);
   - 80: redirect 301 → HTTPS.
4. Attivata la nuvola arancione su `app`.
5. Verifica: `502 Bad Gateway` tramite Cloudflare = catena TLS Full (strict)
   funzionante (nginx risponde, l'app non c'è ancora). Locale inizialmente
   ingannato da cache DNS: verificato con `--resolve` verso IP Cloudflare.

---

## 5. La catena di una richiesta web, passo per passo

Esempio: uno studente apre `https://app.thebitpoets.com/dashboard`.

1. **DNS**: il browser chiede l'IP di `app.thebitpoets.com`. Il resolver
   interroga i nameserver Cloudflare (delega registrata in OVH). Il record è
   *proxied* → risponde con IP Cloudflare (es. 104.21.x.x). La risposta è
   firmata DNSSEC; il resolver valida la catena DS(.com)→DS(zone)→DNSKEY.
2. **TLS edge**: il browser apre HTTPS verso Cloudflare, che presenta il
   proprio certificato pubblico per `*.thebitpoets.com` (fidato dai browser).
3. **Policy edge**: Cloudflare applica redirect rules, WAF, eventuali
   limitazioni. Nessuna regola matcha `app` → inoltra all'origine.
4. **TLS origine (Full strict)**: Cloudflare apre HTTPS verso
   `91.98.123.183:443`; nginx presenta l'Origin Certificate; Cloudflare lo
   verifica (nome e CA Origin) — strict.
5. **nginx**: termina TLS, aggiunge header di sicurezza, legge `Host` e
   inoltra a `http://127.0.0.1:8000` (l'app Python, solo localhost).
6. **App TheBitLab**: autenticazione, autorizzazione, SQLite, risposta.
7. La risposta ripercorre la catena a ritroso.

Per `https://www.thebitpoets.com`: i passi 1–3 sono identici, ma al passo 4
la risposta arriva direttamente dallo **storage statico Cloudflare** (Worker):
nessuna origine coinvolta.

Per `https://thebitpoets.net/qualsiasi`: al passo 3 la Redirect Rule scatta
immediatamente → **301** verso `https://www.thebitpoets.com/qualsiasi`;
l'origine non viene mai contattata.

---

## 6. Costi

| Voce | Costo | Note |
|---|---|---|
| Domini .com + .net | rinnovo annuale OVH | già pagati fino al 31/07/2027 |
| Cloudflare | **€0** | piano Free: DNS, DNSSEC, TLS edge, redirect, Worker statico |
| VPS Hetzner CX23 | ~€6,70/mese IVA incl. | addebito orario, cancellabile |
| Backup VPS | +20% (~€1,30/mese) | snapshot settimanali |
| IPv4 | inclusa/pochi cent | |
| GitHub | **€0** | repo, releases, GHCR (pubblici) |
| **Totale** | **~€8/mese (~€96/anno)** | resize CX33 futuro: ~€12/mese |

---

## 7. Operazioni di routine

### Connettersi al server

```powershell
# dopo un riavvio del PC, sblocca la chiave una volta:
ssh-add C:\Users\antonio\.thebitlab-secrets\hetzner\id_ed25519

# connessione:
ssh thebitlab@91.98.123.183

# verifica quali chiavi sono sbloccate:
ssh-add -l
```

Per la configurazione completa da zero (generazione chiavi, ACL, agent,
known_hosts, SCP, errori tipici) vedi la sezione **3.7bis**.

### Comandi utili sul server

```bash
# Servizi
sudo systemctl status thebitlab   # app Python
sudo systemctl restart thebitlab  # riavvio app
sudo systemctl status nginx       # reverse proxy
sudo nginx -t                     # valida config prima di reload
sudo systemctl reload nginx
sudo docker ps                    # container attivi (Uptime Kuma)

# Sicurezza e sistema
sudo ufw status                   # stato firewall
sudo fail2ban-client status sshd  # IP bannati
df -h /                           # spazio disco
free -h                           # memoria
sudo apt update && sudo apt upgrade   # aggiornamenti manuali

# Log
sudo journalctl -u thebitlab -f   # log app in tempo reale
cat /srv/backups/backup.log       # log backup
```

---

### 7.1 Monitoraggio con Uptime Kuma

Uptime Kuma è installato sullo stesso server in un container Docker e raggiungibile
attraverso il sottodominio `status.thebitpoets.com`.

| URL | Scopo |
|---|---|
| `https://status.thebitpoets.com` | Dashboard di amministrazione (login con l'utente creato al primo avvio) |
| `https://status.thebitpoets.com/status/default` | **Pagina di stato pubblica** da condividere con docenti/studenti |

#### Componenti del monitoraggio

- **Container**: `uptime-kuma` su `127.0.0.1:3001`
- **Reverse proxy**: nginx vhost `status.thebitpoets.com` → `http://127.0.0.1:3001`
- **DNS**: record `A status` → `91.98.123.183` (Proxied 🟠 su Cloudflare)
- **Dati persistenti**: `/srv/uptime-kuma/data`

#### Monitor configurati

| Nome | URL | Metodo | Codice atteso | Note |
|---|---|---|---|---|
| TheBitLab app | `https://app.thebitpoets.com/tools/course_board.html` | GET | 200 | HTTP Basic Auth: username `teacher`, password dal file `teacher-token.txt` |
| TheBitLab Google login | `https://app.thebitpoets.com/auth/google/login` | GET | 302 | **Max redirects = 0**, altrimenti segue il redirect su Google e torna 200 (rosso) |
| thebitpoets.com landing | `https://www.thebitpoets.com/` | GET | 200 | Nessuna auth |
| thebitpoets.com/thebitlab | `https://www.thebitpoets.com/thebitlab/` | GET | 200 | Nessuna auth |

#### Come aggiungere un monitor manualmente

1. Accedi a `https://status.thebitpoets.com`
2. **Add New Monitor**
3. Scegli **HTTP(s)**, dai un nome, inserisci URL e codice atteso
4. Se serve Basic Auth (es. course board), espandi **Auth** → **HTTP Basic Auth**
5. In **Advanced** imposta **Heartbeat Interval** (es. 60 secondi) e **Retries** (es. 3)
6. Per il login Google imposta **Max. Redirects: 0**
7. **Save**

#### Come creare/aggiornare la status page pubblica

1. Nel menu a sinistra clicca **Status Page**
2. Seleziona la pagina `default` (o creane una nuova)
3. Modifica titolo/descrizione e trascina i monitor nella pagina
4. **Save**
5. L'URL pubblico sarà `https://status.thebitpoets.com/status/<slug>`

---

### 7.2 Snapshot Hetzner

Gli snapshot manuali sono la "foto" di uno stato noto buono dell'intera macchina:
SO, pacchetti, configurazioni nginx/systemd, dati applicativi, segreti sul disco.
Lo staging testa il codice, ma non protegge da incidenti a livello di sistema.

#### Quando crearne uno

- Subito dopo un deploy andato a buon fine (golden state)
- Prima di aggiornamenti di sistema importanti (`apt upgrade` del kernel, Docker, nginx)
- Prima di modifiche manuali a configurazioni critiche (nginx, systemd, env)
- Prima di resize o migrazioni

#### Frequenza e retention

- **Snapshot manuali**: 2–3 attivi per volta; cancellare quelli più vecchi dopo averne creato uno nuovo
- **Backup automatici Hetzner**: già attivi (settimanali), costano il 20% del server
- **Costo snapshot manuale**: ~€0,012/GB/mese (paga solo lo spazio effettivamente usato)

#### Procedura manuale dal dashboard

1. https://console.hetzner.cloud/projects → progetto **thebitlab**
2. **Servers** → clicca **thebitlab-prod-1**
3. Scheda **Snapshots**
4. Per coerenza del database SQLite, fermare brevemente il servizio:

   ```bash
   ssh thebitlab@91.98.123.183
   sudo systemctl stop thebitlab
   ```

5. **Create snapshot** → nome es. `thebitlab-prod-1-YYYY-MM-DD-pre-upgrade`
6. Attendi che lo stato sia **Created / Available**
7. Riavvia il servizio:

   ```bash
   sudo systemctl start thebitlab
   ```

8. Verifica che `https://app.thebitpoets.com` risponda

#### Cancellazione

Nel pannello **Snapshots** del server, seleziona lo snapshot obsoleto e clicca
**Delete**. Lo spazio liberato smette di essere fatturato.

---

### 7.3 Backup applicativo cifrato

Mentre lo snapshot salva l'intera macchina, questo backup salva solo i dati
applicativi essenziali in un repository GitHub privato, cifrato con GPG.
È utile per:

- recuperare rapidamente un singolo dato (utente, classe, configurazione)
- tenere una copia off-site dei dati fuori da Hetzner
- confrontare lo stato del database nel tempo

#### Cosa viene salvato

- `auth.sqlite3` — database SQLite identità/sessioni (da `/srv/thebitlab/data/.thebitlab-auth/`)
- `thebitlab.env` — variabili d'ambiente del servizio
- `nginx-thebitlab.conf` e `nginx-status.conf` — vhost nginx

#### Crittografia

- Algoritmo: **AES256** con GPG in modalità simmetrica
- Passphrase: unica, generata casualmente, conservata in:
  - server: `/etc/thebitlab/backup-passphrase` (`600`, utente `thebitlab`)
  - PC admin: `C:\Users\antonio\.thebitlab-secrets\hetzner\backup-passphrase.txt`

> **Senza la passphrase il backup è irrecuperabile.**

#### Dove finisce il backup

- Repository privato: `https://github.com/TheBitPoets/thebitlab-backups`
- File: `thebitlab-prod-1-YYYYMMDD-HHMMSS.tar.gz.gpg`
- Script: `/opt/thebitlab/bin/backup.sh`
- Log: `/srv/backups/backup.log`

#### Autenticazione: a cosa serve la chiave SSH `backup-deploy`

Il server usa una chiave SSH dedicata (`/home/thebitlab/.ssh/backup-deploy`)
per autenticarsi su GitHub e fare il push del backup cifrato.

- La chiave **pubblica** è registrata su GitHub (nel tuo account, opzione A).
- La chiave **privata** resta solo sul server in `/home/thebitlab/.ssh/backup-deploy`.
- Scopo unico: pushare nel repo `TheBitPoets/thebitlab-backups`.

> Se possibile, in futuro sposta la chiave da "account personale" a
> **Deploy Key** del solo repo `thebitlab-backups` (più ristretta). Questo
> richiede che le deploy key siano abilitate per il repository/l'organizzazione.

#### Schedulazione

Il backup parte ogni giorno alle **03:00 UTC** tramite cron dell'utente `thebitlab`:

```bash
sudo -u thebitlab crontab -l
# 0 3 * * * /opt/thebitlab/bin/backup.sh
```

#### Esecuzione manuale

```bash
ssh thebitlab@91.98.123.183
sudo -u thebitlab /opt/thebitlab/bin/backup.sh
```

#### Verifica e ripristino

Da server, per verificare che un backup si apra:

```bash
LATEST=$(ls -t /srv/backups/repo/*.gpg | head -1)
gpg --batch --yes --passphrase-file /etc/thebitlab/backup-passphrase \
    -d "$LATEST" | tar -tzf -
```

Per ripristinare (esempio: ripristinare il database di ieri):

```bash
# 1. Ferma l'app
sudo systemctl stop thebitlab

# 2. Decritta in una cartella temporanea
mkdir -p /tmp/restore
gpg --batch --yes --passphrase-file /etc/thebitlab/backup-passphrase \
    -d /srv/backups/repo/thebitlab-prod-1-YYYYMMDD-HHMMSS.tar.gz.gpg \
    | tar -xzf - -C /tmp/restore

# 3. Sostituisci i file (assicurati di voler sovrascrivere!)
sudo cp /tmp/restore/auth.sqlite3 /srv/thebitlab/data/.thebitlab-auth/
sudo cp /tmp/restore/thebitlab.env /etc/thebitlab/thebitlab.env
sudo chown -R thebitlab:thebitlab /srv/thebitlab/data/.thebitlab-auth
sudo chmod 600 /srv/thebitlab/data/.thebitlab-auth/auth.sqlite3
sudo chmod 640 /etc/thebitlab/thebitlab.env
sudo chown root:thebitlab /etc/thebitlab/thebitlab.env

# 4. Riavvia
sudo systemctl start thebitlab
```

---

## 8. Checklist "come rifare tutto da soli"

1. **Registrar**: registra il dominio; imposta i nameserver del provider DNS.
2. **Zona DNS**: crea i record (A/AAAA per web, MX/TXT per email).
3. **DNSSEC**: attiva nella zona → registra il DS nel registrar → verifica
   `AD=true` (es. `https://dns.google/resolve?name=...&type=A&do=true`).
4. **Redirect**: regole 301 al bordo per domini secondari/apex, preservando
   percorso e query.
5. **Sito statico**: Workers/Pages upload assets → custom domain → elimina i
   vecchi record che puntavano altrove.
6. **Chiave SSH**: `ssh-keygen -t ed25519` con passphrase; pub sul server,
   privata protetta (NTFS + ACL) e in ssh-agent.
7. **VPS**: image Debian/Ubuntu minimale, chiave SSH, backup attivi.
8. **Hardening**: update, utente sudo, sshd key-only no-root, ufw, fail2ban,
   unattended-upgrades, Docker se serve.
9. **TLS origine**: Origin Certificate o Let's Encrypt; nginx 443 + 80→443.
10. **Proxy**: attiva la nuvola arancione; SSL/TLS **Full (strict)**.
11. **Verifiche**: curl `-I` per status/redirect; DoH per DNS/DNSSEC;
    `--resolve` per bypassare cache locali.

---

## 9. Dove sono le cose (mappa dei file e dei segreti)

### Sul PC di amministrazione

| Percorso | Contenuto |
|---|---|
| `E:\thebitpoetslogo\` | loghi originali PNG |
| `E:\thebitpoetslogo\site\` | sorgenti della landing (index.html, assets, favicon) |
| `E:\thebitpoetslogo\mockups\` | bozze (v5 spray animata, v6 finale, ecc.) |
| `E:\.thebitlab-secrets\hetzner\` | chiave SSH + Origin cert/key (exFAT: protetti solo da passphrase) |
| `C:\Users\antonio\.thebitlab-secrets\hetzner\` | copia di lavoro chiave SSH (NTFS, ACL restrittivi), teacher token, passphrase backup |
| `C:\Users\antonio\.thebitlab-secrets\github-app\` | segreti GitHub App TheBitLab (runtime token, private key) |
| `C:\Users\antonio\.thebitlab-secrets\google-oauth-client.json` | client OAuth 2.0 Google (uso deploy) |

### Sul server `thebitlab-prod-1` (91.98.123.183)

| Percorso | Contenuto |
|---|---|
| `/etc/ssl/thebitlab/` | Origin Certificate + chiave (root, 600) |
| `/etc/nginx/sites-available/thebitlab.conf` | vhost app.thebitpoets.com |
| `/etc/nginx/sites-available/status.thebitlab.conf` | vhost status.thebitpoets.com |
| `/etc/systemd/system/thebitlab.service` | unit systemd dell'app |
| `/etc/thebitlab/thebitlab.env` | variabili d'ambiente (teacher token, OAuth, segreti CAS) |
| `/etc/thebitlab/backup-passphrase` | passphrase cifratura backup (600, thebitlab) |
| `/etc/ssh/sshd_config.d/90-thebitlab-hardening.conf` | hardening SSH |
| `/etc/sudoers.d/thebitlab` | sudo NOPASSWD per automazione |
| `/opt/thebitlab/repo/` | checkout pinnato del repository 2cornot2c |
| `/opt/thebitlab/venv/` | virtualenv Python con dipendenze auth |
| `/opt/thebitlab/bin/backup.sh` | script backup giornaliero |
| `/srv/thebitlab/data/` | data root dell'app (SQLite, lock) |
| `/srv/backups/repo/` | clone del repo GitHub con backup cifrati |
| `/srv/backups/backup.log` | log esecuzioni backup |
| `/srv/uptime-kuma/data/` | dati persistenti Uptime Kuma |
| `/home/thebitlab/` | home utente operativo |
| `/home/thebitlab/.ssh/backup-deploy` | chiave SSH per push backup su GitHub |
| `/home/thebitlab/.thebitlab-secrets/github-app/` | runtime.json + private-key.pem GitHub App |

**Regole d'oro**: mai incollare in chat chiavi private, passphrase, token,
DS/digest DNSSEC. Le chiavi pubbliche e gli IP pubblici invece sì.

---

## 10. Prossimi passi

- [x] Deploy dell'applicazione TheBitLab sulla VPS
- [x] Snapshot Hetzner post-deploy ("golden state")
- [x] Monitoraggio Uptime Kuma + status page pubblica
- [x] Backup applicativo cifrato con retention e cron
- [ ] Test login Google reale con un account personale → verificare utente `pending`
- [ ] Ambiente di staging su porta secondaria per test futuri
- [ ] Resize a CX33 quando disponibile (o se il carico lo richiede)
- [ ] Pulizia record obsoleti (TXT placeholder OVH, CNAME ftp)
- [ ] Sostituire la chiave SSH di backup da "account personale" a deploy key
      del solo repo `thebitlab-backups` (quando abilitato)
