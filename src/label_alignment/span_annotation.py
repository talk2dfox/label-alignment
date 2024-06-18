from typing import Sequence, Mapping, Union, Optional, Self

#from .types import LabeledSpan

class SpanAnnotation:
    def __init__(self, start : int,
            label : str,
            end : int = -1) -> None:
        self.start = start
        self.label = label
        self.end = end

    @classmethod
    def open(cls, start: int, 
            label: str = "CHUNK") -> "SpanAnnotation":
        """
        create new SpanAnnotation with no
        end (end == -1)
        """
        return SpanAnnotation(start=start, end=-1, label=label)

    def close(self, end: int) -> None:
        self.end = end

    def reopen(self) -> None:
        self.end = -1

# vim: et ai si sts=4

