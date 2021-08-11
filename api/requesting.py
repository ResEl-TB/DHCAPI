"""This module provides the requesting logic"""


from datetime import datetime
from .exceptions import LeaseNotFoundException, FieldUndefinedException, NoRuleMatchedException
from .loader import get_env
from .messages import Message
from .models import Lease, BaseResult
from .constants import REQUEST_LINE, REQUEST_LOG_FILE


class Result(BaseResult):
    """
    This class represents a request result.
    :param message: The result message
    :param env: The lease environment
    :param ip: The requested ip
    :param lease: The lease
    """
    def __init__(self, message, env, lease=None):
        super().__init__(message, env, lease)
        if lease is not None: # No real need to lock
            lease.update(self.lease_duration)

    def _no_lease(self):
        """NAK"""
        return self.nak()

    def _message_type(self):
        """Ack"""
        return self.ack()


def process(ldap, relay_ip, ip, mac):
    """
    Return the existing lease if it exists.
    :param ldap: The ldap to connect to
    :param relay_ip: The relay's IP address
    :param ip: The requested IP
    :param mac: The client's MAC address
    """
    try:
        env = get_env(relay_ip, mac)
    except NoRuleMatchedException:
        return Result(Message.UNADDRESSABLE, env)
    except FieldUndefinedException:
        return Result(Message.CONF_ERROR, env)
    lid = f'{env["lease_prefix"]}{env["mac"]}'
    try:
        return Result(Message.OK, env, Lease.from_ldap(ldap, lid, ip))
    except LeaseNotFoundException:
        return Result(Message.NO_LEASE, env)
    #except:
    #    return Result(Message.LDAP_ERROR, ip, None)


def log(mac, result):
    """
    Save the request result.
    :param mac: The machine MAC address
    :param result: The discovery result
    """
    with open(REQUEST_LOG_FILE, 'a') as logfile:
        logfile.write(REQUEST_LINE.format(int(datetime.now().timestamp() * 1000000),
                                          result.router_ip, mac, result.get_ip(),
                                          result.message.name))
