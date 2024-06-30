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
from typing import (
        Sequence, Mapping, Generator,
        Dict, Tuple, Set,
        Union, Optional,
        Callable,
        )

from .iob_labels import (
        ParsedLabel, interpret_label, parse_label,
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


def never_error(orig : GetNextDescription) -> GetNextDescAndError:
    """
    function to build a 2-tuple of the label from orig and
    an empty string (indicating no error)
    """
    @wraps(orig)
    def _inner( prev_label : ParsedLabel, 
            current_label : ParsedLabel) -> Tuple[Desc, str]:
#    def _inner( *args: PS.args, **kwargs : PS.kwargs ) -> Tuple[Desc, str]:
        return (orig(prev_label, current_label), "")
    return _inner.__call__

# The following functions are used to configure implementations of Conversion
# They must all take the same arguments: prev_label : ParsedLabel, current_label
# : ParsedLabel and must return a 2-tuple:
#   (prefix_desc : str, error_msg : str)
# where prefix_desc is one of the values in prefix2description, 
# and an empty error_msg indicates no error
# Note: for simplicity, we use the never_error wrapper to add 
# empty error message in cases which should never return an error.
# functools.wraps copies the original docstring, so instead 
# of documenting the underlying function and then updating 
# that docstring, we just write the docstring for the 
# underlying function as if it returned the tuple


@never_error
def maybe_keep_B(prev_label : ParsedLabel, current_label : ParsedLabel)  -> Desc:
    """
    if we are converting to a schema where B is used only when the preceding token was
    labeled I and the current label and previous label are the same class,
    then maybe_keep_B will return a 2-tuple of
    (either "begin" or "inside" as appropriate, True)
    """
    if prev_label.prefix in valid_inside_prefixes and prev_label.chunk_class == current_label.chunk_class:
        return "begin"
    return "inside"

def never_B(
        prev_label : ParsedLabel, current_label : ParsedLabel
        ) -> Tuple[Desc, str]:
    """
    if we are converting to a schema which has no 'B'-prefix (beginning of new 
    chunk), then return a 2-tuple of "inside" (description of replacement
    prefix) and an error message (empty if no ambiguity)
    """
    ambig : bool = (prev_label.chunk_class == current_label.chunk_class 
            and prev_label.prefix not in valid_outgoing_prefixes)
    msg : str = ""
    if ambig:
        msg = f"Two consecutive tokens of class {current_label.chunk_class}"
        msg = msg + " which cannot be unambiguously annotated"
        msg = msg + " in a schema with no B- prefix"
        
    return ("inside", msg)

@never_error
def unchanged(
        prev_label : ParsedLabel, current_label : ParsedLabel
        ) -> Desc:
    """
    generic function to return the description associated with the new_prefix
    unchanged
    """
    return prefix2description[current_label.prefix]

@never_error
def drop_end(
        prev_label : ParsedLabel, current_label : ParsedLabel
        ) -> Desc: 
    """
    if converting to a schema with no last-token-of-chunk label (E/L),
    and see one, what do we replace it with?

    E would not be used for a single-token chunk, so we can
    always replace it with I

    technically, dropping the end symbol could cause ambiguity if the 
    schema has no begin labels, but we will ignore this
    """
    return "inside"

@never_error
def drop_single(
        prev_label : ParsedLabel, current_label : ParsedLabel
        ) -> Desc:
    """
    if converting to a schema with no single (S/U) token, and we see
    one, what do we replace it with?

    technically, dropping the single symbol could cause ambiguity 
    if the schema has end labels, but we will ignore this
    """
    return "begin"
    

class UnambigSchema(object):
    @classmethod
    def IOB1(cls) -> "UnambigSchema":
        return cls(bare_I=True)
    @classmethod
    def IOB2(cls) -> "UnambigSchema":
        return cls()
    @classmethod
    def std_explicit(cls) -> "UnambigSchema":
        """
        use BILOU from annotation as start or
        end for all conversions
        """
        return cls(last='L', single='U')

    def is_explicit(self) -> bool:
        if ('single' in self.mappings 
                and 'last' in self.mappings):
            return True
        return False

    def __init__(self, bare_I : bool = False,
            last : Prefix = 'I',
            single : Prefix = 'B',
            outside : Prefix = 'O') -> None:
        """
        describe any unambig schema above

        * bare_I - (is bare I allowed (IOB1) or not (IOB2)
        * last - label for last token in span
            * I means no special token for last
            * otherwise pass either E or L 
        * single - special label for annotation
          spanning only a single token 
            * B means no special token, just B
            * otherwise pass either U or S
        * outside: 'O' or ' ' or ''

        With defaults, => IOB2
        bare_I == True, but rest default => IOB1
        """
        super().__init__()
        self.bare_I = bare_I
        self.last = last
        self.single = single
        self.mappings : Dict[Desc, Prefix] = {}
        self.check_ambig : Dict[Prefix, Set[Desc]] = {} # reverse map used to detect duplicates
        self.rmap : Dict[Prefix, Desc] = {} # unambiguous
        # reverse map 
        self.map_and_reverse('begin', 'B')
        self.map_and_reverse('inside', 'I')
        if last != 'I':
            self.map_and_reverse('last', last)
        if single != 'B':
            self.map_and_reverse('single', single)
        self.map_and_reverse('outside', outside)
        err_msg : Optional[str] = self.check_for_ambiguous_prefixes()
        if err_msg is not None:
            raise ValueError(err_msg)

    def map_and_reverse(self, description : Desc, 
            prefix : Prefix) -> None:
        self.mappings[description] = prefix
        self.check_ambig.setdefault(prefix, set()).add(description)

    def check_for_ambiguous_prefixes(self) -> Optional[str]:
        """
        if any character prefixes are ambiguous, return 
        error message, otherwise return None
        """
        chars = sorted(set(self.check_ambig))
        for char in chars:
            descs = self.check_ambig[char]
            if len(descs) > 1:
                msg = 'multiple classes ('
                msg = msg + ', '.join(sorted(descs)) + ') '
                msg = msg + f'assigned to {char}'
                print(msg)
                return msg
            else:
                self.rmap[char] = list(descs)[0]
        return None

# prefix to description is now generic, so we can just use the
# module-level prefix2description
#    def prefix2desc(self, char : str) -> str:
#        return self.rmap[char]

#    def chars2descs(self, chars : Union[str, Sequence[str]]) -> List[str]:
#        return [self.rmap[char] for char in chars]]
#    def desc2chars(self, desc : str) -> str:
#        return self.mappings[desc]

# converting the other way is not standard because
# (a) there are two options each for prefixes for single/unique and
#     end/last
# (b) some output schema do not use all descriptions and therefore
#     their description-to-prefix mapping may be missing those
#     descriptions
        


# conversions

class Conversion(ABC):
    @abstractmethod
    def convert(self, orig : Sequence[Label]) -> Generator[Label, None, None]:
        pass


class ConversionImpl(object):
    """
    ConversionImpl implements the conversion as a finite state
    transducer
    """
    def __init__(self, 
            call_by_description : DescriptionMap,
            target : UnambigSchema,
            ) -> None:
        super().__init__()
        self.prev : ParsedLabel = ParsedLabel(prefix="O")
        self.target : UnambigSchema = target
        self.call_by_description : DescriptionDict = dict(call_by_description.items())
    def current2prefix(self, 
            current_label : ParsedLabel) -> Tuple[Prefix, str, str]:
        """
        given description, return corresponding prefix
        character, name of function called, and 
        optional error message (empty if no error)
        """
        desc : Desc = prefix2description[current_label.prefix]
        to_call = self.call_by_description.get(desc,
                unchanged)
        new_desc : Desc
        error_msg : str
        new_desc, error_msg = to_call(self.prev, current_label)
        return new_desc, to_call.__name__, error_msg
            
    def next_label(self, current : ParsedLabel,
            ) -> ParsedLabel:
        fn_name : str
        new_desc : Desc
        new_desc, fn_name = self.next_description(current)
        self.prev = current
        label = self.description2label(current,
                new_desc, fn_name)
        return label

    def next_description(self, current : ParsedLabel,
            ) -> Tuple[Desc, str]:
        """
        given current parsed label for original explicit
        mapping, handle any errors and return converted
        description in the target schema
        label in the target schema
        """
        desc : Desc = prefix2description[current.prefix]
        new_desc : Desc
        error_msg : str
        fn_name : str
        new_desc, fn_name, error_msg = (
                self.current2prefix(current)
                )
        if error_msg:
            sys.stderr.write(error_msg)
            sys.stderr.write('\n')
            sys.stdout.flush()
            sys.stderr.flush()
        return new_desc, fn_name

    def description2label(self, current : ParsedLabel,
            new_desc : Desc,
            fn_name : str,
            ) -> ParsedLabel:
        maybe_c : Optional[Prefix]
        maybe_c = self.target.mappings.get(new_desc)
        if maybe_c is None:
            msg = 'No prefix associated with description {desc} returned by {to_call_name} for label {label}'
            msg = msg.format(desc=new_desc,
                    to_call_name=fn_name,
                    label=current)
            raise ValueError(msg)

        updated : ParsedLabel = update_label(current,
                new_prefix=maybe_c)
        return updated





class Explicit2Unambig(Conversion):
    def __init__(self, explicit : UnambigSchema,
            unambig : UnambigSchema) -> None:
        if not explicit.is_explicit():
            raise ValueError('schema called explicit is not')
        desc2call : DescriptionDict = {}
        if unambig.bare_I:
            desc2call['begin'] = maybe_keep_B
        if unambig.last == 'I':
            desc2call['last'] = drop_end
        if unambig.single == 'B':
            desc2call['single'] = drop_single
        self.call_by_description : DescriptionDict = desc2call
        self.unambig : UnambigSchema = unambig
#        self.trans = {}
#        for desc in explicit.mappings:
#            maybe_c = self.unambig.mappings.get(desc)
#            if maybe_c is None:
#                pass
#            else:
#                self.trans[desc] = maybe_c

    def convert(self, orig_labels : Sequence[Label]) -> Generator[Label, None, None]:
        prev : ParsedLabel = ParsedLabel(prefix="O")
        label : str
        converter : ConversionImpl = ConversionImpl(
                self.call_by_description,
                self.unambig)
        for label in orig_labels:
            parsed : ParsedLabel = parse_label(label)
            new_parsed : ParsedLabel = converter.next_label(parsed)
            yield new_parsed.as_string()





class FromExplicit:
    """
    factory object returning conversions from "explicit"
    schema to different unambiguous schemas
    """

    def __init__(self, explicit : Optional[UnambigSchema] = None):
        explicit = explicit or UnambigSchema.std_explicit()
        if not explicit.is_explicit():
            raise ValueError('schema called explicit is not')
        self.explicit = explicit
    def to_unambig(self, unambig : UnambigSchema) -> Conversion:
        return Explicit2Unambig(self.explicit, unambig)


# vim: et ai si sts=4

