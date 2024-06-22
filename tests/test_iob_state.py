"""
Testing state machine from iob_state

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

from label_alignment.annotation.span_annotation import SpanAnnotation

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

def still_outside_not_first(
        starting_state  : IOBState
        ) -> SeeReturn:
    """
    return an Outside state with a previous token
    """
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    return state, no_emit

def test_sonf(starting_state : Outside) -> None:
    state : IOBState
    no_emit : Optional[SpanAnnotation]
    state, no_emit = still_outside_not_first(starting_state)
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous > 0)
    state, no_emit = still_outside_not_first(state)
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous > 0)


# currently, offset advance occurs in multiple places in each implementation
# of see, so really need to check all of them (or figure out an aspect-oriented
# way to unify them)
#
# here, just test from outside, seeing O
# 
# rest are tested in test_transitions

def test_advance_from_start(starting_state : IOBState) -> None:
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    assert(no_emit is None)
    assert(isinstance(state, Outside))
    assert(state.end_of_previous == len(token))
    assert(state.prev_token == token)

def test_advance_from_nonstart(starting_state : Outside) -> None:
    token : str = 'most'
    sonf : IOBState = still_outside_not_first(starting_state)[0]
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

def state_type_check(state : IOBState, 
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
        assert(state_type_check(inside, 'I'))
        return inside
    return inside_class
    
def test_state_type_check(starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    state : IOBState
    no_emit : Optional[SpanAnnotation]
    state = starting_state_factory()
    assert(state_type_check(state, "O"))
    assert(not state_type_check(state, "I"))
    state, no_emit = still_outside_not_first(state)
    assert(no_emit is None)
    assert(state_type_check(state, "O"))
    assert(not state_type_check(state, "I"))
    state = inside_state_factory()
    assert(not state_type_check(state, "O"))
    assert(state_type_check(state, "I"))


def test_transitions(transition_keys : TK, 
        starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    """
    test all state transitions
    (and also position advancement)
    """
    tk = transition_keys
    dummy = 'Fish'
    for expected, labels in tk['O'].items():
        for label in labels:
            start = starting_state_factory()
            full = maybe_add_class(label)
            end, emitted = start.see(dummy, full)
            # test advancement
            assert(end.end_of_previous == len(dummy))
            assert(emitted is None)
            assert(state_type_check(end, expected))
    for expected, labels in tk['I'].items():
        for label in labels:
            inside = inside_state_factory('COMPANY')
            full = maybe_add_class(label)
            eop = inside.end_of_previous
            end, emitted = inside.see('Fish', full)
            # test advancement
            assert(end.end_of_previous - eop == len(dummy) + 1)
            assert(state_type_check(end, expected))


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

def is_pending(pend : Optional[SpanAnnotation], 
        label : Optional[str] = None, 
        end_of_previous : Optional[int] = None,
        length : Optional[int] = None
        ) -> None:
    assert(pend is not None)
    if label is not None:
        assert(pend.label == label)
    if end_of_previous is not None:
        assert(pend.end == end_of_previous)
    assert(pend.is_closed())
    if length is not None:
        assert(len(pend) == length)

def test_outside_pending(
        starting_state_factory : StartFactory,
        inside_state_factory : InsideFactory) -> None:
    """
    case 1: (positive/negative)
        (a) (positive) if we are inside, and see a token labeled U/S, then
        we end and return the existing annotation, then
        we can't also return the new single-token span,
        so we transition to outside, but keep the single-token
        span as a pending annotation.  

        For any other label, next step is one of the following
        (b) (negative) see I-consistent, return nothing and 
        stay inside,
        (c) (negative) see B or I-inconsistent, return current and transition 
        to new Inside state
        (d) (negative) see E/L or O, return current and transition to outside

    case 2: (positive)
        similarly, if we are outside and already have a pending
        annotation, and then we see another U/S token, then
        we emit the pending token and keep the new span pending

    case 3: (negative)
        if we are outside (with or without pending) and
        see any label other than U/S, we end with no pending 
        annotation
    """
    inside : IOBState = inside_state_factory('COMPANY')
    current : Optional[SpanAnnotation] = inside.current_annotation()
    assert(current is not None)
    assert(current.is_open())
    inside_assertions(inside)
    wpend : IOBState
    new_start : IOBState
    anno : Optional[SpanAnnotation]
    resolved : Optional[SpanAnnotation]

    next_label_type : str
    # starting with an inside state (current, unfinished annotation)
    # we test case 1
    # for next label, test all cases 
    for next_label_type in 'IJOBUSEL':
        # I represents I consistent, whereas J represents I inconsistent
        print(f'next label is of type {next_label_type}')
        # start in (fresh) inside state
        inside = inside_state_factory('COMPANY')
        # veriy that
        state_type_check(inside, "I")
        current = inside.current_annotation()
        assert(current is not None)
        assert(current.is_open())
        assert(current.label == 'COMPANY')

        # what do we expect after inside sees the next labeled token
        expect_pending : bool = False
        # expend pending after next only if next token 
        # (1) ends current anno AND
        # (2) starts a new one
        # only labels which do that are U/S
        if next_label_type in 'US':
            # U/S ends current  - selecting case 1(a)
            # case 1(a)
            expect_pending = True

        next_label : str = maybe_add_class(next_label_type,
                'PERS')
        print(f'next label is {next_label}')
        wpend, anno = inside.see('David', next_label)
        if next_label_type == 'I':
            # testing 1(b)
            assert(state_type_check(wpend, 'I'))
            wp_current = wpend.current_annotation()
            assert(wp_current is not None)
            assert(wp_current is current)
            assert(wp_current.is_open())
        else:
            # everything else ends the current annotation, returning it
            # testing emission in cases 1(c) and 1(d)
            assert(anno is current)
        if next_label_type in 'JB':
            # testing 1(c) transition
            assert(state_type_check(wpend, "I")) 
        elif next_label_type in 'USOEL':
            assert(state_type_check(wpend, "O"))
            pend : Optional[SpanAnnotation] = wpend.pending_annotation()
            if expect_pending: # testing case 1(a)
                is_pending(pend, label='PERS', 
                        end_of_previous=wpend.end_of_previous,
                        length=len('David')
                        )
                # testing case 2
                wpend2 : IOBState
                emit2 : Optional[SpanAnnotation]
                wpend2, emit2 = wpend.see('foo', 'U-MADE-UP-TERM')
                assert(emit2 is pend)
                pend2 : Optional[SpanAnnotation] = wpend2.pending_annotation()
                is_pending(pend2, label='MADE-UP-TERM', 
                        end_of_previous=wpend2.end_of_previous,
                        length=len('foo')
                        )

                if next_label_type == 'U':
                    out_pending = pend
                resolved = wpend2.end_of_text()
                assert(pend2 is resolved)
            else: # testing case 1(d)
                # tests
                assert(pend is None)
                resolved = wpend.end_of_text()
                assert(resolved is None)

        wnopend : IOBState
        outside : Outside = starting_state_factory()
        wnopend, anno = outside.see('then', 'O')
        assert(anno is None)
        assert(state_type_check(wnopend, 'O'))
        assert(wnopend.pending_annotation() is None)
        inside = inside_state_factory('COMPANY')
        outside_pending : IOBState
        outside_pending, anno = inside.see('David', 'U-PERS')
        assert(anno is not None)
        assert(anno.label == 'COMPANY')
        pend = outside_pending.pending_annotation()
        is_pending(pend, label='PERS',
                length=len('David'))
        wnopend, anno = outside_pending.see('then', 'O')
        assert(anno is not None)
        assert(anno.label == 'PERS')
        assert(state_type_check(wnopend, 'O'))
        assert(wnopend.pending_annotation() is None)
        assert(wnopend.end_of_text() is None)









#    return [
#            ( ("O", "B-PER"), "I" ),

#@pytest.fixture
#def test_state_transitions(starting_state):

# test emitted chunks







# vim: et ai si sts=4   

