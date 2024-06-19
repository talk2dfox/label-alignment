import pytest

from typing import (
        Sequence, Mapping, 
        Callable,
        Union, Optional,
        Dict, Set, List, Tuple,
        Protocol,
        )

from collections import OrderedDict

from label_alignment.span_annotation import SpanAnnotation

from label_alignment.iob_state import (
    IOBState, Inside, Outside,
    UnexpectedLabel,
    SeeReturn,
    )


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
    interp = IOBState.interpret_label
    for lab, ans in interpreted_labels:
        assert(interp(lab) == ans)

@pytest.fixture
def starting_state() -> Outside:
    """
    Note: this fixture has function scope, so it will always
    represent the same state if used multiple times in a test.
    Currently, states are mutable and see() may modify
    itself and return itself instead of a new IOBState instance.

    To guarantee an independent starting state, use 
    starting_state_factory below
    """
    return Outside()

StartFactory = Callable[[], Outside]
@pytest.fixture
def starting_state_factory() -> StartFactory:
    def new_start():
        return Outside()
    return new_start


def starting_assertions(start : IOBState) -> None:
    assert(isinstance(start, Outside))
    assert (start.end_of_previous == 0)
    assert (start.prev_token is None)
    assert (start.pending_anno is None)

def inside_assertions(state : IOBState) -> None:
    assert(isinstance(state, Inside))
    assert (state.end_of_previous > 0)
    assert (state.prev_token is not None)
    assert (state.current_anno is not None)

def test_starting_state(starting_state : IOBState) -> None:
    starting_assertions(starting_state)
#    state, emitted = starting_state.see('

def test_starting_state_factory(
        starting_state_factory : StartFactory
        ) -> None:
    previous : List[IOBState] = []
    for i in range(3):
        start = starting_state_factory()
        for prev_state in previous:
            if start is prev_state:
                msg : str = f'new state {start} identical to previous state {prev_state}'
                raise ValueError(msg)
        starting_assertions(start)
        previous.append(start)

@pytest.fixture
def still_outside_not_first(
        starting_state  : IOBState
        ) -> SeeReturn:
    """
    return an Outside state with a previous token
    """
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    return state, no_emit

def test_sonf(still_outside_not_first : SeeReturn) -> None:
    state, no_emit = still_outside_not_first
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous > 0)


# currently, offset advance occurs in multiple places in each implementation
# of see, so really need to check all of them (or figure out an aspect-oriented
# way to unify them

def test_advance_from_start(starting_state : IOBState) -> None:
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous == len(token))
    assert(state.prev_token == token)

def test_advance_from_nonstart(still_outside_not_first : SeeReturn) -> None:
    token = 'most'
    sonf = still_outside_not_first[0]
    eop_orig = sonf.end_of_previous
    state, no_emit = sonf.see(token, 'O')
    print(sonf.end_of_previous)
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous - eop_orig == len(token) + 1)
    assert(state.prev_token == token)


TK = OrderedDict[str, # current state type,
        OrderedDict[
            str, # new state type
            str, # label types producing 
            # transition from current -> new
            ]
        ]

# test transitions
@pytest.fixture
def transition_keys() -> TK:
   """
   for each pair of start and end state, which labels cause
   that transition
   """
   tk : OrderedDict = OrderedDict()
   tk['O'] = OrderedDict()
   tk['O']['O'] = 'SUO'
   tk['O']['I'] = 'BI'
   tk['I'] = OrderedDict()
   tk['I']['O'] = 'ELOSU'
   tk['I']['I'] = 'BI'
   return tk

EK = OrderedDict[str, # current state type,
        str, # label types producing errors
        ]

@pytest.fixture
def transition_errors() -> EK:
   errs = OrderedDict()
   errs['O'] = 'LE'

   return errs

def maybe_add_class(label : str, label_cls : Optional[str] = 'PER') -> str:
    """
    given bare label (IOBELUS), add class if required

    use fake label 'J' or 'F' to force adding label_cls to 'I'
    or 'E' respectively
    """
    if label in 'BUS':
        label_cls = label_cls or 'PER'
        return f'{label}-{label_cls}'
    elif label == 'J':
        return f'I-{label_cls}'
    elif label == 'F':
        return f'E-{label_cls}'
    return label

