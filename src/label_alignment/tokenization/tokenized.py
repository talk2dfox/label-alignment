"""
define tokenized interface for input to 
alignment.align_tokens_and_annotation_bilou

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (
        Protocol, 
        List, Tuple,
        Union, Optional,
        Iterator
        )

from ..annotation.spans.span_annotation import SpanAnnotation

class Tokenized(Protocol):
    """
    defines subset of tokenizers.Encoding
    used by alignment.align_tokens_and_annotation_bilou
    """
    @property
    def tokens(self) -> List[Union[str,int]]:
        pass
    def char_to_token(self, char_ix : int) -> Optional[int]:
        pass

class StrTokenized(Protocol):
    """
    defines subset of tokenizers.Encoding
    used by alignment.align_tokens_and_annotation_bilou
    and iob2spans
    """
    @property
    def tokens(self) -> List[str]:
        pass
    def char_to_token(self, char_ix : int) -> Optional[int]:
        pass
    def __iter__(self) -> Iterator[str]:
        pass
    

class Tokenizer(Protocol):
    def tokenize(self, s : str) -> Tokenized:
        pass
class StrTokenizer(Protocol):
    def tokenize(self, s : str) -> StrTokenized:
        pass


TokenizedIntOrStr = Union[Tokenized, StrTokenized]

STokOut = Tuple[str, StrTokenized, List[SpanAnnotation]]   
# vim: et ai si sts=4
