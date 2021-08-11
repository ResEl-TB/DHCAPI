"""This module provides utility functions"""

def first_available(l, start=0):
    """
    Find the first available value in a sorted list.
    :param l: The list
    :param start: The starting value
    """
    if len(l) == 0 or l[0] != start:
        return start
    mid_i = (len(l) + 1) // 2
    start = l[0]
    mid = l[mid_i-1]
    if mid - start > mid_i - 1:
        return first_available(l[:mid_i], start)
    return first_available(l[mid_i:], mid + 1)
