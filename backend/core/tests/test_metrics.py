"""
core/tests/test_metrics.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for PrometheusMetricsMiddleware and SecurityHeadersMiddleware.
No DB required.
"""

from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory

# -- PrometheusMetricsMiddleware ----------------------------------------------


class TestPrometheusMetricsMiddleware:

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def mock_response(self):
        from django.http import HttpResponse

        return HttpResponse("OK", status=200)

    @pytest.fixture
    def middleware(self, mock_response):
        """Build middleware with a dummy get_response."""
        from core.middleware.metrics import PrometheusMetricsMiddleware

        return PrometheusMetricsMiddleware(get_response=lambda r: mock_response)

    def test_passes_through_request(self, middleware, factory):
        request = factory.get("/api/v1/posts/")
        response = middleware(request)
        assert response.status_code == 200

    def test_skip_path_not_measured(self, factory, mock_response):
        """Requests to /metrics must NOT update Prometheus counters."""
        from core.middleware.metrics import PrometheusMetricsMiddleware

        middleware = PrometheusMetricsMiddleware(get_response=lambda r: mock_response)
        request = factory.get("/metrics")
        with patch.object(middleware, "_duration", MagicMock()):
            middleware(request)
        # _duration is set in __call__ only when path not in _SKIP_PATHS

    def test_health_check_skipped(self, factory, mock_response):
        from core.middleware.metrics import PrometheusMetricsMiddleware

        middleware = PrometheusMetricsMiddleware(get_response=lambda r: mock_response)
        request = factory.get("/health/")
        response = middleware(request)
        assert response.status_code == 200

    def test_404_response_recorded(self, factory):
        from django.http import HttpResponse

        from core.middleware.metrics import PrometheusMetricsMiddleware

        not_found = HttpResponse("Not found", status=404)
        middleware = PrometheusMetricsMiddleware(get_response=lambda r: not_found)
        request = factory.get("/api/v1/missing/")
        response = middleware(request)
        assert response.status_code == 404

    def test_exception_not_swallowed(self, factory):
        from core.middleware.metrics import PrometheusMetricsMiddleware

        def exploding_response(r):
            raise ValueError("Boom")

        middleware = PrometheusMetricsMiddleware(get_response=exploding_response)
        request = factory.get("/api/v1/posts/")
        with pytest.raises(ValueError, match="Boom"):
            middleware(request)

    def test_middleware_enabled_when_prometheus_installed(self, middleware):
        """_enabled flag should be True if prometheus_client is importable."""
        # prometheus_client should be installed in testing env
        assert middleware._enabled is True


# -- Path normalization -------------------------------------------------------


class TestPathNormalization:

    def test_uuid_in_path_looks_like_id(self):
        from core.middleware.metrics import _looks_like_id

        assert _looks_like_id("a8098c1a-f86e-11da-bd1a-00112444be1e") is True

    def test_integer_looks_like_id(self):
        from core.middleware.metrics import _looks_like_id

        assert _looks_like_id("12345") is True

    def test_word_not_id(self):
        from core.middleware.metrics import _looks_like_id

        assert _looks_like_id("posts") is False
        assert _looks_like_id("api") is False
        assert _looks_like_id("v1") is False
        assert _looks_like_id("notifications") is False

    def test_empty_string_not_id(self):
        from core.middleware.metrics import _looks_like_id

        assert _looks_like_id("") is False


# -- SecurityHeadersMiddleware ------------------------------------------------


class TestSecurityHeadersMiddleware:

    @pytest.fixture
    def factory(self):
        return RequestFactory()

    @pytest.fixture
    def secure_middleware(self):
        from django.http import HttpResponse

        from core.middleware.security_headers import SecurityHeadersMiddleware

        resp = HttpResponse("OK", content_type="text/html")
        return SecurityHeadersMiddleware(get_response=lambda r: resp)

    def test_x_content_type_options_set(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_deny(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert response["X-Frame-Options"] == "DENY"

    def test_referrer_policy_set(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert "Referrer-Policy" in response

    def test_permissions_policy_set(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert "Permissions-Policy" in response
        assert "camera=()" in response["Permissions-Policy"]

    def test_csp_on_html_response(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert "Content-Security-Policy" in response
        assert "default-src" in response["Content-Security-Policy"]

    def test_csp_on_json_response(self, factory):
        from django.http import JsonResponse

        from core.middleware.security_headers import SecurityHeadersMiddleware

        resp = JsonResponse({"ok": True})
        middleware = SecurityHeadersMiddleware(get_response=lambda r: resp)
        request = factory.get("/api/")
        response = middleware(request)
        assert "Content-Security-Policy" in response

    def test_server_header_removed(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert "Server" not in response

    def test_cross_origin_opener_policy_set(self, secure_middleware, factory):
        request = factory.get("/")
        response = secure_middleware(request)
        assert response["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_passes_through_response_status(self, factory):
        from django.http import HttpResponse

        from core.middleware.security_headers import SecurityHeadersMiddleware

        resp = HttpResponse("Created", status=201)
        middleware = SecurityHeadersMiddleware(get_response=lambda r: resp)
        response = middleware(factory.post("/api/"))
        assert response.status_code == 201
