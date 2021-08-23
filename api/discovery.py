"""This module provides the discovery logic"""


import logging
from datetime import datetime
from multiprocessing import Lock
from .exceptions import (LeaseNotFoundException, NoFreeIPException, FieldUndefinedException,
                         NoRuleMatchedException)
from .loader import get_env
from .messages import Message
from .models import Lease, BaseResult
from .constants import DISCOVERY_LINE, DISCOVERY_LOG_FILE


lock = Lock()


class Result(BaseResult):
    """
    This class represents a discovery result.
    :param message: The result message
    :param env: The lease environment
    :param lease: The lease
    """

    def _no_lease(self):
        """Do not respond"""
        return self.do_not_respond()

    def _message_type(self):
        """Offer"""
        return self.offer()


def process(ldap, relay_ip, mac):
    """
    Return an existing lease or create one.
    :param ldap: The ldap to connect to
    :param relay_ip: The relay's IP
    :param mac: The client's MAC address
    """
    logging.info('[DISCOVERY][process] DHCPDISCOVER from %s on %s', mac, relay_ip)
    try:
        env = get_env(relay_ip, mac)
    except NoRuleMatchedException as e:
        return Result(Message.UNADDRESSABLE, e.args[0])
    except FieldUndefinedException as e:
        return Result(Message.CONF_ERROR, e.args[0])
    lid = f'{env["lease_prefix"]}{env["mac"]}'
    try: # Avoid the costly critical section
        return Result(Message.OK, env, Lease.from_ldap(ldap, lid))
    except LeaseNotFoundException:
        with lock:
            try: # Just make sure nothing new happened
                return Result(Message.OK, env, Lease.from_ldap(ldap, lid))
            except LeaseNotFoundException:
                try:
                    c_env = {k: v for k, v in env.items() if k in ['first', 'last', 'mac',
                                                                   'lease_prefix']}
                    return Result(Message.OK, env, Lease.create(ldap, **c_env))
                except NoFreeIPException:
                    return Result(Message.NO_FREE_IP, env)
                except:
                    return Result(Message.LDAP_ERROR, env)


def log(mac, result):
    """
    Save the discovery result.
    :param mac: The machine MAC address
    :param result: The discovery result
    """
    with open(DISCOVERY_LOG_FILE, 'a') as logfile:
        logfile.write(DISCOVERY_LINE.format(int(datetime.now().timestamp() * 1000000),
                                            result.router_ip, mac, result.get_ip(),
                                            result.message.name, result.env.get('vid', 'UNKNOWN'),
                                            result.env.get('zid', 'UNKNOWN')))
