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
from label_alignment.annotation.spans.span_annotation import SpanAnnotation
from label_alignment.tokenization.tokenized import Tokenized, StrTokenized, TokenizedIntOrStr
from label_alignment.annotation.spans.labeled import LabeledSpan

from label_alignment.annotation.spans.span_utils import (
        expand_to_spaces,
        span_anno2labeled_spans,
        )




def test_alignment_with_wss_verne(wss_tok_verne_ch5) -> None:
    text : str
    wss_tokenized : StrTokenized
    span_annos : List[SpanAnnotation]
    text, wss_tokenized, span_annos = wss_tok_verne_ch5
    assert(span_annos[-1] == SpanAnnotation(start=1129, label='place', end=1138))
    aligned : List[str] = alignment.align_from_spans(wss_tokenized, span_annos)
    nspans : List[SpanAnnotation] = list(tok2spans.iob2spans(wss_tokenized.tokens, aligned))
    assert(len(nspans) == len(span_annos))
    expanded : List[SpanAnnotation] = expand_to_spaces(text, span_annos, debug=False)
    assert(expanded == nspans)
    realigned : List[str] = alignment.align_from_spans(wss_tokenized, nspans)
    respanned = list(tok2spans.iob2spans(wss_tokenized.tokens, realigned))
    assert(len(respanned) == len(span_annos))
    print(respanned[:5])
    print(span_annos[:5])
    assert(respanned == nspans)







# vim: et ai si sts=4   

