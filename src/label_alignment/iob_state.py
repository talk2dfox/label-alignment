"""
classes implementing a state machine for interpreting
IOB-style sequence tagging

see
    https://en.wikipedia.org/wiki/Inside%E2%80%93outside%E2%80%93beginning_(tagging)

for more about IOB tagging and its variants.

Supports any of the following schema:

- IOB1 (IOB but B only used for adjacent chunks of the 
    same type)
- IOB2 (IOB with B required (no bare I)
- IO (not distinguishing between first and subsequent 
    tokens in a chunk, at the cost of being unable to 
    represent sequences with two adjacent tokens of the 
    same class)
- IOB plus E/L (ending token of an annotation)
    and/or U/S (either U or S represents a class spanning 
    only a single token)

Note: this state machine is permissive, which allows it 
to accept any of the schema above.  However, this
means that it cannot validate any specific scheme

Copyright (c) 2024-present David C. Fox (talk2dfox@gmail.com)
"""

from abc import ABC, abstractmethod
from typing import Sequence, Mapping, Union, Optional

from .annotation.span_annotation import SpanAnnotation


def delim_width_before(token : str, 
        prev_token : Optional[str]) -> int:
    """
    default delim_width function which assume a single
    (space) character between all tokens

        For most tokenizations, delim_width can be omitted,
        as it will be assumed to be 1 
        (as returned by delim_width_before)

        However, if your tokenization supports sub-word tokens
        (e.g. WordPiece or BytePair encodings, or even
        simple systems which split hyphenated words into
        multiple tokens), then you should pass a function
        which, given the previous and current tokens, will
        return either 0 or 1

    """
    return 1

class UnexpectedLabel(ValueError):
    def __init__(self, msg : str) -> None:
        self.msg = msg
    def __str__(self):
        return self.msg

class IOBState(ABC):
    """
    abstract base class for state in IOB sequence tagging schema

    Note: current implementation assumes that the tokens are 
    all separated by single spaces
    """
    def __init__(self, prev_token : Optional[str] = None, 
            end_of_previous : int = 0, 
            default_class : str = "CHUNK",
#            delim_width : Callable[str, int] = delim_width_before,
            ) -> None:
        """
        initialize common attributes of IOBState

        end_of_previous is the offset of the end of
        the previous token.  

        default_class allows you to omit the
        class portion of the label when you are only
        annotating a single class of chunks.

        Note: since IOBState is an abstract base class,
        this method will be called only from __init__ of
        a concrete subclass via super()
        """
        super().__init__()
        self.default : str = default_class
        self.prev_token = prev_token
        self.end_of_previous : int = end_of_previous

    @abstractmethod
    def pending_annotation(self) -> Optional[SpanAnnotation]:
        return None
    @abstractmethod
    def current_annotation(self) -> Optional[SpanAnnotation]:
        return None
    def new_annotation(self, label : Optional[str] = None) -> SpanAnnotation:
        """
        create a new 'open' annotation (one with end == -1)
        starting at the current location
        """
        start = self.end_of_previous + (self.prev_token is not None)
        # handles special case of no delimiter before first token
        return SpanAnnotation.open(
                start=start,
                label=label or self.default
                )

    def end_of_text(self) -> Optional[SpanAnnotation]:
        """
        owner MUST call end_of_text when there are no more tokens
        to ensure than any pending SpanAnnotation gets returned.
        """
        # default implementation (returning None) can be used
        # unless we are Inside, or Outside with pending
        return None

    @abstractmethod
    def see(self, token : str, 
            label : Optional[str] = None) -> tuple["IOBState", Optional[SpanAnnotation]]:
        """
        given next token and label,
        update the offset of the end of the previous token,
        and return 
        (1) subsequent IOBState (possibly the same state
        instance), and
        (2) when appropriate, the next complete SpanAnnotation.
        """
        pass

    @classmethod
    def interpret_label(cls, 
            label : Optional[str] = None) -> tuple[str, Optional[str]]:
        if not label or label == " ":
            return ("O", None)
        wc = label.split('-', maxsplit=1)
        which : str
        cat : Optional[str] = None
        which = wc[0][0]
        if wc[1:]:
            cat = wc[1]
        return (which, cat)

SeeReturn = tuple[IOBState, Optional[SpanAnnotation]]

