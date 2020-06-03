"""
Utilities for lists.
"""
from typing import List, TypeVar, Iterator

Item = TypeVar("Item")


def split_list(input_list: List[Item], slice_size: int) -> Iterator[List[Item]]:
    """
    Yields sub-lists of the *input_list* of size *slice_size* or less.

    :param input_list: input_list to be divided
    :param slice_size: maximum number of sub list
    :return: a generator
    """
    if slice_size < 1:
        raise ValueError("slize_size must be > 0, not {}".format(slice_size))

    if not input_list:
        yield []

    for idx in range(0, len(input_list), slice_size):
        yield input_list[idx : idx + slice_size]
