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
    start : int
    end : int
    label : str

class LabeledText(TypedDict):
    text : str
    label : NotRequired[str]

