import pytest

from sap.aibus.dar.client.util.lists import split_list


class TestSplitList:
    """Tests split_list"""

    def test_slice_size_invalid(self):
        for invalid_slice_size in [-1000, -1, 0]:
            with pytest.raises(ValueError):
                list(split_list(["a", "b"], invalid_slice_size))

    def test_empty_list(self):
        res = list(split_list([], slice_size=1))
        assert res == [[]]

    def test_regular_case(self):
        res = list(split_list(["a", "b", "c", "d"], 2))
        assert res == [["a", "b"], ["c", "d"]]

    def test_list_uneven(self):
        res = list(split_list(["a", "b", "c", "d"], 3))
        assert res == [["a", "b", "c"], ["d"]]

    def test_slice_size_bigger_than_list(self):
        res = list(split_list(["a", "b", "c", "d"], 6))
        assert res == [["a", "b", "c", "d"]]
