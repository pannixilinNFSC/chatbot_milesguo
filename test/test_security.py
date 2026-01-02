"""
Unit tests for security module.
All external dependencies are mocked.
"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi import HTTPException


class TestRequireAuth:
    """Tests for require_auth dependency."""
    
    def test_require_auth_disabled(self):
        """Test require_auth when auth is disabled."""
        with patch("lib.security.http_security._is_auth_enabled", return_value=False):
            from lib.security import require_auth
            # Should not raise exception
            mock_request = Mock()
            mock_request.query_params = {}
            mock_request.headers = {}
            require_auth(mock_request, token=None)

    def test_require_auth_rejects_missing_token(self):
        with patch("lib.security.http_security._is_auth_enabled", return_value=True):
            from lib.security import require_auth

            with pytest.raises(HTTPException) as exc_info:
                mock_request = Mock()
                mock_request.query_params = {}
                mock_request.headers = {}
                require_auth(mock_request, token=None)

            assert exc_info.value.status_code == 401
            assert "Missing bearer token" in exc_info.value.detail

    def test_require_auth_accepts(self):
        with patch("lib.security.http_security._is_auth_enabled", return_value=True), patch(
            "lib.security.http_security._get_expected_token", return_value="valid_token"
        ):
            from lib.security import require_auth

            mock_request = Mock()
            mock_request.query_params = {}
            mock_request.headers = {}
            require_auth(mock_request, token="valid_token")

    def test_require_auth_accepts_query_param_token(self):
        with patch("lib.security.http_security._is_auth_enabled", return_value=True), patch(
            "lib.security.http_security._get_expected_token", return_value="valid_token"
        ):
            from lib.security import require_auth

            mock_request = Mock()
            mock_request.query_params = {"token": "valid_token"}
            mock_request.headers = {}
            require_auth(mock_request, token=None)


class TestGlobalExceptionHandler:
    """Tests for global exception handler."""
    
    @pytest.mark.asyncio
    async def test_global_exception_handler_generic_exception_maps_to_500(self):
        from fastapi import Request
        from fastapi.responses import JSONResponse
        from lib.security import global_exception_handler
        
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        mock_request.query_params = {}
        
        response = await global_exception_handler(mock_request, ValueError("Test error"))
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        data = json.loads(response.body.decode())
        assert "Test error" in data["detail"]

