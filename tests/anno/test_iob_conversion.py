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
        Schema,
        FromExplicit,
        Conversion,
        BeginTag,
        )

from label_alignment.annotation.iob.iob_labels import (
        Label, Prefix, ChunkClass,
        ParsedLabel, ParsedLabelString, ParsedLabelOutside, 
        parse_label,
        interpret_label,
        from_interpreted,
        )

from label_alignment.annotation.spans.span_utils import (
        expand_to_spaces,
        span_anno2labeled_spans,
        )

# first test: explicit schema -> arbitrary
#
# - verne has span anno, readable with sax2spans
# - alignment produces explicit schema from span anno
# - then convert
# - iob2spans takes any schema and turns it back into 
#   spans, which we can compare to original 
#   (modulo space-delimited vs. not)
#
# TODO: need separate case for IO schema which can 
# fail to convert unambiguously
# 

def align_spans(tokenized : TokenizedIntOrStr, 
        span_annos : Sequence[SpanAnnotation]) -> List[str]:
    lab_spans : List[LabeledSpan] = span_anno2labeled_spans(span_annos)
    aligned : List[str] = alignment.align_tokens_and_annotations_bilou(tokenized, lab_spans)
    return aligned

#    nspans = list(tok2spans.iob2spans(nized.tokens, aligned))


def explicit_to_arbitrary_labeled(target : Schema, 
        str_toked : STokOut) -> Iterable[LabeledText]:
    text : str
    nized : StrTokenized
    annos : List[SpanAnnotation]
    text, nized, annos = str_toked
    print('nannos = ', len(annos))

    aligned : List[str] = align_spans(nized, annos)


    # convert to target schema
    from_explicit = FromExplicit()
    converter : Conversion = from_explicit.to_arbitrary(target)
    target_labels : Generator[Label, None, None] = converter.convert(aligned)
    return map(lambda labtok : LabeledText(text=labtok[0],
        label=labtok[1]), zip(nized.tokens, target_labels))


def explicit_to_arbitrary(target : Schema, 
        str_toked : STokOut) -> List[SpanAnnotation]:

    labeled_text : List[LabeledText] = list(explicit_to_arbitrary_labeled(target,
            str_toked))
    print('ex2a first token', labeled_text[0])

    nspans : List[SpanAnnotation] = list(
            tok2spans.iob_labeled2spans(labeled_text)
            )
    return nspans
#    assert(len(nspans) == len(space_annos))


def lso_translation(orig_labels : Iterable[Label],
        last : Prefix = "L",
        single : Prefix = "U",
        outside : Prefix = "O",
        ) -> Iterable[Label]:
    """
    simple alternative implementation of conversion 
    from explicit to explicit
    """
    expected_mapping : Dict[Prefix, Prefix] = {
            'L' : last,
            'U' : single,
            'O' : outside,
            }
    prev_class : Optional[Label] = None
    for orig in orig_labels:
        prefix : Prefix
        chunk_class : ChunkClass
        prefix, chunk_class = interpret_label(orig)
        trans_prefix : Prefix = expected_mapping.get(prefix,
                prefix)
            
        upd : ParsedLabel = from_interpreted(prefix=trans_prefix, 
                chunk_class = chunk_class)
        prev_class = chunk_class
        yield upd.as_label()
    

def begin_disambig(labels : Iterable[Label],
        ) -> Iterable[Label]:
    """
    remove non-required Begin tags
    """
    prev_class : Optional[Label] = None
    lab : Label
    for lab in labels:
        prefix : Prefix
        chunk_class : ChunkClass
        prefix, chunk_class = interpret_label(lab)
        if prefix == 'B' and \
                prev_class != chunk_class:
            pl : ParsedLabel = from_interpreted(prefix="I",
                    chunk_class = chunk_class)
            prev_class = chunk_class
            yield pl.as_label()
        else:
            prev_class = chunk_class
            yield lab



@pytest.mark.parametrize("begin,is_explicit", 
        [
            (BeginTag.REQUIRED, True),
            (BeginTag.DISAMBIG, True),
            (BeginTag.OMITTED, False),
            ]
        )
