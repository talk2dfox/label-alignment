"""
common fixtures for tests using test data from ../data/annotations

note: because of the peculiar way in which pytest
makes conftest.py available, anything defined
in here conftest.py can be used here, but only
the @pytest.fixture functions can be used
in the test_ modules.

Copyright (C) 2024-present David C. Fox <talk2dfox@gmail.com>
"""
import pytest

from pathlib import Path

from collections import Counter

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from label_alignment.annotation.spans.span_annotation import SpanAnnotation

from label_alignment import alignment

import xml.sax 

from label_alignment.annotation.spans.sax2spans import (
        SpanAndText,
        text_and_spans,
        span_parsed,
        find_consec_whitespace,
        )

from label_alignment.tokenization.tokenized import Tokenized, StrTokenized, StrTokenizer, STokOut

from label_alignment.tokenization.simple_tokenizers import ws_tokenizer, wss_tokenizer


#--------------------
# Paths to data
#--------------------

@pytest.fixture
def data_path():
    return Path('tests') / 'data'

@pytest.fixture
def anno_path(data_path):
    return data_path / 'annotated_texts'

#--------------------
# Jules Verne as data
#--------------------


@pytest.fixture
def verne_ch5_excerpt(anno_path : Path) -> Path:
    return anno_path / 'verne_20000_leagues.ch5.xml'

@pytest.fixture
def v5_by_label() -> Dict[str, Counter[str]]:
    answers = {
            'vessel': Counter({'Abraham Lincoln': 2, 'Monroe': 1}),
            'person': Counter({'Ned Land': 4, 'Commander Farragut': 2}), 
            'date': Counter({'30th of June,': 1, '3rd of July': 1}), 
            'nationality': Counter({'American': 1}),
            'country': Counter({'America': 1}),
            'place': Counter({
                'Straits of Magellan': 1,
                'Cape Vierges': 1,
                'Cape Horn': 1})
         }
    return answers


@pytest.fixture
def ws_tok():
    return ws_tokenizer()

@pytest.fixture
def wss_tok():
    return wss_tokenizer()

#STokOut = Tuple[str, StrTokenized, List[SpanAnnotation]]
def tokenize(src, 
        tokenizer : StrTokenizer) -> STokOut:
    """
    standardize reading from XML-annotated text
    and tokenization 
    """
    text, annos = span_parsed(src)
    assert(len(find_consec_whitespace(text)) == 0)
    tokenized = tokenizer.tokenize(text)
    return text, tokenized, annos

@pytest.fixture
def wss_tok_verne_ch5(verne_ch5_excerpt : Path, wss_tok : StrTokenizer) -> STokOut:
    text : str
    nized : StrTokenized
    annos : List[SpanAnnotation]
    text, nized, annos = tokenize(verne_ch5_excerpt, wss_tok)
    return text, nized, annos

@pytest.fixture
def aligned_verne_ch5(wss_tok_verne_ch5 : STokOut) -> List[str]:
    text : str
    nized : StrTokenized
    annos : List[SpanAnnotation]
    text, nized, annos = wss_tok_verne_ch5
    orig_labels : List[str] = alignment.align_from_spans(nized, 
            annos)
    return orig_labels


# vim: et ai si sts=4   
