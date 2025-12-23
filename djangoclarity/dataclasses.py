from dataclasses import dataclass


@dataclass(frozen=True)
class ReadOnlyField:
    field: str
    label_tag: str
