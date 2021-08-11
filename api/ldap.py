"""This module defines the tools used by the API to communicate with the LDAP"""

import logging
from datetime import datetime
from .constants import LEASES_DN
from .exceptions import LeaseNotFoundException
from .roundrobin import RoundRobinLdap


class Ldap(RoundRobinLdap):
    """This class extends the Round-Robin LDAP by adding methods useful for the API"""

    def get_lease(self, lid, ip=None):
        """
        Get a lease from the LDAP server.
        :param lid: The lease ID
        :returns: A dictionary representing the lease
        """
        if not self.search(f'(&(objectclass=reselLease)(leaseID={lid}-*))', LEASES_DN,
                           ['leaseID', 'macAddress', 'ipHostNumber', 'leaseExpiry']):
            raise LeaseNotFoundException()

        results = self.get_results()

        if ip is not None:
            results = list(filter(lambda x: x.ipHostNumber.value == ip, results))
            if len(results) == 0:
                raise LeaseNotFoundException()

        # We only keep the longest lease
        result = max(results, key=lambda x: x.leaseExpiry.value)
        return {'lease_id': result.leaseID.value,
                'mac_address': result.macAddress.value,
                'ip_address': result.ipHostNumber.value,
                'lease_expiry': result.leaseExpiry.value
               }

    def get_used_ips(self, partial_lid):
        """
        Get the used IPs pertaining to a same lease prefix.
        :param partial_lid: The lease ID prefix
        :returns: A list of used IP addresses
        """
        self.search(f'(&(objectclass=reselLease)(leaseID={partial_lid}*))', LEASES_DN,
                    ['ipHostNumber'])
        return [result.ipHostNumber.value for result in self.get_results()]

    def add_lease(self, lid, mac_address, ip_address, lease_expiry):
        """
        Add a lease to the LDAP.
        :param lid: The lease ID
        :param mac_address: The machine MAC address
        :param ip_address: The machine IP address
        :param lease_expiry: The lease expiry
        """
        logging.info(f'[LDAP][add_lease] Adding lease {lid} for machine {mac_address}/{ip_address}')
        return self.do('add', f'leaseID={lid},{LEASES_DN}', 'reselLease',
                       {'macAddress': mac_address, 'ipHostNumber': ip_address,
                        'leaseExpiry': lease_expiry})

    def remove_expired_leases(self):
        """Remove expired leases"""
        logging.info('[LDAP][remove_expired_leases] Removing expired leases')
        expiry = datetime.now().astimezone().strftime('%Y%m%d%H%M%S%z')
        self.search(f'(&(objectclass=reselLease)(leaseExpiry<={expiry}))', LEASES_DN)
        results = self.get_results()
        for result in results:
            self.delete(result.entry_dn)
        logging.info(f'[LDAP][remove_expired_leases] Removed {len(results)} leases')
