"""This module implements the HTTP API endpoint"""

import logging
from flask import Flask, request, jsonify
from . import discovery, requesting
from .ip import IP
from .ldap import Ldap
from .constants import LDAP_USER, LDAP_PASSWORD, MASTER_LDAP, SLAVE_LDAPS


app = Flask(__name__)
logging.basicConfig(filename='/var/log/dhcapi.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')
ldap = Ldap(LDAP_USER, LDAP_PASSWORD, MASTER_LDAP, SLAVE_LDAPS)


@app.route('/discover', methods=['POST'])
def discover():
    """This route is the endpoint to answer DHCPDISCOVERs"""
    relay_ip = IP(request.form.get('relay_ip'))
    mac = ''.join(request.form.get('mac').split(':')).lower()

    if relay_ip == '0.0.0.0':
        return discovery.Result.do_not_respond(), 200

    result = discovery.process(ldap, relay_ip, mac)

    discovery.log(mac, result)

    return jsonify(result.get_dict()), 200

@app.route('/request', methods=['POST'])
def req():
    """This route is the endpoint to answer DHCPREQUESTs"""
    relay_ip = IP(request.form.get('relay_ip'))
    try:
        requested_ip = IP(request.form.get('requested_ip'))
    except ValueError:
        return requesting.Result.nak()
    mac = ''.join(request.form.get('mac').split(':')).lower()
    hostname = request.form.get('hostname').strip()

    if relay_ip == '0.0.0.0':
        return requesting.Result.do_not_respond(), 200

    result = requesting.process(ldap, relay_ip, requested_ip, mac, hostname)

    requesting.log(mac, result)

    return jsonify(result.get_dict()), 200

@app.route('/cleanup')
def cleanup():
    """This route is the endpoint to remove old leases"""
    ldap.remove_expired_leases()
    return jsonify(None), 204
