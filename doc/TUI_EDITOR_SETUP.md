# Configurare l'editor della TUI

La TUI di TheBitLab integra di default l'editor **micro**:

- piccolo e veloce (un solo binario);
- syntax highlighting per C, Python, Markdown e molti altri linguaggi;
- supporto mouse;
- keybinding intuitivi (`Ctrl+S` salva, `Ctrl+Q` esce, `Ctrl+G` aiuto).

`micro` viene installato automaticamente nelle immagini del lab (Windows e Linux).
Lo studente non deve configurare nulla per iniziare.

## Variabili d'ambiente

| Variabile | Scopo |
|-----------|-------|
| `THEBITLAB_EDITOR` | Editor usato dal comando `v` per aprire il file sorgente della consegna. |
| `THEBITLAB_WORKSPACE_EDITOR` | Programma usato dal comando `o` per aprire la cartella del workspace. |

Se `THEBITLAB_WORKSPACE_EDITOR` non e' impostata, la TUI prova a usare `THEBITLAB_EDITOR` solo se e' un editor in grado di aprire cartelle (ad esempio VS Code, VSCodium, Cursor, Zed, Fleet, Sublime Text). Se l'editor non supporta le cartelle, `o` apre la cartella con il file manager di sistema.

## Editor che supportano l'apertura di cartelle

La TUI riconosce automaticamente i seguenti editor per il comando `o`:

- `code`, `code-insiders`, `code-oss` (Visual Studio Code)
- `codium`, `vscodium` (VSCodium)
- `cursor`
- `zed`
- `fleet`
- `subl` (Sublime Text)
- `atom`
- `gedit`
- `kate`
- `mousepad`
- `notepadqq`
- `geany`
- `brackets`

## Configurare Visual Studio Code

### 1. Aggiungere `code` al PATH di Windows

1. Apri **VS Code**.
2. Premi `Ctrl+Shift+P` (o `Cmd+Shift+P` su macOS).
3. Digita e seleziona: `Shell Command: Install 'code' command in PATH`.
4. Chiudi e riapri il terminale.

Verifica con:

```powershell
Get-Command code
```

oppure, nel Prompt dei comandi:

```cmd
where code
```

### 2. Impostare la variabile d'ambiente

#### PowerShell (solo sessione corrente)

```powershell
$env:THEBITLAB_WORKSPACE_EDITOR = "code"
$env:THEBITLAB_EDITOR = "code"
```

#### Prompt dei comandi (solo sessione corrente)

```cmd
set THEBITLAB_WORKSPACE_EDITOR=code
set THEBITLAB_EDITOR=code
```

#### Resa permanente con `setx` (PowerShell)

```powershell
setx THEBITLAB_WORKSPACE_EDITOR "code"
setx THEBITLAB_EDITOR "code"
```

> Dopo `setx` chiudi e riapri il terminale perche' le variabili non si applicano alla finestra corrente.

#### Resa permanente dalle impostazioni Windows

1. Cerca "Modifica le variabili di ambiente relative al sistema".
2. Clicca su **Variabili d'ambiente**.
3. Nella sezione **Variabili utente** clicca **Nuova**.
4. Nome: `THEBITLAB_WORKSPACE_EDITOR`, Valore: `code`.
5. Ripeti per `THEBITLAB_EDITOR` se vuoi usare VS Code anche per `v`.

### 3. Usare la TUI

```powershell
cd E:\dev\2cornot2c
python scripts\student_lab_cli.py --server-url https://app.thebitpoets.com --pair-browser
```

Dopo il pairing:

- premi `v` per aprire il file sorgente in VS Code;
- premi `o` per aprire la cartella del workspace in VS Code.

## Configurare Notepad++ (Windows)

Notepad++ apre file singoli, non cartelle. E' adatto al comando `v`:

```cmd
set THEBITLAB_EDITOR="C:\Program Files\Notepad++\notepad++.exe"
```

Il comando `o` continuera' a usare il file manager.

## Configurare VSCodium

VSCodium e' la versione open source di VS Code. Dopo averlo installato e averlo aggiunto al PATH, usa:

```powershell
$env:THEBITLAB_WORKSPACE_EDITOR = "codium"
$env:THEBITLAB_EDITOR = "codium"
```

## Configurare editor Linux/macOS

Su Linux e macOS le variabili si esportano nello shell:

```bash
export THEBITLAB_WORKSPACE_EDITOR="code"
export THEBITLAB_EDITOR="micro"
```

Per renderle permanenti, aggiungi le due righe a `~/.bashrc` (Linux) o `~/.zshrc` (macOS).

## Disabilitare l'editor personalizzato e tornare al default

Rimuovi le variabili d'ambiente:

```powershell
Remove-Item Env:\THEBITLAB_WORKSPACE_EDITOR
Remove-Item Env:\THEBITLAB_EDITOR
```

oppure, nel Prompt dei comandi:

```cmd
set THEBITLAB_WORKSPACE_EDITOR=
set THEBITLAB_EDITOR=
```

A quel punto:

- `v` tornera a cercare `micro`, `nvim`, `vim`, `hx`, `nano` (e `notepad` su Windows);
- `o` aprira' la cartella con il file manager di sistema.

## Risoluzione problemi

### "Editor non avviabile: [WinError 2] Impossibile trovare il file specificato"

L'eseguibile indicato non e' nel `PATH` oppure il percorso completo e' errato.
Verifica con `where nome` (cmd) o `Get-Command nome` (PowerShell).

### `o` apre il file manager invece di VS Code

La variabile `THEBITLAB_WORKSPACE_EDITOR` non e' impostata oppure `THEBITLAB_EDITOR`
punta a un editor che la TUI non riconosce come in grado di aprire cartelle.
Imposta esplicitamente `THEBITLAB_WORKSPACE_EDITOR=code`.
