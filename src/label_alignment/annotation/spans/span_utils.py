"""
helper functions for working with 
SpanAnnotation class representing annotated spans

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

import re

from typing import (
        Sequence, Mapping, Union, Optional,
#        Sized,
        Self,
        Tuple, List, Dict,
        Generator,
        )
from collections.abc import Iterator

from .labeled import LabeledSpan
from .span_annotation import SpanAnnotation

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


# spacing issues with SpanAnnotation and space-tokenization

def initial_nonspaces(text : str) -> str:
    """
    helper function to find first (space-delimited)
    "word" in text
    """
    m : Optional[re.Match] = re.match(r'\S*', text)
    found : str  = m.group() if m else ''
    return found

def expand_to_spaces(text : str, 
        span_annos: Sequence[SpanAnnotation],
        debug : bool = False) -> List[SpanAnnotation]:
    """
    given span annotations which may start or end within
    a (space-delimited) word, expand the annotation to
    the minimal space-delimited superset
    """
    expanded = []
    for span in span_annos:
        orig = text[span.start:span.end]
        after = initial_nonspaces(text[span.end:])
        tbefore = text[:span.start]
        rev = ''.join(reversed(tbefore))
        if debug:
            print(tbefore)
            print(rev)
        before = initial_nonspaces(rev)
        if debug:
            print(f'"{orig}" "{after}" "{before}"')
        new_span = SpanAnnotation(start=span.start - len(before), 
                end=span.end + len(after),
                label=span.label)
        expanded.append(new_span)
    return expanded

# adaptor to turn Sequence[SpanAnnotation] into Sequence[LabeledSpan]
def span_anno2labeled_spans(
        span_annos : Sequence[SpanAnnotation]) -> List[LabeledSpan]:
    return [span_anno.to_labeled_span() for span_anno           
                            in span_annos]



# vim: et ai si sts=4

