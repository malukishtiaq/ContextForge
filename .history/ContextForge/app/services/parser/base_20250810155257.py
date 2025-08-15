from typing import Protocol, TypedDict


class ParsedPage(TypedDict):
    page: int
    text: str
    blocks: list[dict]
    lang: str | None


class Parser(Protocol):
    def parse(self, pdf_path: str) -> tuple[list[ParsedPage], dict]:
        ...