class Outside(IOBState):
    def __init__(self, prev_token : Optional[str] = None,
            end_of_previous : int = 0,
            pending_anno : Optional[SpanAnnotation] = None,
            default_class : str = "CHUNK",
            ) -> None:
        super().__init__(prev_token=prev_token, end_of_previous=end_of_previous, default_class=default_class)
        self.pending_anno = pending_anno
    def pending_annotation(self) -> Optional[SpanAnnotation]:
        return self.pending_anno
    def current_annotation(self) -> Optional[SpanAnnotation]:
        return None
    def end_of_text(self) -> Optional[SpanAnnotation]:
        """
        owner MUST call end_of_text when there are no more tokens
        to ensure than any pending SpanAnnotation gets returned.
        """
        return self.pending_anno

    def see(self, token : str,
            label : Optional[str] = None) -> SeeReturn:
        """
        given next token and label,
        update the offset of the end of the previous token,
        and return 
        (1) subsequent IOBState (possibly the same state
        instance), and
        (2) when appropriate, the next complete SpanAnnotation.
        """
        to_emit = self.pending_anno
        which : str
        cat : Optional[str]
        which, cat = self.interpret_label(label)
        end_of_current = self.end_of_previous + len(token) + (self.prev_token is not None)
        # outside, so possibilities are:
        # 1. stay outside
        # 2. start new chunk and
        #    a. change state to inside, or
        #    b. end the new chunk, and continue outside

        # possibility 1
        if which == "O":
            self.prev_token = token
            self.end_of_previous = end_of_current
            self.pending_anno = None
            # still outside, so clear pending_anno and 
            # return self (Outside)
            # if there was a pending annotation, emit it
            return (self, to_emit)
        # we are outside, so no existing chunk to 
        # finish and return

        # not one of expected possibilities,
        # so raise exception
        if which in "EL":
            msg = f"not expecting {which} (end of anno) when Outside any current SpanAnnotation"
            raise UnexpectedLabel(msg)

        # possibility 2, so create new (incomplete) annotation
        new_anno = self.new_annotation(label=cat)
        if which in "BI":
            # 2.a continue to inside, keeping incomplete
            # annotation, rather than returning it
            new_state = Inside(prev_token=token,
                    end_of_previous=end_of_current,
                    current_anno = new_anno,
                    default_class = self.default)
            return (new_state, to_emit)
        # or finally possibility 2.b
        elif which in "US":
            # transition to outside
            self.prev_token = token
            self.end_of_previous = end_of_current
            # close new anno, but save it as pending,
            # returning to_emit
            new_anno.close(end=end_of_current)
            self.pending_anno = new_anno
            return (self, to_emit)

        # finally, raise exception for unknown label
        msg = f"unknown label-type {which}"
        raise UnexpectedLabel(msg)

class Inside(IOBState):
    def __init__(self, prev_token,
            end_of_previous : int,
            current_anno : SpanAnnotation,
            default_class : str = "CHUNK",
            ) -> None:
        super().__init__(prev_token=prev_token, end_of_previous=end_of_previous, default_class=default_class)
        self.current_anno = current_anno
    def pending_annotation(self) -> Optional[SpanAnnotation]:
        return None
    def current_annotation(self) -> Optional[SpanAnnotation]:
        return self.current_anno
    def end_of_text(self) -> Optional[SpanAnnotation]:
        """
        owner MUST call end_of_text when there are no more tokens
        to ensure than any pending SpanAnnotation gets returned.
        """
        self.current_anno.close(end=self.end_of_previous)
        return self.current_anno

    def see(self, token : str,
            label : Optional[str] = None) -> SeeReturn:
        """
        given next token and label,
        update the offset of the end of the previous token,
        and return 
        (1) subsequent IOBState (possibly the same state
        instance), and
        (2) when appropriate, the next complete SpanAnnotation.
        """
        which : str
        cat : Optional[str]
        which, cat = self.interpret_label(label)
        end_of_current = self.end_of_previous + len(token) + 1

        # inside, so possibilities are
        # 1. new label is outside (O), or explicitly ends the 
        #    current annotation without starting a new one 
        #    (E/L), so close and return current annotation 
        #    and transition to outside
        # 2. new label (U/S) explicitly starts a single-token 
        #    annotation, so close and return current annotation
        #    and transition to Outside (pending) so we can emit
        #    the new annotation on next token (or end of text)
        # 3. new label explicitly starts a new annotation,
        #    or is inconsistent with current one
        #    so close and return current annotation, start
        #    new one, and transition to new inside state
        # 4. new label is consistent with current one, so
        #    continue inside

        if which not in "BIOUSEL": # none of the above
            msg = f"unknown label-type {which}"
            raise UnexpectedLabel(msg)

        # prepare to update offset
        end_of_current = self.end_of_previous + len(token) + 1
        if (
                which == "I" and
                (
                    cat is None # unspecified, must be continuation
                    or cat == self.current_anno.label
                    )
                ): # possibility 4, so don't emit anything
            # just stay inside and update offset
            self.prev_token = token
            self.end_of_previous = end_of_current
            return (self, None)
            

#       already handled unexpected and I-consistent,
#       so we know we have "BOEUS" or I-inconsistent
#       therefore existing anno ends
        to_emit : SpanAnnotation = self.current_anno
        if which in "EL":  # if current token is included
            to_emit.close(end=end_of_current)
        else:
            to_emit.close(end=self.end_of_previous)
        
        if which in "ELO":
            # possibility 1
            # no new annotation, so transition to Outside
            new_state = Outside(prev_token=token,
                    end_of_previous=end_of_current,
                    default_class=self.default)
            return (new_state, to_emit)

        current_anno : SpanAnnotation = self.new_annotation(
                label=cat)
        if which in "US":
            # possibility 2
            # new anno ends, but we already have an
            # existing anno to emit, so we have to
            # transition to Outside pending
            # to save the new anno for emission next
            # call to see() or end()
            current_anno.close(end=end_of_current)

            new_state = Outside(prev_token=token,
                    end_of_previous=end_of_current,
                    pending_anno=current_anno,
                    default_class=self.default,)
            return (new_state, to_emit)

        # otherwise, possibility 3, new anno starts but
        # doesn't end, so update current Inside, and 
        # emit previous anno 
        self.prev_token = token
        self.end_of_previous = end_of_current

        return (self, to_emit)


# vim: et ai si sts=4