def state_type_assertion(state : IOBState, 
        state_type : str) -> bool:
    if state_type.startswith('I'):
        return isinstance(state, Inside)
    elif state_type.startswith('O'):
        return isinstance(state, Outside)
    return False

class InsideFactory(Protocol):
    @classmethod
    def __call__(cls, label_cls : Optional[str] = "COMPANY") -> IOBState:
        pass

@pytest.fixture
def inside_state_factory(starting_state_factory : StartFactory) -> InsideFactory:
    def inside_class(label_cls : Optional[str] = "COMPANY") -> IOBState:
        start = starting_state_factory()
        inside, emitted = start.see('Intel', f'B-{label_cls}')
        assert(emitted is None)
        assert(state_type_assertion(inside, 'I'))
        return inside
    return inside_class
    
def test_transitions(transition_keys : TK, 
        starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    tk = transition_keys
    dummy = 'Fish'
    for expected, labels in tk['O'].items():
        for label in labels:
            start = starting_state_factory()
            full = maybe_add_class(label)
            end, emitted = start.see(dummy, full)
            assert(end.end_of_previous == len(dummy))
            assert(emitted is None)
            assert(state_type_assertion(end, expected))
    for expected, labels in tk['I'].items():
        for label in labels:
            inside = inside_state_factory('COMPANY')
            full = maybe_add_class(label)
            eop = inside.end_of_previous
            end, emitted = inside.see('Fish', full)
            assert(end.end_of_previous - eop == len(dummy) + 1)
            assert(state_type_assertion(end, expected))


def test_errors(transition_errors : EK, 
        starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    for labels in transition_errors.get('O', ''):
        for label in labels:
            start = starting_state_factory()
            full = maybe_add_class(label)
            with pytest.raises(UnexpectedLabel):
                start.see('Fish', full)
    for labels in transition_errors.get('I', ''):
        for label in labels:
            inside = inside_state_factory()
            full = maybe_add_class(label)
            with pytest.raises(UnexpectedLabel):
                start.see('foo', full)

#---------------------------
# test emitted annotation
#---------------------------

def test_outside_pending(starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    """
    if we are inside, and see a token labeled U/S, then
    we end and return the existing annotation, then
    we can't also return the new single-token span,
    so we transition to outside, but keep the single-token
    span as a pending annotation

    similarly, if we are outside and already have a pending
    annotation, and then we see another U/S token, then
    we emit the pending token and keep the new span pending

    if we are outside (with or without pending) and
    see any label other than U/S, we end with no pending 
    annotation
    """
    inside : IOBState = inside_state_factory('COMPANY')
    current : Optional[SpanAnnotation] = inside.current_annotation()
    assert(current is not None)
    inside_assertions(inside)
    wpend : IOBState
    new_start : IOBState
    anno : Optional[SpanAnnotation]
    resolved : Optional[SpanAnnotation]

    next_label_type : str
    for next_label_type in 'IJOBUS':
        print(f'next label is of type {next_label_type}')
        expect_pending : bool = False
        if next_label_type in 'US':
            expect_pending = True
        inside = inside_state_factory('COMPANY')
        state_type_assertion(inside, "I")
        current = inside.current_annotation()
        assert(current is not None)
        assert(current.label == 'COMPANY')
        next_label : str = maybe_add_class(next_label_type,
                'PERS')
        print(f'next label is {next_label}')
        wpend, anno = inside.see('David', next_label)
        if next_label_type != 'I':
            assert(anno is current)
        else:
            state_type_assertion(wpend, 'I')
            assert(wpend.current_annotation() is current)
        if next_label_type in 'USO':
            state_type_assertion(wpend, "O")
            pend : Optional[SpanAnnotation] = wpend.pending_annotation()
            if expect_pending:
                assert(pend is not None)
                assert(pend.label == 'PERS')
                assert(pend.end == wpend.end_of_previous)
                assert(pend.is_closed())
                assert(len(pend) == len('David'))
                resolved = wpend.end_of_text()
                assert(pend is resolved)
            else:
                assert(pend is None)
                resolved = wpend.end_of_text()
                assert(resolved is None)



#    return [
#            ( ("O", "B-PER"), "I" ),

#@pytest.fixture
#def test_state_transitions(starting_state):

# test emitted chunks







# vim: et ai si sts=4   

