"""
TypedDict classes to simplify compatibility 
between alignment spans used by sax2spans.py and those
expected by alignment.py

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import (
        Sequence, Mapping, 
        Union, Optional, 
        TypedDict, NotRequired
        )

class LabeledSpan(TypedDict):
    """
    alignment routine expects dictionary-like
    access to start, end, label, which TypedDict
    provides

    Although TypedDicts can be defined in a way which looks 
    like a class, you can't define methods
    """
    start : int
    end : int
    label : str

class LabeledText(TypedDict):
    text : str
    label : NotRequired[str]

# vim: et ai si sts=4
