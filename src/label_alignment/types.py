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

