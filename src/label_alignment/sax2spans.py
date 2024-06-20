"""
Classes to parse simple XML and separate out text and spans

Copyright 2024-present David Fox
"""

from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import Locator

from typing import (Sequence, Mapping, Union, Optional,
        Tuple, List, Dict
        )

from .span_annotation import SpanAnnotation

class Reporter(ContentHandler):
    """
    Simple SAX-based reader to extract an idealized
    reference text and corresonding SpanAnnotation
    markers
    """
    def __init__(self) -> None:
        super().__init__()
        self.locator = None

    def setDocumentLocator(self, locator : Locator) -> None:
        super().setDocumentLocator(locator)
        print(locator)
        self.locator = locator

    def startElement(self, 
            name : str, 
            attrs : Mapping[str, str],
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
    def __init__(self) -> None:
        super().__init__()
        self.paragraphs = []
        self.current_paragraph = None
        self.current_tag = None
        self.current_text = {}

    def startParagraph(self, attrs : Mapping[str, str]) -> None:
        print('starting paragraph')
        self.current_paragraph = []
        self.current_text = {}

    def endParagraph(self):
        print('ending paragraph')
        self.paragraphs.append(self.current_paragraph)
        self.current_paragraph = None

    def maybe_append_current(self):
        if self.current_text:
            self.current_paragraph.append(self.current_text)
        self.current_text = {}
    def startElement(self, 
            name : str, 
            attrs : Mapping[str, str],
            ) -> None:
        if name == 'doc':
            print('starting doc')
            return
        if name == 'p':
            self.startParagraph(attrs)
        else:
            print(f'starting {name}')
            self.maybe_append_current()
            self.current_tag = name
            self.current_text['label'] = name


    def endElement(self, 
            name : str, 
            ) -> None:
        if name == 'doc':
            print('ending doc')
            print(f'{len(self.paragraphs)} paragraphs')
            return
        if name == 'p':
            self.maybe_append_current()
            self.endParagraph()
        else:
            print(f'ending {name}')
            self.maybe_append_current()
            self.current_tag = None
            self.current_text = {}

    def characters(self, ch : str) -> None:
        if self.current_paragraph is None:
            print('ignoring text outside paragraphs')
            return
        self.current_text['text'] = (
                self.current_text.get('text', '') + ch
                )
    def text_and_spans(self) -> Tuple[str, List[SpanAnnotation]]:
        start_of_paragraph : int = 0
        annos = []
        chunks = []
        for paragraph in self.paragraphs:
            offset : int = start_of_paragraph
            chunk : Optional[str] = None
            for chunk in paragraph:
                chunk_text = chunk.get('text')
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
        return (''.join(chunks), annos)





        


# vim: et ai si sts=4
