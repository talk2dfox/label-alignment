"""
Classes to parse simple XML and separate out text and spans

Copyright 2024-present David Fox
"""

import re

from pathlib import Path
from typing import (Sequence, Mapping, Union, Optional,
        Tuple, List, Dict
        )

import xml.sax
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import Locator, AttributesImpl

from .span_annotation import SpanAnnotation
from .types import LabeledText


class Reporter(ContentHandler):
    """
    Simple SAX-based reader to extract an idealized
    reference text and corresonding SpanAnnotation
    markers
    """
    def __init__(self) -> None:
        super().__init__()
        self.locator : Optional[Locator] = None

    def setDocumentLocator(self, locator : Locator) -> None:
        super().setDocumentLocator(locator)
        print(locator)
        self.locator = locator

    def startElement(self, 
            name : str, 
            attrs : AttributesImpl,
            ) -> None:
        print(f'starting {name}')

    def endElement(self, 
            name : str, 
            ) -> None:
        print(f'ending {name}')

    def characters(self, ch : str) -> None:
        print(f'{len(ch)} characters')
        


# vim: et ai si sts=4
class SpanAndText(ContentHandler):
    """
    Simple SAX-based reader to extract an idealized
    reference text and corresonding SpanAnnotation
    markers
    """
    def __init__(self, verbose : int = 0) -> None:
        super().__init__()
        self.verbose : int = verbose
        self.paragraphs : List[List[LabeledText]] = []
        self.current_paragraph : List[LabeledText] = []
        self.current_tag : Optional[str] = None
        self.current_text : Optional[str] = None

    def startParagraph(self, attrs : AttributesImpl) -> None:
        if self.verbose:
            print('starting paragraph')
        self.current_paragraph = []
        self.current_text = None

    def endParagraph(self):
        if self.verbose:
            print('ending paragraph')
        self.paragraphs.append(self.current_paragraph)
        self.current_paragraph = None

    def maybe_append_current(self):
        if self.current_text is not None:
            to_add = LabeledText(text=self.current_text,
                    label=self.current_tag)
            self.current_paragraph.append(to_add)
        self.current_text = None

    def startElement(self, 
            name : str, 
            attrs : AttributesImpl,
            ) -> None:
        if name == 'doc':
            if self.verbose:
                print('starting doc')
            return
        if name == 'p':
            self.startParagraph(attrs)
        else:
            if self.verbose:
                print(f'starting {name}')
            self.maybe_append_current()
            self.current_tag = name


    def endElement(self, 
            name : str, 
            ) -> None:
        if name == 'doc':
            if self.verbose:
                print('ending doc')
                print(f'{len(self.paragraphs)} paragraphs')
            return
        if name == 'p':
            self.maybe_append_current()
            self.endParagraph()
        else:
            if self.verbose:
                print(f'ending {name}')
            self.maybe_append_current()
            self.current_tag = None
            self.current_text = None

    def characters(self, ch : str) -> None:
        if self.current_paragraph is None:
            if self.verbose:
                print('ignoring text outside paragraphs')
            return
        self.current_text = (self.current_text or '') + ch


def text_and_spans(parsed : SpanAndText) -> Tuple[str, List[SpanAnnotation]]:
    start_of_paragraph : int = 0
    annos : List[SpanAnnotation] = []
    chunks : List[str] = []
    paragraph : List[LabeledText] = []
    for paragraph in parsed.paragraphs:
        offset : int = start_of_paragraph
        chunk : LabeledText
        for chunk in paragraph:
            chunk_text : str = chunk.get('text', '')
            chunks.append(chunk_text)
            chunk_label = chunk.get('label')
            if chunk_label:
                anno = SpanAnnotation(start=offset,
                        label=chunk_label,
                        end=offset + len(chunk_text))
                annos.append(anno)
            offset += len(chunk_text)
        pbreak = '\n' 
        chunks.append(pbreak)
        offset += len(pbreak)
        start_of_paragraph = offset
    text = ''.join(chunks)
    return (''.join(chunks), annos)

def find_consec_whitespace(text : str) -> List[SpanAnnotation]:
    """
    One of the purposes of text_and_spans is to test round-trips
    through alignment.align_tokens_and_annotations_bilou
    followed by tok2spans.iob2spans

    However, annotation spans will only match after
    this round-trip if there are no consecutive whitespace
    characters in the resulting text.
    """
    if not re.search(r'\s\s+', text):
        return []
    consec : List[SpanAnnotation] = []
    for m in re.finditer(r'\s\s+', text):
        consec.append(SpanAnnotation(start=m.start(),
            end=m.end(), label='consec-ws'))
    return consec


def span_parsed(p : Union[Path, str]) -> Tuple[str, List[SpanAnnotation]]:
    sat : SpanAndText = SpanAndText()
    xml.sax.parse(p, handler=sat)
    return text_and_spans(sat)







    


# vim: et ai si sts=4
