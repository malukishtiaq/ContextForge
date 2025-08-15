from typing import Optional, Protocol, TypedDict


class ParsedPage(TypedDict):
    page: int
    text: str
    blocks: list[dict]
    lang: Optional[str]


class Parser(Protocol):
    def parse(self, pdf_path: str) -> tuple[list[ParsedPage], dict]:
        ...


