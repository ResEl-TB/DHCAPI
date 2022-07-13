"""This modules provides tools to manipulate IP addresses and pools"""

from datetime import datetime, timedelta
from random import shuffle
from .exceptions import NoMoreIPException


class PoolIP:
    """
    This class implements an IP member of a pool
    """
    def __init__(self, address, should_write):
        self.address = address
        self.should_write = should_write
        self.last_crash = datetime.now()
        self.last_timeout = datetime.now() - timedelta(minutes=10)
        self.up = True

    def reset(self):
        """Reset the state of the IP"""
        self.last_crash = datetime.now()
        self.last_timeout = datetime.now() - timedelta(minutes=10)
        self.up = True

    @property
    def is_available(self):
        """
        Check if the IP is available.
        :returns: Whether the IP is available or not
        """
        if self.up or (datetime.now() - self.last_crash).seconds > 300:
            return True
        return False

    @property
    def can_write(self):
        """
        Check if the IP corresponds to a writable node.
        :returns: Whether the node is writable or not
        """
        return self.should_write and (datetime.now() - self.last_timeout).seconds > 300

    def timed_out(self):
        """Mark the node as timed out"""
        self.last_timeout = datetime.now()


class RoundRobinIP:
    """
    This class implements a round-robin IP pool
    """
    def __init__(self, rw_servers, ro_servers):
        self.servers = ([PoolIP(address, True) for address in rw_servers] +
                        [PoolIP(address, False) for address in ro_servers])
        self.ip = None

    def get_rw_pool(self):
        """
        Get the R/W pool.
        :returns: The R/W pool
        """
        return [srv for srv in self.servers if srv.can_write and srv.is_available]

    def next(self):
        """
        Get the next available IP.
        :returns: The next IP
        """
        self.just_crashed()
        rw_pool = self.get_rw_pool()
        shuffle(rw_pool)
        ro_pool = [srv for srv in self.servers if not srv.can_write and srv.is_available]
        shuffle(ro_pool)
        pool = rw_pool + ro_pool
        try:
            self.ip = pool[0]
            return self.ip.address
        except IndexError as e:
            self.reset()
            raise NoMoreIPException() from e

    def just_crashed(self):
        """Mark the node as just crashed"""
        if self.ip is not None:
            self.ip.last_crash = datetime.now()
            self.ip.up = False

    def reset(self):
        """Reset the internal state"""
        self.ip = None
        for ip in self.servers:
            ip.reset()

    @property
    def address(self):
        """
        Get the node's IP address.
        :returns: The IP address
        """
        return self.ip.address

    @property
    def can_write(self):
        """
        Check if the node has Write capabilities.
        :returns: Whether the node can write
        """
        return self.ip.can_write

    def timed_out(self):
        """Mark the node as timed out"""
        self.ip.timed_out()

    @property
    def has_writable(self):
        """
        Check if the pool has any writable IP.
        :returns: Whether the pool has writable IPs
        """
        return len(self.get_rw_pool()) > 0