@pytest.mark.parametrize("last", ["E", "L"])
@pytest.mark.parametrize("single", ["S", "U"])
@pytest.mark.parametrize("outside", [None, "", " ", "O"])
class TestExplicitOrNot:
    @staticmethod
    def test_is_explicit(wss_tok_verne_ch5,
            begin : BeginTag,
            is_explicit : bool,
            last : str, 
            single : str, 
            outside : Optional[str],
            ) -> None:

        target : Schema = Schema(begin=begin, last=last, single=single, outside=outside)
        assert(target.is_explicit() == is_explicit)
    @staticmethod
    def test_explicit2explicit(aligned_verne_ch5,
            begin : BeginTag,
            is_explicit : bool,
            last : str, 
            single : str, 
            outside : str,
            ) -> None:
#        print(type(outside))
        target : Schema = Schema(begin=begin, last=last, single=single, outside=outside)
        to_target : Conversion = FromExplicit().to_arbitrary(target)
        assert(target.is_explicit() == is_explicit)
        if not target.is_explicit():
            assert(is_explicit == False)
            assert(target.begin == BeginTag.OMITTED)
            pytest.skip('skipping explicit2explicit b/c target is not explicit')
            return
        orig_labels : List[Label] = aligned_verne_ch5
        trans_labels : List[Label] = list(to_target.convert(orig_labels))
        # added a mapping from O to str(outside), which fixes that problem, 
        # and fixed a bug in begin_logic which was failing to keep begin
        # tags when begin==BeginTag.REQUIRED.
        # now only getting diffs for begin==BeginTag.DISAMBIG,
        # which makes sense.
        #
        # how do we test that case (without relying on the same implementation
        # of begin_logic)?
        itlab : Iterable[Label]
        itlab = lso_translation(orig_labels, last=last,
            single=single,
            outside=outside)
        if target.begin == BeginTag.DISAMBIG:
            itlab = begin_disambig(itlab)
        expected = list(itlab)
        assert(trans_labels == expected)





@pytest.mark.parametrize("last", ["I", "E", "L"])
@pytest.mark.parametrize("single", ["S", "U"])
def test_last_and_single(last : Prefix, single : Prefix):
    target : Schema = Schema(last=last, single=single)

@pytest.mark.parametrize("last", ["E", "L"])
@pytest.mark.parametrize("single", ["B"])
@pytest.mark.xfail(raises=ValueError)
def test_last_without_single(last : Prefix, single : Prefix):
    target : Schema = Schema(last=last, single=single)



#@pytest.mark.parametrize("bare_I,last,single,outside", 
#        [
#            (False, "L", "U", "O"),
#            (False, "I", "B", " "),
#            (True, "I", "B", "O"),
#            (False, "E", "S", "O"),
#            (False, "L", "S", "O"),
#            (False, "E", "U", "O"),
#            ]
#        )




@pytest.mark.parametrize("begin,is_explicit", 
        [
            (BeginTag.REQUIRED, True),
            (BeginTag.DISAMBIG, True),
            (BeginTag.OMITTED, False),
            ]
        )
@pytest.mark.parametrize("last", ["I", "E", "L"])
@pytest.mark.parametrize("single", ["S", "U"])
@pytest.mark.parametrize("outside", [None, "", " ", "O"])
def test_explicit_params_to_arbitrary(wss_tok_verne_ch5, 
        begin : BeginTag #=  BeginTag.REQUIRED
        , is_explicit : bool #= True 
        , last : Prefix# = "I"
        , single : Prefix# = "B"
        , outside : Optional[Prefix]# = "O",
        ) -> None:
    # pick target schema
    print(type(outside))
    target : Schema = Schema(begin=begin, last=last, single=single, outside=outside)

    text : str
    wss_tokenized : StrTokenized
    span_annos : List[SpanAnnotation]
    text, wss_tokenized, span_annos = wss_tok_verne_ch5
    nspans = explicit_to_arbitrary(target,
            wss_tok_verne_ch5)
    # reference list of span anno for comparison
    reference_annos : List[SpanAnnotation] = expand_to_spaces(
            text,
            span_annos)
    assert(nspans == reference_annos)


# vim: et ai si sts=4   
