import pytest

from label_alignment import iob_state

@pytest.fixture
def starting_state():
    return iob_state.Outside()

def test_starting_state(starting_state):
    assert(isinstance(starting_state, iob_state.Outside))
    assert (starting_state.end_of_previous == 0)
    assert (starting_state.prev_token is None)
    assert (starting_state.pending_anno is None)
# vim: et ai si sts=4   

