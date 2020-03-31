#!/usr/bin/env python
__author__ = 'machiry'


def flatten_list(nested_list):
    """
        Given a list of lists, it flattens it to a single list.
    :param nested_list: list of lists
    :return: Single list containing flattened list.
    """
    return [item for sub_list in nested_list for item in sub_list]
