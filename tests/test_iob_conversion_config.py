"""
Testing conversions among IOB schema

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

import label_alignment.annotation.iob.iob_conversion as iob_conv

def test_consistent_dicts():
    assert(set(iob_conv.prefix2description) ==
            set.union(iob_conv.valid_inside_prefixes, 
                iob_conv.valid_outgoing_prefixes,
                set("O")
                )
            )
# vim: et ai si sts=4   

