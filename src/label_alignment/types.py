from typing import Sequence, Mapping, Union, Optional, TypedDict

class Annotation(TypedDict):
    start: int
    end: int
    label: str

    @classmethod
    def open(cls, start: int, label: str = "CHUNK") -> Annotation:
        """
        create an open (unfinished) annotation with a start 
        offset but no end (end==-1)
        """
        return cls(start=start, end=-1, label=label)

    def close(self, end: int) -> None:
        self.end = end

    def reopen(self) -> None:
        self.end = -1

class IOBState:
    def __init__(self, default_class : str = "CHUNK"):
        # note: by convention, offset will be the start of 
        # the next token to be seen. If we have seen
        # at least one token, then the previous token
        # ended at self.offset - 1
        self.offset : int = 0
        self.inside : Optional[Annotation] = None
        self.default : str = default_class
    def start_new_annotation(self, label : Optional[str] = None):
        self.inside = Annotation.open(
                start=self.offset,
                label=label or self.default
                )

    def see(self, token : str, 
            label : str) -> Optional[Annotation]:
        """
        given state and next token and label,
        transition to a new state (or remain in the same one),
        optionally emitting a completed Annotation
        """
        wc = label.split('-', max_split=1)
        which : str
        cat : Optional[str]
        which, cat = wc[0], wc[1:] or None
        to_emit : Annotation = None
        if which == "O":
            if self.inside:
                to_emit = self.end_current(token)
        elif which == "I":
            if self.inside: # if we are inside an existing
                # annotation, then either
                # (1) "I" will have no specified class or 
                # one matching the class of the current 
                # annotation, in which case that annotation 
                # continues, or
                # (2) "I" will have a different class, in 
                # which case that annotation continues and a
                # new one starts
                if (
                        cat is None # unspecified, must be continuation
                        or cat == self.inside.label 
                        ):
                    pass
                else:
                    to_emit = self.end_current(token)
                    self.start_new_annotation(cat)
            else:
                self.start_new_annotation(cat)
        elif which in 'BUS':
            if self.inside:
                to_emit = self.end_current(token)
            self.start_new_annotation(cat)
        elif which == 'E':
            pass
        else:
            raise ValueError(f'Unknown label type {which}')
        self.advance(token)
        # ugh E U S create a new annotation, but may also terminate and exising
        # annotation, so we'd have to return one or two annotations 
        # (and if we turn this into a generator, we can't yield two results from
        # a single next)



    def advance(self, token : str):
        self.offset += len(token) + 1
    def end_current(self, token : str):
        to_emit = self.inside
        # if self.inside is not None
        # then there was a previous token.  Then,
        # according to the convention above in __init__
        # self.offset will represent the start of the new token
        # and while the end of prev token would have been
        # self.offset - 1
        if to_emit is not None:
            to_emit.end = self.offset - 1
        self.inside = None
        return to_emit




        pass





# vim: et ai si sts=4

