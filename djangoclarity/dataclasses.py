from dataclasses import dataclass


@dataclass
class ReadOnlyField:
    name: str
    label_tag: str
    value: str | None
