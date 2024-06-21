import pytest

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from label_alignment import alignment

# first do a simple smoke test - will alignment run with
# output of wss_tok?


def test_alignment_with_wss_verne(wss_tok_verne_ch5):
    text, wss_tokenized, span_annos = wss_tok_verne_ch5
    annos = [span_anno.to_labeled_span() for span_anno 
            in span_annos]
    aligned = alignment.align_tokens_and_annotations_bilou(wss_tokenized, annos)





# vim: et ai si sts=4   

