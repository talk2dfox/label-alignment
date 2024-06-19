from typing import (
        Sequence, Mapping, Union, Optional,
#        Sized,
        )

#from .types import LabeledSpan

class SpanAnnotation():
    def __init__(self, start : int,
            label : str,
            end : int = -1) -> None:
        self.start = start
        self.label = label
        self.end = end

    def is_open(self) -> bool:
        return self.end == -1

    def is_closed(self) -> bool:
        return self.end >= 0

    def __len__(self) -> int:
        if self.end == -1:
            return -1
        return self.end-self.start
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

