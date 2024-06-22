"""
define tokenized interface for input to 
alignment.align_tokens_and_annotation_bilou

Copyright (C) 2024-present David Fox
"""

from typing import Protocol, List, Union, Optional

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



# vim: et ai si sts=4
