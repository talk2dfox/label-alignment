import pytest

import re

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )


def test_wss_tok(wss_tok_verne_ch5):
    text, wss_tokenized, annos = wss_tok_verne_ch5
    text = text.strip('\n')
    simple = re.split(r'\s', text)
    assert(len(simple) == len(wss_tokenized.tokens))
    assert(list(simple) == list(wss_tokenized.tokens))
#    print(len(text))
#    print(len(text.strip()))
    for i in range(len(text)):
        ti = wss_tokenized.char_to_token(i)
#        print(i, repr(text[i]), ti)
        if re.match(r'\s', text[i]):
            assert(ti is None)
        else:
            assert(ti is not None)






# vim: et ai si sts=4   

