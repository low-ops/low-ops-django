import os
import unittest
from unittest.mock import patch

from django.http import request as django_request

from config.hosts import (
    _is_internal_probe_host,
    build_allowed_hosts,
    build_csrf_trusted_origins,
    patch_validate_host_for_kubernetes,
)


class BuildAllowedHostsTests(unittest.TestCase):
    def test_includes_application_url_hostname(self):
        with patch.dict(
            os.environ,
            {'APPLICATION_URL': 'https://app.example.com', 'ALLOWED_HOSTS': ''},
            clear=False,
        ):
            hosts = build_allowed_hosts(debug=False)
        self.assertIn('app.example.com', hosts)
        self.assertIn('localhost', hosts)

    def test_falls_back_to_ci_cinaq_domain_when_application_url_unset(self):
        with patch.dict(
            os.environ,
            {'APPLICATION_URL': '', 'ALLOWED_HOSTS': ''},
            clear=False,
        ):
            hosts = build_allowed_hosts(debug=False)
        self.assertIn('.ci.cinaq.com', hosts)

    def test_ci_cinaq_subdomain_is_allowed(self):
        with patch.dict(
            os.environ,
            {'APPLICATION_URL': '', 'ALLOWED_HOSTS': ''},
            clear=False,
        ):
            hosts = build_allowed_hosts(debug=False)
        from django.http.request import validate_host

        self.assertTrue(validate_host('django-dev.ci.cinaq.com', hosts))

    def test_csrf_trusted_origins_fall_back_to_ci_cinaq(self):
        with patch.dict(
            os.environ,
            {'APPLICATION_URL': '', 'CSRF_TRUSTED_ORIGINS': ''},
            clear=False,
        ):
            origins = build_csrf_trusted_origins(debug=False)
        self.assertIn('https://*.ci.cinaq.com', origins)

    def test_includes_pod_ip_when_set(self):
        with patch.dict(
            os.environ,
            {'POD_IP': '10.244.1.148', 'ALLOWED_HOSTS': 'app.example.com'},
            clear=False,
        ):
            hosts = build_allowed_hosts(debug=False)
        self.assertIn('10.244.1.148', hosts)


class KubernetesHostValidationTests(unittest.TestCase):
    def test_private_pod_ip_is_allowed(self):
        self.assertTrue(_is_internal_probe_host('10.244.1.148:8000'))

    def test_public_ip_is_rejected(self):
        self.assertFalse(_is_internal_probe_host('8.8.8.8:8000'))

    def test_validate_host_accepts_private_ip(self):
        original = django_request.validate_host
        patch_validate_host_for_kubernetes()
        try:
            self.assertTrue(django_request.validate_host('10.244.1.148:8000', []))
        finally:
            django_request.validate_host = original
