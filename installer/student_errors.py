"""Messaggi semplici e stabili mostrati agli studenti dall'installer."""

from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True, slots=True)
class StudentError:
    code: str
    title: str
    explanation: str
    actions: tuple[str, ...]

    def lines(self, technical: str = "") -> tuple[str, ...]:
        result = [
            f"ERRORE {self.code} - {self.title}",
            f"COSA SIGNIFICA: {self.explanation}",
            "COSA DEVI FARE:",
        ]
        result.extend(
            f"COSA FARE {index}: {action}"
            for index, action in enumerate(self.actions, 1)
        )
        result.append(f"CODICE DA COMUNICARE AL DOCENTE: {self.code}")
        if technical:
            result.append(f"Dettagli tecnici: {technical[:240]}")
        return tuple(result)


ERRORS = {
    "memory": StudentError(
        "E02",
        "Il computer non ha abbastanza memoria RAM",
        "La RAM è lo spazio di lavoro temporaneo del computer.",
        ("Chiudi gli altri programmi e riprova.", "Comunica E02 al docente."),
    ),
    "virtualization": StudentError(
        "E03",
        "La virtualizzazione del computer è disabilitata",
        "Docker e le VM ne hanno bisogno. Non hai rotto nulla.",
        (
            "Apri Gestione attività, poi Prestazioni e infine CPU.",
            "Con Intel cerca Intel Virtualization Technology oppure Intel VT-x.",
            "Con AMD cerca SVM Mode, AMD-V oppure Secure Virtual Machine.",
            "Fatti aiutare da un adulto e attiva soltanto quella voce.",
            "Non modificare Secure Boot, TPM o altre impostazioni.",
        ),
    ),
    "disk": StudentError(
        "E05",
        "Non c'è abbastanza spazio libero sul disco",
        "Serve spazio per conservare programmi ed esercizi.",
        (
            "Svuota il Cestino o sposta file personali.",
            "Non cancellare file che non riconosci; poi riprova.",
        ),
    ),
    "resources": StudentError(
        "E06",
        "Il controllo delle risorse non è riuscito",
        "RAM, disco o virtualizzazione non rispettano i requisiti.",
        ("Leggi i dettagli qui sotto.", "Comunica E06 al docente."),
    ),
    "network": StudentError(
        "E07",
        "Non riesco a collegarmi al server di download",
        "La procedura ha bisogno di Internet.",
        (
            "Controlla con il browser che Internet funzioni.",
            "Non disattivare l'antivirus; riprova o comunica E07.",
        ),
    ),
    "winget": StudentError(
        "E08",
        "Il programma di installazione di Windows non è disponibile",
        "winget è lo strumento ufficiale usato da Windows.",
        (
            "Aggiorna App Installer dal Microsoft Store.",
            "Riapri PowerShell e rilancia il comando.",
        ),
    ),
    "docker": StudentError(
        "E17",
        "Docker Desktop non è installato",
        "Docker avvia l'ambiente Linux leggero.",
        ("Conferma l'installazione dal menu.", "Accetta la richiesta di Windows."),
    ),
    "docker-engine": StudentError(
        "E19",
        "Docker Desktop non è riuscito a diventare pronto",
        (
            "Il setup lo ha già avviato e ha atteso automaticamente. "
            "Windows sta chiedendo un intervento che non può essere confermato "
            "al posto tuo."
        ),
        (
            "Guarda la finestra di Docker Desktop e premi Accetta o Continua.",
            "Se Windows chiede di riavviare, fallo.",
            "Dopo il riavvio rilancia lo stesso comando: riprenderà da solo.",
        ),
    ),
    "student-image": StudentError(
        "E21",
        "Non riesco a scaricare l'ambiente Linux",
        "Docker funziona, ma il download non è completo.",
        (
            "Lascia Docker Desktop aperto e controlla Internet.",
            "Rilancia l'installer: non perderai quanto già scaricato.",
        ),
    ),
    "student-security": StudentError(
        "E22",
        "L'ambiente Linux non supera il controllo di sicurezza",
        "Per sicurezza non verrà avviato nulla e il tuo lavoro resta intatto.",
        ("Non scaricare immagini alternative.", "Comunica E22 al docente."),
    ),
    "docker-command": StudentError(
        "E23",
        "PowerShell non riesce a trovare Docker",
        "Docker può essere appena stato installato e Windows non lo vede ancora.",
        (
            "Chiudi PowerShell e avvia Docker Desktop.",
            "Apri un nuovo PowerShell; se serve, riavvia Windows.",
        ),
    ),
    "container": StudentError(
        "E24",
        "L'ambiente Linux non è riuscito ad avviarsi",
        "Il tuo lavoro non è stato cancellato.",
        (
            "Controlla che Docker Desktop sia aperto e pronto.",
            "Riprova; se ricompare, comunica E24 al docente.",
        ),
    ),
    "terminal": StudentError(
        "E16",
        "Questo terminale non può mostrare il menu",
        "Serve un terminale interattivo.",
        ("Apri PowerShell o Windows Terminal.", "Rilancia lo stesso comando."),
    ),
}


def resource_error(detail: str) -> StudentError:
    blocked = next(
        (
            part
            for part in detail.split(";")
            if part.strip().lower().startswith("blocked")
        ),
        detail,
    )
    lowered = blocked.lower()
    if "virtualizzazione" in lowered:
        return ERRORS["virtualization"]
    if "ram " in lowered:
        return ERRORS["memory"]
    if "disco " in lowered:
        return ERRORS["disk"]
    return ERRORS["resources"]


def for_check(key: str, detail: str) -> StudentError:
    if key == "resources":
        return resource_error(detail)
    return ERRORS.get(
        key,
        StudentError(
            "E09",
            "Un componente necessario non è disponibile",
            "La procedura si è fermata senza cancellare il tuo lavoro.",
            ("Rilancia l'installer.", "Se ricompare, comunica E09 al docente."),
        ),
    )


def for_step(key: str) -> StudentError:
    if key == "docker":
        return StudentError(
            "E18",
            "Windows non è riuscito a installare Docker Desktop",
            "L'installazione è stata interrotta o non autorizzata.",
            (
                "Controlla se Windows aspetta una conferma.",
                "Riavvia e rilancia il comando; se ricompare comunica E18.",
            ),
        )
    return for_check(key, "")


def print_error(error: StudentError, technical: str = "") -> None:
    """Stampa rosso/giallo quando il terminale lo consente."""

    color = sys.stdout.isatty()
    for line in error.lines(technical):
        escape = "\x1b[31m" if line.startswith("ERRORE ") else "\x1b[33m"
        reset = "\x1b[0m" if color else ""
        print(f"{escape if color else ''}{line}{reset}")
