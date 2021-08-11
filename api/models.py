"""This module defines the Lease model used by the API"""

import os
import struct
from abc import abstractmethod
from datetime import datetime, timedelta
from .constants import LEASES_DN, SERVER_IP
from .exceptions import NoFreeIPException
from .ip import IP
from .util import first_available


class Lease:
    """
    This class represents a DHCP lease.
    :param ldap: The ldap to connect to
    :param lease_id: The lease ID
    :param mac_address: The MAC address
    :param ip_address: The IP address
    :param lease_expiry: The lease expiry
    """
    def __init__(self, ldap, lease_id, mac_address, ip_address, lease_expiry):
        self.ldap = ldap
        self.lease_id = lease_id
        self.mac_address = mac_address
        self.ip_address = ip_address
        self.lease_expiry = lease_expiry

    @classmethod
    def from_ldap(cls, ldap, lease_id, ip=None):
        """
        Fetch a DHCP lease from the LDAP.
        :param ldap: The ldap to connect to
        :param lease_id: The beginning of the lease ID
        :param ip: The optional lease IP address
        """
        lease_data = ldap.get_lease(lease_id, ip)
        return cls(ldap, **lease_data)

    @classmethod
    def create(cls, ldap, first, last, mac, lease_prefix):
        """
        Create a DHCP lease.
        :param ldap: The ldap to connect to
        :param first: The first addressable IP
        :param last: The last addressable IP
        :param mac: The MAC address
        :param lease_prefix: The lease prefix
        """
        int_ips = sorted(set(int(IP(ip)) for ip in ldap.get_used_ips(f'{lease_prefix}')))
        ip = IP(first_available(int_ips, int(first)))
        if ip > last:
            raise NoFreeIPException

        seed = struct.unpack('I', os.urandom(4))[0]

        # We leave 5 minutes for the client to accept the lease
        lid = f'{lease_prefix}{mac}'
        ldap.add_lease(f'{lid}-{seed}', mac, str(ip),
                       datetime.now().astimezone() + timedelta(seconds=300))
        return cls.from_ldap(ldap, lid)

    def update(self, duration):
        """
        Update the lease expiry
        :param duration: The lease duration
        """
        if self.ldap.is_master():
            self.ldap.update(f'leaseID={self.lease_id},{LEASES_DN}', 'leaseExpiry',
                             datetime.now().astimezone() + timedelta(seconds=duration+300))


class BaseResult:
    """
    This class represents a DHCP result.
    :param message: The result message
    :param env: The lease environment
    :param lease: The lease
    """
    def __init__(self, message, env, lease=None):
        self.message = message
        self.router_ip = env['router_ip']
        self.lease = lease
        self.mask = env['mask']
        self.lease_duration = env['lease_duration']
        self.dns = env.get('dns', [])
        self.attributes = env.get('attributes', {})

    @abstractmethod
    def _no_lease(self):
        """Return something when there is no lease"""

    @abstractmethod
    def _message_type(self):
        """Return the result message type"""

    def get_dict(self):
        """
        Get the dictionary to return to FreeRADIUS as a JSON object.
        :returns: The dictionary summarizing the result
        """
        if self.lease is None:
            return self._no_lease()

        return {**{'DHCP-Domain-Name-Server': self.dns, 'DHCP-DHCP-Server-Identifier': SERVER_IP,
                   'DHCP-Your-IP-Address': self.lease.ip_address,
                   'DHCP-Subnet-Mask': str(self.mask), 'DHCP-Router-Address': str(self.router_ip),
                   'DHCP-IP-Address-Lease-Time': self.lease_duration},
                **self.attributes, **self._message_type()}

    @staticmethod
    def do_not_respond():
        """Return a DHCP-Do-Not-Respond"""
        return {'DHCP-Message-Type': 'DHCP-Do-Not-Respond'}

    @staticmethod
    def nak():
        """Return a DHCP-NAK"""
        return {'DHCP-Message-Type': 'DHCP-NAK'}

    @staticmethod
    def ack():
        """Return a DHCP-Ack"""
        return {'DHCP-Message-Type': 'DHCP-Ack'}

    @staticmethod
    def offer():
        """Return a DHCP-Offer"""
        return {'DHCP-Message-Type': 'DHCP-Offer'}

    def get_ip(self):
        """
        Get the lease IP
        :returns: The lease IP or 'UNKNOWN'
        """
        if self.lease is None:
            return 'UNKNOWN'
        return self.lease.ip_address
