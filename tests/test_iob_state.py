import pytest

from collections import OrderedDict

from label_alignment import iob_state


@pytest.fixture
def interpreted_labels():
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

def test_interpret_labels(interpreted_labels):
    interp = iob_state.IOBState.interpret_label
    for lab, ans in interpreted_labels:
        assert(interp(lab) == ans)

@pytest.fixture
def starting_state():
    return iob_state.Outside()

def test_starting_state(starting_state):
    assert(isinstance(starting_state, iob_state.Outside))
    assert (starting_state.end_of_previous == 0)
    assert (starting_state.prev_token is None)
    assert (starting_state.pending_anno is None)
#    state, emitted = starting_state.see('

@pytest.fixture
def still_outside_not_first(starting_state):
    """
    return an Outside state with a previous token
    """
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    return state, no_emit

def test_sonf(still_outside_not_first):
    state, no_emit = still_outside_not_first
    assert(no_emit is None)
    assert(isinstance(state, iob_state.Outside))
    assert(state.end_of_previous > 0)

def test_advance_from_start(starting_state):
    token = 'the'
    state, no_emit = starting_state.see(token, 'O')
    assert(no_emit is None)
    assert(isinstance(state, iob_state.Outside))
    assert(state.end_of_previous == len(token))
    assert(state.prev_token == token)

def test_advance_from_nonstart(still_outside_not_first):
    token = 'most'
    sonf = still_outside_not_first[0]
    eop_orig = sonf.end_of_previous
    state, no_emit = sonf.see(token, 'O')
    print(sonf.end_of_previous)
    assert(no_emit is None)
    assert(isinstance(state, iob_state.Outside))
    assert(state.end_of_previous - eop_orig == len(token) + 1)
    assert(state.prev_token == token)


#@pytest.fixture
#def transition_keys():

#    """
#    return [
#            ( ("O", "B-PER"), "I" ),

#@pytest.fixture
#def test_state_transitions(starting_state):








# vim: et ai si sts=4   

