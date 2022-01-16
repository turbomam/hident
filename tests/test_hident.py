from hident import __version__
import hident.hident as h


def test_version():
    assert __version__ == '0.1.0'


def test_s2sl():
    expected_list = ["sand", "tree", "water"]
    set_of_terms = {"tree", "water", "sand"}
    returned_list = h.set_to_sorted_list(set_of_terms)
    assert returned_list == expected_list
