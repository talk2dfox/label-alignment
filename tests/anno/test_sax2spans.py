"""
test routines to load my XML text with span annotations 

Copyright (C) 2024-present David C. Fox <talk2dfox@gmail.com>
"""
import pytest


from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from collections import Counter

from pathlib import Path

import xml.sax 
from xml.sax.handler import ContentHandler

from label_alignment.annotation.span_annotation import SpanAnnotation

from label_alignment.annotation.sax2spans import (
        SpanAndText, text_and_spans, 
        find_consec_whitespace,
        span_parsed,
        )


def count_entities(text : str, 
        annos : Sequence[SpanAnnotation]) -> Dict[str,Counter]:
    by_label : Dict[str, Counter] = {}
    for anno in annos:
        entity = text[anno.start:anno.end]
        by_label.setdefault(anno.label, 
                Counter()).update([entity])
    return by_label


def test_parse_verne(verne_ch5_excerpt, v5_by_label) -> None:
    text : str
    annos : List[SpanAnnotation]
    text, annos = span_parsed(verne_ch5_excerpt)
    assert(len(find_consec_whitespace(text)) == 0)
    found = count_entities(text, annos)
    assert(found == v5_by_label)








# vim: et ai si sts=4   
