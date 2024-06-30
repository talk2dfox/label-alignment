"""
test iob_conversion using alignment.py

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
        Generator,
        Iterable,
        )

from label_alignment import alignment
from label_alignment import tok2spans
from label_alignment.annotation.spans.span_annotation import SpanAnnotation
from label_alignment.tokenization.tokenized import (
        Tokenized,
        StrTokenized,
        TokenizedIntOrStr,
        STokOut
        )
from label_alignment.annotation.spans.labeled import LabeledSpan, LabeledText
from label_alignment.annotation.iob.iob_conversion import (
        UnambigSchema,
        FromExplicit,
        Conversion,
        )

from label_alignment.annotation.iob.iob_labels import (
        Label, Prefix, ParsedLabel, parse_label,
        )

from label_alignment.annotation.spans.span_utils import (
        expand_to_spaces,
        span_anno2labeled_spans,
        )

# first test: explicit schema -> unambig
#
# - verne has span anno, readable with sax2spans
# - alignment produces explicit schema from span anno
# - then convert
# - iob2spans takes any schema and turns it back into 
#   spans, which we can compare to original 
#   (module space-delimited vs. not)

def align_spans(tokenized : TokenizedIntOrStr, 
        span_annos : Sequence[SpanAnnotation]) -> List[str]:
    lab_spans : List[LabeledSpan] = span_anno2labeled_spans(span_annos)
    aligned : List[str] = alignment.align_tokens_and_annotations_bilou(tokenized, lab_spans)
    return aligned

#    nspans = list(tok2spans.iob2spans(nized.tokens, aligned))


def explicit_to_unambig_labeled_text(target : UnambigSchema, 
        str_toked : STokOut) -> Iterable[LabeledText]:
    text : str
    nized : StrTokenized
    annos : List[SpanAnnotation]
    text, nized, annos = str_toked

    aligned : List[str] = align_spans(nized, annos)


    # convert to target schema
    from_explicit = FromExplicit()
    converter : Conversion = from_explicit.to_unambig(target)
    target_labels : Generator[str, None, None] = converter.convert(aligned)
    return map(lambda labtok : LabeledText(text=labtok[0],
        label=labtok[1]), zip(nized.tokens, target_labels))


def explicit_to_unambig(target : UnambigSchema, 
        str_toked : STokOut) -> List[SpanAnnotation]:

    labeled_text : List[LabeledText] = list(explicit_to_unambig_labeled_text(target,
            str_toked))



    nspans : List[SpanAnnotation] = list(
            tok2spans.iob_labeled2spans(labeled_text)
            )
    return nspans
#    assert(len(nspans) == len(space_annos))


def translate_labels(orig_labels : Iterable[Label],
        last : Prefix = "L",
        single : Prefix = "U",
        ) -> Iterable[Label]:
    expected_mapping : Dict[Prefix, Prefix] = {
            'L' : last,
            'U' : single,
            }
    for orig in orig_labels:
        parsed : ParsedLabel = parse_label(orig)
        trans_prefix : Prefix = expected_mapping.get(parsed.prefix,
                parsed.prefix)
        upd : ParsedLabel = ParsedLabel(prefix=trans_prefix, 
                chunk_class = parsed.chunk_class)
        yield upd.as_string()
    


@pytest.mark.parametrize("bare_I,last,single,outside", 
        [
            (False, "E", "U", "O"),
            (False, "E", "S", "O"),
            (False, "L", "S", "O"),
            (False, "L", "U", "O"),
            ]
        )
class TestExplicit:
    @staticmethod
    def test_is_explicit(wss_tok_verne_ch5,
            bare_I : bool, 
            last : str, 
            single : str, 
            outside : str,
            ) -> None:

        target : UnambigSchema = UnambigSchema(bare_I=bare_I, last=last, single=single, outside=outside)
        assert(target.is_explicit())
    @staticmethod
    def test_explicit2explicit(aligned_verne_ch5,
            bare_I : bool, 
            last : str, 
            single : str, 
            outside : str,
            ) -> None:
        target : UnambigSchema = UnambigSchema(bare_I=bare_I, last=last, single=single, outside=outside)
        to_target : Conversion = FromExplicit().to_unambig(target)
        orig_labels : List[str] = aligned_verne_ch5
        trans_labels : List[str] = list(to_target.convert(orig_labels))
        expected = list(translate_labels(orig_labels, last=last,
            single=single))
        assert(trans_labels == expected)





@pytest.mark.parametrize("bare_I,last,single,outside", 
        [
            (False, "L", "U", "O"),
            (False, "I", "B", " "),
            (True, "I", "B", "O"),
            (False, "E", "S", "O"),
            (False, "L", "S", "O"),
            (False, "E", "U", "O"),
            ]
        )
def test_explicit_params_to_unambig(wss_tok_verne_ch5, bare_I, last, single, outside) -> None:
    # pick target schema
    target : UnambigSchema = UnambigSchema(bare_I=bare_I, last=last, single=single, outside=outside)

    text : str
    wss_tokenized : StrTokenized
    span_annos : List[SpanAnnotation]
    text, wss_tokenized, span_annos = wss_tok_verne_ch5
    nspans = explicit_to_unambig(target,
            wss_tok_verne_ch5)
    # reference list of span anno for comparison
    reference_annos : List[SpanAnnotation] = expand_to_spaces(
            text,
            span_annos)
    assert(nspans == reference_annos)


# vim: et ai si sts=4   
