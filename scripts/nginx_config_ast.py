"""Shared token-aware nginx configuration parser for deployment security checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


class NginxConfigError(ValueError):
    """The nginx source is syntactically incomplete or ambiguous."""


@dataclass(frozen=True)
class Token:
    value: str
    line: int
    structural: bool = False


@dataclass(frozen=True)
class Directive:
    source: str
    name: str
    args: tuple[str, ...]
    children: tuple["Directive", ...] | None
    line: int


def tokenize_nginx(source: str, text: str) -> tuple[Token, ...]:
    tokens: list[Token] = []
    value: list[str] = []
    token_line = 1
    line = 1
    quote: str | None = None
    escaped = False
    index = 0

    def flush() -> None:
        nonlocal value
        if value:
            tokens.append(Token("".join(value), token_line))
            value = []

    while index < len(text):
        char = text[index]
        if escaped:
            value.append(char)
            escaped = False
            if char == "\n":
                line += 1
            index += 1
            continue
        if char == "\\":
            if not value:
                token_line = line
            escaped = True
            index += 1
            continue
        if quote is not None:
            if char == quote:
                quote = None
            else:
                value.append(char)
                if char == "\n":
                    line += 1
            index += 1
            continue
        if char in {"'", '"'}:
            if not value:
                token_line = line
            quote = char
            index += 1
            continue
        if char == "#":
            flush()
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline
            continue
        if char in "{};":
            flush()
            tokens.append(Token(char, line, structural=True))
            index += 1
            continue
        if char.isspace():
            flush()
            if char == "\n":
                line += 1
            index += 1
            continue
        if not value:
            token_line = line
        value.append(char)
        index += 1
    if escaped or quote is not None:
        raise NginxConfigError(f"Configurazione nginx ambigua in {source}: quote/escape incompleto")
    flush()
    return tuple(tokens)


def parse_nginx_source(source: str, text: str) -> tuple[Directive, ...]:
    tokens = tokenize_nginx(source, text)

    def parse_sequence(index: int, *, nested: bool) -> tuple[tuple[Directive, ...], int]:
        directives: list[Directive] = []
        words: list[Token] = []
        while index < len(tokens):
            token = tokens[index]
            if token.structural and token.value == "}":
                if words or not nested:
                    raise NginxConfigError(
                        f"Configurazione nginx malformata in {source}:{token.line}"
                    )
                return tuple(directives), index + 1
            if token.structural and token.value == ";":
                if not words:
                    raise NginxConfigError(f"Direttiva nginx vuota in {source}:{token.line}")
                directives.append(
                    Directive(
                        source,
                        words[0].value,
                        tuple(item.value for item in words[1:]),
                        None,
                        words[0].line,
                    )
                )
                words = []
                index += 1
                continue
            if token.structural and token.value == "{":
                if not words:
                    raise NginxConfigError(
                        f"Blocco nginx senza direttiva in {source}:{token.line}"
                    )
                children, index = parse_sequence(index + 1, nested=True)
                directives.append(
                    Directive(
                        source,
                        words[0].value,
                        tuple(item.value for item in words[1:]),
                        children,
                        words[0].line,
                    )
                )
                words = []
                continue
            words.append(token)
            index += 1
        if words or nested:
            line_number = words[0].line if words else (tokens[-1].line if tokens else 1)
            raise NginxConfigError(f"Configurazione nginx incompleta in {source}:{line_number}")
        return tuple(directives), index

    parsed, end = parse_sequence(0, nested=False)
    if end != len(tokens):
        raise NginxConfigError(f"Configurazione nginx non consumata in {source}")
    return parsed


def walk_directives(
    directives: Sequence[Directive], context: tuple[str, ...] = ()
) -> Iterable[tuple[Directive, tuple[str, ...]]]:
    for directive in directives:
        yield directive, context
        if directive.children is not None:
            yield from walk_directives(directive.children, context + (directive.name,))


def direct(directives: Sequence[Directive], name: str) -> list[Directive]:
    return [directive for directive in directives if directive.name == name]
