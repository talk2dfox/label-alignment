"""
align character-offset annotations to token boundaries

Copyright (c) 2020 LightTag

with additional changes (primarily type hints and docstrings) Copyright (c)
2024-present David C. Fox (talk2dfox@gmail.com)
"""

from typing import Sequence, Mapping, Union, Optional, List

from .tokenized import Tokenized



from .types import LabeledSpan

def align_tokens_and_annotations_bilou(tokenized: Tokenized, 
        annotations : Sequence[LabeledSpan]) -> List[str]:
    """
    given a sequence of annotations with keys "start" and "end" mapped to
    character offsets and "label" mapped to the annotation type,
    along with a tokenization in the form of HuggingFace tokenizers.Encoding,

    create a list of BILOU labels representing the same annotations, but
    aligned with the tokens
    """
    tokens = tokenized.tokens
    aligned_labels = ["O"] * len(
        tokens
    )  # Make a list to store our labels the same length as our tokens
    for anno in annotations:
        annotation_token_ix_set = (
            set()
        )  # A set that stores the token indices of the annotation
        for char_ix in range(anno["start"], anno["end"]):

            token_ix = tokenized.char_to_token(char_ix)
            if token_ix is not None:
                annotation_token_ix_set.add(token_ix)
        if len(annotation_token_ix_set) == 1:
            # If there is only one token
            token_ix = annotation_token_ix_set.pop()
            prefix = (
                "U"  # This annotation spans one token so is prefixed with U for unique
            )
            aligned_labels[token_ix] = f"{prefix}-{anno['label']}"

        else:

            last_token_in_anno_ix = len(annotation_token_ix_set) - 1
            for num, token_ix in enumerate(sorted(annotation_token_ix_set)):
                if num == 0:
                    prefix = "B"
                elif num == last_token_in_anno_ix:
                    prefix = "L"  # Its the last token
                else:
                    prefix = "I"  # We're inside of a multi token annotation
                aligned_labels[token_ix] = f"{prefix}-{anno['label']}"
    return aligned_labels

# vim: et ai si sts=4
