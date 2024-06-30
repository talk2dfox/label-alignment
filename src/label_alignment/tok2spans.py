"""
transform IOB-annotated tokens into character-offset annotations 
suitable as input to alignment.py

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (Iterable, Sequence, Mapping, 
        Union, Optional, Generator, Tuple,
        )

from .annotation.spans.span_annotation import SpanAnnotation

from .annotation.iob.iob_state import IOBState, Outside
from .annotation.spans.labeled import LabeledText

def zipped2labeled(zipped : Iterable[Tuple[str, str]]):
    for token, label in zipped:
        yield LabeledText(text=token, label=label)

def iob_labeled2spans(labeled : Iterable[LabeledText],
        default_class : str = "CHUNK"
        ) -> Generator[SpanAnnotation, None, None]:
    state : IOBState = Outside(default_class=default_class)
    maybe_anno : Optional[SpanAnnotation] = None
    to_emit: SpanAnnotation
    for labeled_token in labeled:
        print(labeled_token)
        state, maybe_anno = state.see(
                token=labeled_token["text"],
                label=labeled_token["label"],
                )
        if maybe_anno is not None:
            to_emit = maybe_anno
            yield to_emit
    final : Optional[SpanAnnotation] = state.end_of_text()
    if final is not None:
        yield final

def iob_zipped2spans(zipped: Iterable[Tuple[str, str]],
        default_class : str = "CHUNK"
        ) -> Generator[SpanAnnotation, None, None]:
    yield from iob_labeled2spans(zipped2labeled(zipped))

def iob2spans(tokens : Iterable[str],
        labels : Iterable[str],
        default_class : str = "CHUNK"
        ) -> Generator[SpanAnnotation, None, None]:
    """
    given a sequence of string tokens and corresponding labels
    in IOB-style tagging, yield corresponding annotations in 
    character offsets into the string which would result from
    concatening tokens with a single space as delimiter.

    see
    https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)

    for more about IOB tagging.

    iob2spans assumes that the labels are of the form

    "O": outside any chunk
    "B-<class>" first token in a chunk of the given <class>
    "I[-<class>]" inside (but not first token of ) a chunk of 
    given class. 

    as well as optional extensions

    "E[-<class>]" last token in a chunk of the given <class>,
    "U-<class>" or "S-<class>" single token (first and last) in a chunk 
    of the given class.

    iob2spans should work correctly for 
    (1) IOB1 (IOB but B only used for adjacent chunks of the 
        same type)
    (2) IOB2 (IOB with B required (no bare I)
    (2) IO (not distinguishing between first and subsequent 
        tokens in a chunk, at the cost of being unable to 
        represent sequences with two adjacent tokens of the 
        same class)
    (3) IOB plus E and/or U


    The "-<class>" suffix is required for B and U, but optional 
    for I (except in the IOB1 and IO cases) and E.
    """
    yield from iob_zipped2spans(
            zip(tokens, labels), 
            default_class=default_class,
            )


# vim: et ai si sts=4
