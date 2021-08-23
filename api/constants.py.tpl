"""This module defines all the constants used by the API"""


CONFIG_FILE = '/srv/dhcapi/dhcp.conf'

MASTER_LDAP = '10.3.3.1' # Master IP
SLAVE_LDAPS = ['10.3.3.101'] # Slaves IP list
LDAP_USER = 'cn=admin,dc=maisel,dc=enst-bretagne,dc=fr'
LDAP_PASSWORD = '' # LDAP password
LEASES_DN = 'ou=leases,dc=resel,dc=enst-bretagne,dc=fr'
DEVICES_DN = 'ou=devices,dc=resel,dc=enst-bretagne,dc=fr'


MESSAGES = ['OK', 'No free IP', 'No lease', 'Unaddressable pool', 'Configuration error',
            'LDAP error']


DISCOVERY_LINE = '{}// dhcp.discover{{relay_ip={},mac={},ip={},status={}}} 1\n'
DISCOVERY_LOG_FILE = '/tmp/discover'
REQUEST_LINE = '{}// dhcp.request{{relay_ip={},mac={},ip={},status={}}} 1\n'
REQUEST_LOG_FILE = '/tmp/request'


SERVER_IP = '10.3.12.1'
