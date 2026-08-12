import ipaddress
import os
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from django.http import request as django_request

from config.env import get_application_hostname, get_application_url

_LOOPBACK_HOSTS = ('localhost', '127.0.0.1', '[::1]')
# Matches the Low-Ops Next.js template fallback when APPLICATION_URL is unset.
_LOWOPS_DEFAULT_HOST_PATTERNS = ('.ci.cinaq.com',)


def build_allowed_hosts(*, debug):
    hosts = []

    application_url = get_application_url()
    if application_url:
        hostname = urlparse(application_url).hostname
        if hostname:
            hosts.append(hostname)

    env_value = os.environ.get('ALLOWED_HOSTS', '').strip()
    if env_value:
        hosts.extend(part.strip() for part in env_value.split(',') if part.strip())

    if not application_url:
        hosts.extend(_LOWOPS_DEFAULT_HOST_PATTERNS)

    pod_ip = os.environ.get('POD_IP', '').strip()
    if pod_ip:
        hosts.append(pod_ip)

    hosts.extend(_LOOPBACK_HOSTS)

    unique_hosts = list(dict.fromkeys(hosts))
    if unique_hosts:
        return unique_hosts

    if debug:
        return list(_LOOPBACK_HOSTS)

    raise ImproperlyConfigured(
        'ALLOWED_HOSTS must be set when DEBUG is false '
        '(comma-separated hostnames) or provide APPLICATION_URL.'
    )


def _is_internal_probe_host(host):
    domain, _port = django_request.split_domain_port(host)
    try:
        ip = ipaddress.ip_address(domain)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local


def _matches_application_hostname(host):
    hostname = get_application_hostname()
    if not hostname:
        return False
    domain, _port = django_request.split_domain_port(host)
    return domain == hostname


def patch_validate_host_for_kubernetes():
    original_validate_host = django_request.validate_host

    def validate_host(host, allowed_hosts):
        if original_validate_host(host, allowed_hosts):
            return True
        if _matches_application_hostname(host):
            return True
        return _is_internal_probe_host(host)

    django_request.validate_host = validate_host
