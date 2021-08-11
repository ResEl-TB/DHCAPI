"""This module provides all the exceptions needed by the API"""


from .roundrobin import NotFoundException, NoMoreIPException, ReadOnlyException


class LeaseNotFoundException(NotFoundException):
    """This class represents the fact that a lease hasn't been found in the LDAP"""

class NoFreeIPException(Exception):
    """This class represents the fact that no free IP is available"""

class UnaddressablePoolException(Exception):
    """This class represents the fact that the given IP is not in any addressable pool"""

class FieldUndefinedException(Exception):
    """This class represents the fact that a required field has not been defined"""

class NoRuleMatchedException(Exception):
    """This class represents the fact that no rule has been matched"""
