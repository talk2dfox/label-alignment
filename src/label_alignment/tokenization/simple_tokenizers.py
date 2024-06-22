"""
define simple tokenizers for testing alignment
and tok2spans

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (
        Sequence, Mapping, 
        Union, Optional,
        List, Dict, Tuple
        )

from bisect import bisect_right
from itertools import chain

from .tokenized import Tokenized

import tokenizers
import tokenizers.pre_tokenizers as pre_tokenizers

TokOut = List[Tuple[str, tokenizers.Offsets]]

def flatten(list_of_lists):
    "Flatten one level of nesting."
    return chain.from_iterable(list_of_lists)

class TokenizedImpl:
    def __init__(self, tok_out : TokOut) -> None:
        self.tok_out : TokOut = tok_out
        self.bounds = list(
                flatten(
                    x[1] for x in tok_out
                    )
                )
        self._tokens = tuple(x[0] for x in tok_out)
    @property
    def tokens(self):
        return self._tokens

    def char_to_token(self, char_ix: int) -> Optional[int]:
        i_all : int = bisect_right(self.bounds, char_ix)
        if i_all % 2 == 0:
            return None
        tok_ix : int = (i_all - 1) // 2
        return tok_ix


class PretokenizerWrapper:
    def __init__(self, pretok : pre_tokenizers.PreTokenizer) -> None:
        self.pretok = pretok
    def raw_tokenize(self, text : str) -> TokOut:
        pre_tok_output : TokOut
        pre_tok_output = self.pretok.pre_tokenize_str(text)
        return pre_tok_output
    def tokenize(self, text : str) -> TokenizedImpl:
        pre_tok_output : TokOut = self.raw_tokenize(text)
        return TokenizedImpl(pre_tok_output)

def ws_tokenizer() -> PretokenizerWrapper:
    return PretokenizerWrapper(pre_tokenizers.Whitespace())
def wss_tokenizer() -> PretokenizerWrapper:
    return PretokenizerWrapper(pre_tokenizers.WhitespaceSplit())




# vim: et ai si sts=4
