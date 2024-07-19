"""
basic utilities for working with IOB-style labels

see
    https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from dataclasses import dataclass

from abc import ABC, abstractmethod

from typing import (
        Sequence, Mapping, Generator,
        Dict, Tuple, Set,
        Union, Optional,
        ParamSpec, Callable,
        )

Prefix = str
Desc = str
Label = Optional[str]
ChunkClass = Optional[str]

class ParsedLabel(ABC):
    @abstractmethod
    def as_label(self) -> Label:
        pass
    @abstractmethod
    def interpret(self) -> Tuple[str, ChunkClass]:
        pass



@dataclass
class ParsedLabelString(ParsedLabel):
    prefix : Prefix
    chunk_class : Optional[str] = None
    def as_label(self) -> Label:
        if self.chunk_class:
            return f'{self.prefix}-{self.chunk_class}'
        return self.prefix
    def interpret(self) -> Tuple[str, ChunkClass]:
        return (self.prefix.strip() or "O", self.chunk_class)

class ParsedLabelOutside(ParsedLabel):
    def as_label(self) -> Label:
        return None
    def interpret(self) -> Tuple[str, ChunkClass]:
        return ("O", None)


def from_interpreted(prefix : Prefix, chunk_class : ChunkClass = None):
    if prefix is None:
        return ParsedLabelOutside()
    return ParsedLabelString(prefix=prefix, chunk_class=chunk_class)

def interpret_label(label : Label) -> tuple[Prefix, ChunkClass]:
    p : ParsedLabel = parse_label(label)
    return p.interpret()

def interpret_string_label(label : str) -> tuple[str, ChunkClass]:
    """
    given label in form a string prefix and an optional class:
    "<prefix>[-<class>]", 
    return a 2-tuple of (<prefix>, Optional[<class>])
    """
    wc = label.split('-', maxsplit=1)
    prefix : str
    cat : Optional[str] = None
    prefix = wc[0]
    if wc[1:]:
        cat = wc[1]
    print('orig, prefix, cat:', label, prefix, repr(cat))
    return (prefix, cat)

def parse_label(label : Label) -> ParsedLabel:
    """
    version of interpret_label returning a ParsedLabel instead of a tuple
    """
    prefix : Prefix
    cat : ChunkClass
    if label is None:
        return ParsedLabelOutside()
    prefix, cat = interpret_string_label(label)
    return ParsedLabelString(prefix=prefix, chunk_class=cat)

def update_label(orig_parsed : ParsedLabel, new_prefix : Prefix):
    if new_prefix is None:
        return ParsedLabelOutside()
    return ParsedLabelString(prefix=new_prefix, 
            chunk_class=orig_parsed.chunk_class)
# vim: et ai si sts=4
