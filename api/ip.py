"""This module provides tools to manipulate IP addresses and pools"""


from functools import reduce


class Network:
    """
    This class represents an IP network.
    :param ip: The network string (IP/Mask, IP/Mask/Contiguous mask)
    If the given mask is contiguous (its MSB=1 and there is no 0 between the MSB and the least
    significant 1) and no other contiguous mask is provided, the result will be the one expected.
    The real benefit of contiguous masks is if an IP is matched against a group of networks by
    ignoring some bits; when computing the base IP of the network, the ignored bits may be needed.
    That is what this algorithm assumes.
    """
    def __init__(self, network):
        network_parts = network.split('/')
        ip, mask = network_parts[:2]
        self.ip = IP(ip)
        try:
            int_mask = int(mask)
            self.mask = IP((2**int_mask-1) * 2**(32-int_mask))
        except ValueError:
            self.mask = IP(mask)
        if len(network_parts) == 2:
            self.contiguous_mask = IP('255.255.255.255') - IP((self.mask.ip&-self.mask.ip)-1)
        elif len(network_parts) == 3:
            contiguous_mask = network_parts[2]
            try:
                int_contiguous_mask = int(contiguous_mask)
                self.contiguous_mask = IP((2**int_contiguous_mask-1) * 2**(32-int_contiguous_mask))
            except ValueError:
                self.contiguous_mask = IP(contiguous_mask)

    def __str__(self):
        """
        Return the string representation of the network
        :returns: The string representation
        """
        return f'{self.ip}/{self.mask}'

    def __repr__(self):
        """
        Return the string representation of the IP address object
        :returns: The string representation
        """
        return f"Network('{str(self)}')"

    def __contains__(self, ip):
        """
        Check if an IP is in a network
        :param ip: The ip
        :returns: Whether the IP is in the network
        """
        return not (ip^self.ip) & self.mask

    def base_ip(self, ip=None):
        """
        Return the base network IP of a given IP using the previously computed contiguous mask. If
        no IP is given, use the original IP.
        :param ip: The IP to consider
        """
        if ip is None:
            ip = self.ip
        return ip & self.contiguous_mask

class IP:
    """
    This class represents an IP address
    :param ip: The IP string or integer
    """
    def __init__(self, ip):
        self.ip = self._int(ip)

    @classmethod
    def _int(cls, obj):
        """
        Convert an IP-like object into its integer representation
        :param obj: The object
        :returns: Its integer representation
        """
        if isinstance(obj, str):
            return reduce(lambda x, y: x*2**8+int(y), obj.split('.'), 0)
        if isinstance(obj, int):
            return obj
        if isinstance(obj, cls):
            return obj.ip
        raise TypeError(f'Invalid argument: {repr(obj)}')

    def _op(self, op, other):
        """
        Apply a binary operator on the integer representations of two IP addresses
        :param op: The operator to apply
        :param other: The other IP-like object
        """
        return IP(op(self._int(self), self._int(other)))

    def _rop(self, op, other):
        """
        Apply a binary operator on the integer representations of two IP addresses after reversing
        the operands
        :param op: The operator to apply
        :param other: The other IP-like object
        """
        return IP(op(self._int(other), self._int(self)))

    def __int__(self):
        """
        Return the integer representation of the IP address
        :returns: The integer representation
        """
        return self.ip

    def __str__(self):
        """
        Return the string representation of the IP address
        :returns: The string representation
        """
        def int2ip_rec(i, numbers):
            if i or numbers > 0:
                return int2ip_rec(i//256, numbers-1) + [str(i%256)]
            return []
        return '.'.join(int2ip_rec(self.ip, 4))

    def __repr__(self):
        """
        Return the string representation of the IP address object
        :returns: The string representation
        """
        return f"IP('{str(self)}')"

    def __xor__(self, other):
        """^"""
        return self._op(int.__xor__, other)

    def __rxor__(self, other):
        """^"""
        return self._rop(int.__xor__, other)

    def __and__(self, other):
        """&"""
        return self._op(int.__and__, other)

    def __rand__(self, other):
        """&"""
        return self._rop(int.__and__, other)

    def __add__(self, other):
        """+"""
        return self._op(int.__add__, other)

    def __radd__(self, other):
        """+"""
        return self._rop(int.__add__, other)

    def __sub__(self, other):
        """-"""
        return self._op(int.__sub__, other)

    def __rsub__(self, other):
        """-"""
        return self._rop(int.__sub__, other)

    def __lt__(self, other):
        """<"""
        return self._op(int.__lt__, other)

    def __le__(self, other):
        """<="""
        return self._op(int.__le__, other)

    def __gt__(self, other):
        """>"""
        return self._op(int.__gt__, other)

    def __ge__(self, other):
        """>="""
        return self._op(int.__ge__, other)

    def __eq__(self, other):
        """=="""
        return self._op(int.__eq__, other)

    def __ne__(self, other):
        """!="""
        return self._op(int.__ne__, other)

    def __bool__(self):
        """
        Return if the IP is different from 0.0.0.0
        """
        return self.ip != 0

    def extract(self, mask):
        """
        Apply a mask and shift the result to the least significant bit set to 1 of the mask
        :param mask: The mask
        :returns: The integer result
        """
        imask = self._int(mask)
        return int(self&mask) // (imask&-imask)
