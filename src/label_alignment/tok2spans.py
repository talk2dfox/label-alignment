"""
align character-offset annotations to token boundaries

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (Sequence, Mapping, 
        Union, Optional, 
        )

from tokenizers import Encoding

from .types import Annotation

def iob2spans(tokens : Sequence[str], 
        labels : Sequence[str]
        ) -> Sequence[Annotation]:
    """
    given a sequence of string tokens and corresponding labels
    in IOB-style tagging, return corresponding annotations in 
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
    current_anno : Annotation = None
        

    offset: int = 0
    state: Optional[str] = None
    # using None for outside, otherwise lab
    annotations : list[Annotation] = []
    current_start: int = -1
    prev_token_end: int = -1
    for tok, label in zip(tokens, labels):
        prev_state: Optional[str] = state
        which, cat = label.split('-', max_split=1)
        if 
        if label



#    offset: int = 0
#    for tok, label in labeled_tokens:
#        offset


# vim: et ai si sts=4
