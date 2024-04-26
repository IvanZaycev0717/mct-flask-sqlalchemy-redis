import pytest

@pytest.fixture
def my_fixture():
    data = "example data"
    return data

def test_fixture_example(my_fixture):
    assert my_fixture == "example data"

@pytest.fixture
def another_fixture():
    return [1, 2, 3]

def test_another_fixture_length(another_fixture):
    assert len(another_fixture) == 3

def test_another_fixture_contains_element(another_fixture):
    assert 2 in another_fixture