"""This module provides tools to manipulate round-robin IP pools"""


from datetime import datetime
from .exceptions import NoMoreIPException


class RoundRobinIP:
    """
    This class implements a round-robin IP pool
    """
    def __init__(self, master, slaves):
        self.is_master = self.attempts = self.address = self.index = None
        self.default_address = master
        self.slaves = slaves
        self.last_crash = datetime.now()
        self.reset(init=True)
        self.next_index = 0

    def next(self):
        """
        Get the next available IP.
        :returns: The next IP
        """
        n_slaves = len(self.slaves)
        if self.is_master:
            self.last_crash = datetime.now()
        if self.attempts >= n_slaves:
            self.reset()
            raise NoMoreIPException()
        if self.attempts == 0 and not self.is_master:
            self.is_master = True
            self.attempts -= 1
        else:
            self.index = self.next_index
            self.next_index = (self.index + 1) % n_slaves
            self.is_master = False
        self.address = self.slaves[self.index] if not self.is_master else self.default_address
        self.attempts += 1
        return self.address

    def found(self):
        """Reset the internal counter if an IP is reachable"""
        self.attempts = 0

    def reset(self, init=False):
        """
        Reset the internal state.
        :param init: Whether the reinitialization should be forced
        """
        self.index = 0
        if init or (datetime.now() - self.last_crash).seconds > 300:
            self.is_master = True
            self.address = self.default_address
        self.attempts = 0

    def get(self):
        """
        Get the current address
        :returns: The current address
        """
        return self.address

    def get_default(self):
        """
        Get the default/master address
        :returns: The default address
        """
        return self.default_address
