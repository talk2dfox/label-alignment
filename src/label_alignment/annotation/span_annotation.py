"""
SpanAnnotation class representing annotated spans,
used by sax2spans.py

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (
        Sequence, Mapping, Union, Optional,
#        Sized,
        Self,
        Tuple, List, Dict,
        )
from collections.abc import Iterator

from .labeled import LabeledSpan

class SpanAnnotation(object):
    """
    Annotated Span (complete or incomplete)
    and associated methods
    """
    def __init__(self, start : int,
            label : str,
            end : int = -1) -> None:
        self.start = start
        self.label = label
        self.end = end
    def __str__(self):
        return f'{self.label}: ({self.start}, {self.end})'
    def __repr__(self):
        r = '{cls}({label}, {start}, {end})'
        filled = r.format(cls='SpanAnnotation',
                label=self.label,
                start=self.start,
                end=self.end)
#        {
#            'cls': type(self), 
#            'label': self.label,
#            'start': self.start,
#            'end': self.end,
#            }
#            )
            
        return filled
    def __eq__(self, other : object) -> bool:
        if not isinstance(other, SpanAnnotation):
            raise NotImplemented
        return (
                (self.start == other.start)
                and
                (self.end == other.end)
                and
                (self.label == other.label)
                )
    @classmethod
    def from_labeled_span(cls, labeled : LabeledSpan) -> Self:
        return cls(start=labeled['start'],
                end=labeled['end'],
                label = labeled['label'])

    def to_labeled_span(self) -> LabeledSpan:
        return LabeledSpan(start=self.start,
                label=self.label,
                end=self.end)

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

    def intersection(self, 
            other : Self) -> Optional[Tuple[int, int]]:
        """
        find intersection with another SpanAnnotation,
        returning tuple of bounds on intersection if non-empty,
        else None
        """
        left = max(self.start, other.start)
        right = min(self.end, other.end)
        if left < right:
            return (left, right)
        return None

def partial_order(spans : Sequence[SpanAnnotation]) -> List[SpanAnnotation]:
    """
    given a sequence of SpanAnnotations, return a list
    in sorted order.

    Takes O(N) space and O(N log N) time

    mathematically, this is a partial ordering, because
    it uses only the start attributes
    """
    sorted_spans : List[SpanAnnotation] = \
            sorted(spans, key=lambda el: el.start)
    return sorted_spans

def are_disjoint(spans : Sequence[SpanAnnotation]) -> bool:
    """
    verify that a sequence of SpanAnnotations has no
    nested or overlapping spans
    """
    sorted_spans : List[SpanAnnotation] = partial_order(spans)
    if len(sorted_spans) < 2:
        return True
    ordered : Iterator[SpanAnnotation] = iter(sorted_spans)
    prev : SpanAnnotation = next(ordered)
    for span in ordered:
        if prev.intersection(span):
            return False
    return True

def compare_annotation(spans : Sequence[SpanAnnotation],
        other_spans : Sequence[SpanAnnotation]) \
                -> Dict:
    """
    TODO: finish

    Note: compare_annotation ASSUMES that each sequence
    is disjoint 
    """
    ordered : List[SpanAnnotation] = partial_order(spans)
    other_ordered : List[SpanAnnotation] = partial_order(other_spans)
    if len(ordered) == 0 or len(other_ordered) == 0:
        return {}
    i = iter(spans)
    io = iter(other_spans)
    return {}





# vim: et ai si sts=4

