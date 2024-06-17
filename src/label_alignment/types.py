from typing import Sequence, Mapping, Union, Optional, TypedDict

class LabeledSpan(TypedDict):
    start : int
    end : int
    label : str
