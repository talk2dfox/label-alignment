"""
Testing state machine from iob_state

Copyright (C) 2024-present David C. Fox <talk2dfox@gmail.com>
"""
import pytest

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from collections import OrderedDict

from label_alignment.annotation.spans.span_annotation import SpanAnnotation

from label_alignment.annotation.iob.iob_state import (
    IOBState, Inside, Outside,
    UnexpectedLabel,
    SeeReturn,
    )

from label_alignment.annotation.iob.iob_labels import interpret_label

IL = List[
        Tuple[str, #label
            Tuple[str, # bare label
                Optional[str] # class
                ]
            ]
        ]

@pytest.fixture
def interpreted_labels() -> IL:
    labint = [
        ("O", ("O", None)),
        ("I", ("I", None)),
        ("I-PER", ("I", "PER")),
        ("B-PER", ("B", "PER")),
        ("U-DATE", ("U", "DATE")),
        ("S-DATE", ("S", "DATE")),
        ("E", ("E", None)),
        ("E-TIME", ("E", "TIME")),
        ("O", ("O", None)),
        ("B-FOO-BAR", ("B", "FOO-BAR")),
        ]
    return labint
#    for lab, ans in labint:
#        yield lab, ans

def test_interpret_labels(interpreted_labels : IL) -> None:
    for lab, ans in interpreted_labels:
        assert(interpret_label(lab) == ans)

# vim: et ai si sts=4   

