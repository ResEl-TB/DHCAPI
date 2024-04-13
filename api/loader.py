"""This module loads the DHCP configuration and gives functions to process it"""


import toml
from .exceptions import FieldUndefinedException, NoRuleMatchedException
from .ip import Network, IP
from .constants import CONFIG_FILE


CONF = toml.load(CONFIG_FILE)
DURATIONS = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}


def parse(value, env):
    """
    Smart parse a value by visiting its structure recursively and formatting its strings
    :param value: The value to parse
    :param env: The environment for value substitution in strings
    :returns: The parsed value
    """
    if isinstance(value, str):
        return value.format(**env)
    if isinstance(value, list):
        return [parse(x, env) for x in value]
    if isinstance(value, dict):
        return {k: parse(v, env) for k, v in value.items()}
    return value


def set_vals(conf, env):
    """
    Define the values from the configuration in the environment
    :param conf: The configuration to process
    :parm env: The environment
    """
    for name in [x for x in conf if x[:1].islower()]:
        value = conf[name]
        if isinstance(value, dict) and 'call' in value:
            env[name] = env[value['call']](*(parse(x, env) for x in value['args']))
            if 'values' in value:
                values = value['values']
                for i, v in enumerate(values):
                    # Here we avoid a common problem with closures
                    env[v] = (lambda i, name: lambda e: e[name] == i)(i, name)
        else:
            env[name] = parse(value, env)


def visit_subrules(conf, env):
    """
    Recursively visit matching subrules of a configuration
    :param conf: The configuration to process
    :param env: The environment
    """
    set_vals(conf, env)
    for subrule in [x for x in conf if isinstance(conf[x], dict) and x[:1].isupper()]:
        if env[subrule](env):
            visit_subrules(conf[subrule], env)
            return


def mask_extract(ip, mask):
    """Helper function around IP.extract"""
    return IP(ip).extract(IP(mask))


def get_env(relay_ip, mac):
    """
    Get the environment matching the configuration
    :param relay_ip: The relay IP address
    :param mac: The client MAC address
    :returns: The environment
    """
    env = {'relay_ip': relay_ip, 'mac': mac, 'mask_extract': mask_extract}
    set_vals(CONF, env)
    for conf in [conf for k, conf in CONF.items() if isinstance(conf, dict) and k[:1].isupper()]:
        network = Network(conf['match'])
        if relay_ip in network:
            visit_subrules(conf, env)
            if any(k not in env for k in ['lease_duration', 'first', 'last']):
                raise FieldUndefinedException(env)
            filtered_env = parse({k: v for k, v in env.items() if k[:1].islower()}, env)
            first = filtered_env['first']
            last = filtered_env['last']
            relay_ip = IP(relay_ip)
            base = network.base_ip(relay_ip)
            filtered_env['first'] = base + first if first[:1] == '+' else IP(first)
            filtered_env['last'] = base + last if last[:1] == '+' else IP(last)
            filtered_env['mask'] = filtered_env.get('mask', network.contiguous_mask)
            if 'router_ip' in filtered_env:
                router_ip = filtered_env['router_ip']
                filtered_env['router_ip'] = (base + router_ip if router_ip[:1] == '+'
                                                              else IP(router_ip))
            else:
                filtered_env['router_ip'] = relay_ip
            if 'lease_prefix' not in filtered_env:
                filtered_env['lease_prefix'] = ''
            duration = filtered_env['lease_duration']
            if isinstance(duration, str):
                filtered_env['lease_duration'] = int(duration[:-1]) * DURATIONS[duration[-1]]
            return filtered_env
    raise NoRuleMatchedException(env)
