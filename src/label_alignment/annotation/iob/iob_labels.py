"""
basic utilities for working with IOB-style labels

see
    https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from dataclasses import dataclass

from typing import (
        Sequence, Mapping, Generator,
        Dict, Tuple, Set,
        Union, Optional,
        ParamSpec, Callable,
        )

Prefix = str
Desc = str
Label = str

@dataclass
class ParsedLabel:
    prefix : Prefix
    chunk_class : Optional[str] = None
    def as_string(self) -> Label:
        if self.chunk_class:
            return f'{self.prefix}-{self.chunk_class}'
        return self.prefix



def interpret_label(label : Optional[str] = None) -> tuple[Prefix, Optional[str]]:
    """
    given label in form a prefix and an optional class:
    "<prefix>[-<class>]", 
    return a 2-tuple of (<prefix>, Optional[<class>])
    """
    if not label or label == " ":
        return ("O", None)
    wc = label.split('-', maxsplit=1)
    prefix : str
    cat : Optional[str] = None
    prefix = wc[0][0]
    if wc[1:]:
        cat = wc[1]
    return (prefix, cat)

def parse_label(label : Optional[str] = None) -> ParsedLabel:
    """
    version of interpret_label returning a ParsedLabel instead of a tuple
    """
    prefix : Prefix
    cat : Optional[str]
    prefix, cat = interpret_label(label)
    return ParsedLabel(prefix=prefix, chunk_class=cat)

def update_label(orig_parsed : ParsedLabel, new_prefix : Prefix):
    return ParsedLabel(prefix=new_prefix, 
            chunk_class=orig_parsed.chunk_class)
# vim: et ai si sts=4
