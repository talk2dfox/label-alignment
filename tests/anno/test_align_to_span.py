"""
joint tests of alignment.py and tok2spans / iob_state

Copyright (C) 2024-present David C. Fox <talk2dfox@gmail.com>
"""
import pytest

import re

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from label_alignment import alignment
from label_alignment import tok2spans
from label_alignment.annotation.span_annotation import SpanAnnotation
from label_alignment.tokenization.tokenized import Tokenized
from label_alignment.annotation.labeled import LabeledSpan

# first do a simple smoke test - will alignment run with
# output of wss_tok?

def initial_nonspaces(text : str) -> str:
    m : Optional[re.Match] = re.match(r'\S*', text)
    found : str  = m.group() if m else ''
    return found

def expand_to_spaces(text : str, 
        span_annos: Sequence[SpanAnnotation],
        debug : bool = False) -> List[SpanAnnotation]:
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

def get_aligned(text : str, tokenized : Tokenized, 
        span_annos : Sequence[SpanAnnotation]) -> List[str]:
    annos = [span_anno.to_labeled_span() for span_anno 
            in span_annos]
    aligned = alignment.align_tokens_and_annotations_bilou(tokenized, annos)
    return aligned

def test_alignment_with_wss_verne(wss_tok_verne_ch5) -> None:
    text, wss_tokenized, span_annos = wss_tok_verne_ch5
    aligned = get_aligned(text, wss_tokenized, span_annos)
    nspans = list(tok2spans.iob2spans(wss_tokenized.tokens, aligned))
    assert(len(nspans) == len(span_annos))
    expanded = expand_to_spaces(text, span_annos, debug=False)
    assert(expanded == nspans)
    realigned = get_aligned(text, wss_tokenized, nspans)
    respanned = list(tok2spans.iob2spans(wss_tokenized.tokens, realigned))
    assert(len(respanned) == len(span_annos))
    print(respanned[:5])
    print(span_annos[:5])
    assert(respanned == nspans)







# vim: et ai si sts=4   

