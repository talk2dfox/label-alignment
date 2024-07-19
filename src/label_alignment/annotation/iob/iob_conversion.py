"""
conversions between different variants of IOB tagging

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
import sys

from abc import ABC, abstractmethod
from enum import Enum

from typing import (
        Sequence, Mapping, Generator,
        Dict, Tuple, Set,
        Union, Optional,
        Callable,
        )

from .iob_labels import (
        ParsedLabel, ParsedLabelString, parse_label,
        update_label,
        Prefix, Desc, Label,
        )

from functools import wraps

# prefixes where we end the token outside any chunk
valid_outside_prefixes = set([None, "", " ", "O"])

# prefixes where we end the token inside a chunk
valid_inside_prefixes = set(["B", "I",]) 

# prefixes where are inside a token but end the token outside any chunk
valid_outgoing_prefixes = set(["E", "L", "U", "S"])

prefix2description = {
        "O": "outside",
        "I": "inside",
        "B": "begin",
        "L": "last",
        "E": "last",
        "U": "single",
        "S": "single",
        }




GetNextDescription = Callable[[ParsedLabel, ParsedLabel], Desc]
GetNextDescAndError = Callable[[ParsedLabel, ParsedLabel], 
        Tuple[Desc, str]]
DescriptionMap = Mapping[Desc, GetNextDescAndError]
DescriptionDict = Dict[Desc, GetNextDescAndError]


class BeginTag(Enum):
    """
    an iob-style schema could have no B- labels (IO),
    or B could be required (IOB2), or could be 
    required only when necessary to separate two adjacent
    chunks of the same type
    """
    OMITTED = 0
    REQUIRED = 1
    DISAMBIG = 2

    
class Schema(object):
    """
    Schema represents a specific variant of IOB-style 
    tagging

    The core of the representation is a dictionary
    mapping from prefix descriptions:

    ["begin", "inside", "outside", "last", "single"]

    to corresponding prefixes:
    ["B", "I", "O", "L" or "E", "S" or "U"]
    
    with the caveat that some descriptions may not
    have a corresponding prefix in a given schema

    Note: it is unclear whether last makes sense without
    single (or if we only have I, O and last)
    """
    def __init__(self,
            begin : BeginTag = BeginTag.REQUIRED,
            single : Prefix = 'B',
            last : Prefix = 'I', 
            outside : Optional[Prefix] = 'O'
            ) -> None:
        """
        create a Schema object configured as follows:

        begin:
        - REQUIRED => no chunk can start with
          I (with default values of last and single, 
          this is also known as IOB2).  
        - DISAMBIG => B is only used to start a chunk
          if the preceeding token is a chunk with the same
          chunk class (with default last and single, this
          is also known as IOB1)
        - OMITTED => B is omitted.  With default last
          and single this is IO


        last: special tag for end of chunk.  The
          default "I" means no special tag, though
          in fact that means the end of a chunk can be
          "I" (for multi-token chunk) or "B" (for 
          single-token chunk).  Note: If begin is not
          OMITTED, and last is not "I", then single cannot 
          be "B"

        single: special tag for single-token chunk.  Default
          "B" means no special tag for single-token chunks.
          (but should not be used if last is not "I")

        outside: just allows a schema to use " ", "", or None
          to tag tokens outside any chunk, with no logical
          consequences.
        """
        self._mappings : Dict[Desc, Prefix] = {}
        self._check_ambig : Dict[Prefix, Set[Desc]] = {} # reverse map used to detect duplicates
        self.rmap : Dict[Prefix, Desc] = {} # unambiguous reverse map
        self.begin : BeginTag = begin
        self.last : Prefix = last
        self.single : Prefix = single
        self.outside : Optional[Prefix] = outside


        self.map_and_reverse_outside(outside)
        self.map_and_reverse('inside', 'I')

        self.bare_I : bool

        if self.begin == BeginTag.OMITTED:
            self.bare_I = True
        else:
            self.map_and_reverse('begin', 'B')
            self.bare_I = (
                    True if self.begin == BeginTag.DISAMBIG 
                    else False
                    )

        if last != 'I':
            self.map_and_reverse('last', last)
            if single == 'B':
                msg = 'given prefix for last token in chunk, '
                msg = msg + 'must have prefix for single-token chunk'
                raise ValueError(msg)
        if single != 'B':
            self.map_and_reverse('single', single)

        err_msg : Optional[str] = self.check_for_ambiguous_prefixes()
        if err_msg is not None:
            raise ValueError(err_msg)

    @classmethod
    def IOB1(cls) -> "Schema":
        return cls(begin=BeginTag.DISAMBIG)
    @classmethod
    def IOB2(cls) -> "Schema":
        return cls(begin=BeginTag.REQUIRED)
    @classmethod
    def std_explicit(cls) -> "Schema":
        """
        use BILOU from annotation as start or
        end for all conversions
        """
        return cls(last='L', single='U')

    def is_unambig(self) -> bool:
        if self.begin in (BeginTag.DISAMBIG, BeginTag.REQUIRED):
            return True
        return False

    def is_explicit(self) -> bool:
        desc : Desc
        for desc in ('begin', 'single', 'last'):
            if desc not in self._mappings:
                return False 
        return True

    def desc2prefix(self, description : Desc) -> Prefix:
        op : Optional[Prefix] = self._mappings.get(description)
        return op

    def map_and_reverse(self, description : Desc, 
            prefix : Prefix) -> None:
        """
        add a mapping from description to prefix
        and add/update the reverse entry in check_ambig
        """
        self._mappings[description] = prefix
        self._check_ambig.setdefault(prefix, set()).add(description)
    def map_and_reverse_outside(self, 
            prefix : Prefix) -> None:
        """
        add a mapping from "outside" to optional prefix
        and add/update the reverse entry in check_ambig
        """
        description : str = "outside"
        # allow desc2prefix to distinguish between
        # no mapping and mapping of outside to None
        eff_prefix : str
        if prefix is None:
            eff_prefix = ""
            # omit from _mappings, but still add to _check_ambig
            # with effective prefix
        else:
            eff_prefix = prefix
            self._mappings[description] = eff_prefix
        self._check_ambig.setdefault(eff_prefix, set()).add(description)


    def check_for_ambiguous_prefixes(self) -> Optional[str]:
        """
        if any character prefixes are ambiguous, return 
        error message, otherwise construct the
        unique reverse map and return None
        """
        chars = sorted(set(self._check_ambig))
        rmap : Dict[Prefix, Desc] = {} # unambiguous reverse map
        for char in chars:
            descs = self._check_ambig[char]
            if len(descs) > 1:
                msg = 'multiple classes ('
                msg = msg + ', '.join(sorted(descs)) + ') '
                msg = msg + f'assigned to {char}'
                print(msg)
                return msg
            else:
                rmap[char] = list(descs)[0]
        self.rmap = rmap
        return None

    def handles_desc(self, description : Desc) -> bool:
        """
        does this schema have a prefix specific to the
        given description?
        """
        return description in self._mappings




# conversions
def noop_warning(reason : str, 
        specific : bool = True) -> str:
    msg : str = f"Warning: given schema {reason}, "
    if specific:
        conv = "this conversion"
        noop = "a no-op"
    else:
        conv = "all conversions"
        noop = "no-ops"
    msg = msg + f"so {conv} will be {noop}"
    sys.stderr.write(msg)
    return msg

class Conversion(ABC):
    @abstractmethod
    def convert(self, orig : Sequence[Label]) -> Generator[Label, None, None]:
        """
        convert IOB-style labels from current schema
        to a new one (with both schema specified
        in constructor of subclass implementing convert
        """
        pass

    def noop_convert(self, orig : Sequence[Label]) -> Generator[Label, None, None]:
        """
        in some cases, factory creating a concrete subclass
        to implement convert may only know when convert is 
        called whether that conversion is a no-op.  If
        so, it can use this implementation
        """
        label : Label
        for label in orig:
            yield label

class ConversionImplBase(object):
    """
    common elements implementation of Schema conversion
    implemented as a finite state transducer.
    """
    def __init__(self, 
            target : Schema,
            ) -> None:
        super().__init__()
        self.prev : ParsedLabel = ParsedLabelString(prefix="O")
        self.prev_desc = 'outside'
        self.target : Schema = target

    def next_label(self, current : ParsedLabel,
            ) -> ParsedLabel:
        desc : Desc = self.current_description(current)
        print('orig desc:', desc)
        new_desc : Desc = self.next_description(current,
                current_desc=desc)
#        print(f'next label for {new_desc!r}')
        print('new desc:', new_desc)
        self.prev = current
        self.prev_desc = desc # or should this be new_desc!?
        parsed : ParsedLabel
        parsed = self.description2label(current,
                new_desc)
        return parsed

    @classmethod
    def prefix2desc(cls, p : Prefix):
        desc : Desc = prefix2description[p]
        return desc

    @classmethod
    def current_description(cls, current : ParsedLabel,
            ) -> Desc:
        """
        get current description from current prefix
        """
        return cls.prefix2desc(current.prefix)

    @abstractmethod
    def next_description(self, current : ParsedLabel,
            current_desc : Desc,
            ) -> Desc:
        """
        given current parsed label in original schema,
        and corresponding description,
        find new description in the target schema,
        handle any errors and return the new description
        """
        pass

    def description2label(self, current : ParsedLabel,
            new_desc : Desc,
            ) -> ParsedLabel:
        prefix : Prefix
        prefix = self.target.desc2prefix(new_desc)
        updated : ParsedLabel = update_label(current,
                new_prefix=prefix)
#        print('updated label:', updated)
        return updated


class FromExplicitConversionImpl(ConversionImplBase):
    """
    FromExplicitConversionImpl implements the conversion from
    an explicit Schema to an arbitrary schema as a finite state
    transducer.

    All Schema must include inside and outside, so 
    on conversion, inside -> inside, and outside -> outside

    If no "last", then last -> I

    If we see begin and schema.begin == REQUIRED, then 
    we map begin -> begin.

    If we see begin but schema.begin != REQUIRED, then
    we need to check 

    (a) whether prev prefix was an inside prefix, and
    (b) whether the previous chunk class matches the current one

    if both are true, then we either map begin -> begin 
    (when schema.begin == DISAMBIG) or raise an error
    (when schema.begin == OMIT), otherwise

    Finally, if no "single", then single -> begin, and we then 
    apply the logic above for begin

    Note: 
    1. the only logic which depends on previous label is begin
    2. the actual conditionals are the same regardless of
    whether schema.begin is DISAMBIG or OMIT)

    Therefore, we can implement that logic once in 
    the translation, rather than in the individual transition 
    functions.  In fact, since the mappings themselves are 
    trivial apart from this logic, we don't need the transition
    functions at all.

    Finally, we don't need to separate UnambigSchema from Schema
    or have separate conversion implementations for the two cases.
    """
    def __init__(self, 
            target : Schema,
            ) -> None:
        super().__init__(target)

    def safe_to_drop_begin(self, current : ParsedLabel) -> bool:
        """
        is it safe to drop begin from current label and
        replace with inside?
        """
        ambig : bool = (
                (self.prev_desc not in ('last', 'single', 'outside'))

                and 

                (self.prev.chunk_class == current.chunk_class )
            )
        return not ambig

    def begin_logic(self, current : ParsedLabel) -> Desc:
        """
        central place to handle begin logic
        """
        if self.target.begin == BeginTag.REQUIRED:
            return "begin"
        return self.drop_begin(current)
            

    def drop_begin(self, 
            current : ParsedLabel
            ) -> Desc:
        """
        drop begin or raise error
        """
        safe : bool = self.safe_to_drop_begin(current=current)
        if safe:
            return 'inside'
        if self.target.begin == BeginTag.DISAMBIG:
            return 'begin'
        msg = f"Two consecutive {current.chunk_class} chunks"
        msg = msg + " cannot be annotated"
        msg = msg + " in a schema with no B- prefix"
        raise ValueError(msg)

    def next_description(self, current : ParsedLabel,
            current_desc : Desc,
            ) -> Desc:
        """
        given current parsed label in original schema,
        and corresponding description,
        find new description in the target schema,
        handle any errors and return the new description
        """
#        print('prefix: ', current.prefix)
#        print('yields description ', desc)
        if current_desc in ('inside', 'outside'):
            return current_desc
        if current_desc in 'begin':
            return self.begin_logic(current)
        elif current_desc == 'last':
            if self.target.last != 'I':
                return current_desc
            return 'inside'
        if current_desc == 'single':
            if self.target.single != 'B':
                return current_desc
            return self.begin_logic(current)

        raise ValueError(f'Unexpected description {desc}')
        # this should never happen unless there is a bug
        # or misconfiguration in Schema or here, 
        # but is a safe way to satisfy type-checkers


class RestoreBeginConversionImpl(object):
    def __init__(self, 
            target : Schema,
            ) -> None:
        super().__init__(target)

    def next_description(self, current : ParsedLabel,
            current_desc : Desc,
            ) -> Desc:
        """
        given current parsed label in original schema,
        and corresponding description,
        find new description in the target schema,
        handle any errors and return the new description
        """
        if current_desc != 'inside':
            return current_desc
        if self.prev_desc in ('outside', 'last', 'single'):
            # current "inside" unambiguously begins a new chunk
            # so we only convert it to "begin" if we are
            # always requiring "begin"
            if self.target.begin == BeginTag.REQUIRED:
                return 'begin'
            return current_desc
        if self.prev_desc in ('inside', 'begin'):
                current

class RestoreBegin(Conversion):
    """
    implements Conversion.convert to add
    begin tags to tokenized text tagged
    in an IO schema 
    """
    def __init__(self, 
            schema : Schema,
            begin : BeginTag = BeginTag.REQUIRED,
            noop_msg : str = ""):
        self.orig_schema : Schema = schema
        self.begin_target : BeginTag = begin
        self.noop_msg = noop_msg
    def convert(self, 
            orig_labels : Sequence[Label]
            ) -> Generator[Label, None, None]:
        if self.noop_msg:
            sys.stderr.write(self.noop_msg)
            return noop_convert(orig_labels=orig_labels)





class Explicit2ArbitrarySchema(Conversion):
    def __init__(self, explicit : Schema,
            target : Schema) -> None:
        if not explicit.is_explicit():
            raise ValueError('schema called explicit is not')
        self.target : Schema = target

    def convert(self, orig_labels : Sequence[Label]) -> Generator[Label, None, None]:
        label : str
        print('in convert')
        converter : FromExplicitConversionImpl = \
                FromExplicitConversionImpl(self.target)
        for label in orig_labels:
            print('orig:', label)
            parsed : ParsedLabel = parse_label(label)
            print(parsed)
            new_parsed : ParsedLabel = converter.next_label(parsed)
            print(new_parsed)
            yield new_parsed.as_label()



class FromExplicit:
    """
    factory object returning conversions from "explicit"
    schema to different unambiguous schemas
    """

    def __init__(self, explicit : Optional[Schema] = None):
        explicit = explicit or Schema.std_explicit()
        if not explicit.is_explicit():
            raise ValueError('schema called explicit is not')
        self.explicit = explicit
    def to_arbitrary(self, unambig : Schema) -> Conversion:
        return Explicit2ArbitrarySchema(self.explicit, unambig)

class FromNonExplicit:
    """
    factory object returning conversions from
    a non-explicit schema to a more explict one.
    """

    def __init__(self, schema : Schema) -> None:
        if schema.is_explicit():
            noop_warning("is already explicit",
                    specific=False)
        self.orig_schema = schema

    def restore_begin(self, begin : BeginTag = BeginTag.REQUIRED) -> Conversion:
        """
        return an object with a conversion method
        which will restore begin tags to a schema without
        them (typically IO-only)
        """
        if begin == BeginTag.OMITTED:
            msg = 'to restore begin, must specify '
            msg = 'a value of begin other than OMITTED'
            raise ValueError(msg)
        noop_msg : str = ""
        if self.orig_schema.begin == BeginTag.REQUIRED:
            noop_msg = noop_warning('requires begin tags',
                    specific=True)
        elif (
                self.orig_schema.begin == BeginTag.DISAMBIG

                and

                begin == BeginTag.DISAMBIG
                ):
            noop_msg = noop_warning('already uses begin tags for disambiguation', specific=True)

        return RestoreBegin(schema=self.orig_schema,
                begin=begin,
                noop_msg=noop_msg)


class FromIO:
    """
    factory object returning conversions from
    an IO schema to schema which include a B tag
    (whether always required or only when required
    to disambiguate)
    """

    def __init__(self, io_schema : Schema) -> None:
        if not explicit.is_explicit():
            raise ValueError('schema called explicit is not')
        self.explicit = explicit
    def to_arbitrary(self, unambig : Schema) -> Conversion:
        return Explicit2ArbitrarySchema(self.explicit, unambig)


# vim: et ai si sts=4

