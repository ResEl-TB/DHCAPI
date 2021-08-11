"""This module defines the different outcomes"""

from enum import Enum
from .constants import MESSAGES


class Message(Enum):
    """This enum defines all the possible outcomes of an authorization"""
    OK = 0
    NO_FREE_IP = 1
    NO_LEASE = 2
    UNADDRESSABLE = 3
    CONF_ERROR = 4
    LDAP_ERROR = 5

    def message(self):
        """
        Return a text message for the current value.
        :return: The result description
        """
        #pylint: disable=E1126
        return MESSAGES[self.value]
