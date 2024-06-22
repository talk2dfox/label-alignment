import pytest

from pathlib import Path

@pytest.fixture
def data_path():
    return Path('tests') / 'data'

@pytest.fixture
def anno_path(data_path):
    return data_path / 'annotated_texts'


# vim: et ai si sts=4   
