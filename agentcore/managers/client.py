# ###################################################################################
# Business Source License 1.1

# This file is licensed under the Business Source License 1.1 (BSL 1.1). 
# You may not use this file except in compliance with the License.

# You may obtain a copy of the License at:
# https://mariadb.com/bsl11

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# Change Date: 2028-08-01 (3 years from initial release)

# On the Change Date, the License will change to a specified open source license:
# Apache License, Version 2.0

# Original Developer: CoreOps.AI 
# Original License Date: 2025-07-24
# ###################################################################################

import requests
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, Union
import logging
from datetime import datetime
import time
from agentcore.managers.config import ConfigManager
from agentcore.utils.config import TOKEN_ENDPOINT
from enum import Enum


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class APIError(Exception):
    """Custom exception for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class TokenManager:
    """Handles token management, including refresh logic."""

    def __init__(self, config: ConfigManager, client: "APIClient"):
        self.config = config
        self.client = client
        self.logger = logging.getLogger(__name__)  # Initialize logger

    def refresh_token(self) -> bool:
        """Refresh access token, or re-login if refresh token expired."""
        refresh_token = self.config.refresh_token()

        # Attempt to refresh the access token
        if refresh_token:
            try:
                response = self.client.post(f"{TOKEN_ENDPOINT}refresh/", data={"refresh": refresh_token})
                if response and "access" in response:
                    new_access_token = response["access"]
                    self.config.set_token(new_access_token, token_type="access")
                    self.client.set_token(new_access_token)
                    # self.logger.info("Access token refreshed successfully.")
                    return True
                else:
                    # self.logger.warning("Refresh token API did not return a new access token.")
                    raise APIError("Session expired. Please login again.", status_code=401)
            except APIError:
                raise APIError("Session expired. Please login again.", status_code=401)
        
        raise APIError("Please login to run the Agentcore.", status_code=401)
        

class APIClient:
    """
    Enhanced API Client with token authentication, retry logic, comprehensive error handling, and logging.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        # THis has to be externalized and timeout should be according to request made. 
        # For example creating the environment is may not be completed in 100 sec
        # timeout: int = 100,
        timeout: int = 300,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None,
        config: Optional[ConfigManager] = None,
        verify_ssl: bool = True
    ):
        self.config = config or ConfigManager()
        self.base_url = base_url or self.config.url()
        self.timeout = timeout
        self.session = self._create_session(max_retries, verify_ssl)
        self.logger = logger or self._setup_logger()
        self.token_manager = TokenManager(self.config, self)
        token = self.config.access_token()
        if token:
            self.set_token(token)

    def _create_session(self, max_retries: int, verify_ssl: bool = True) -> requests.Session:
        """Create and configure requests session with retry logic."""
        import urllib3
        
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        session = requests.Session()
        session.verify = verify_ssl

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AgentCore-Client/1.0",
        })

        return session

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the API client."""
        logger = logging.getLogger("agentcore.api")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def set_token(self, token: str) -> None:
        """Set the authentication token in the session headers."""
        self.session.headers["Authorization"] = f"Bearer {token}"
        # self.logger.debug("Authentication token set successfully")

    def _handle_response(self, response: requests.Response, start_time: float) -> Dict[str, Any]:
        """Handle response and check for token expiration."""
        try:
            response.raise_for_status()

            # Prevent JSON parsing on empty responses (e.g., 204 No Content)
            if response.status_code == 204 or not response.text.strip():
                return {}

            return response.json()

        except HTTPError as e:
            if response.status_code == 401:
                # Safely attempt JSON parsing only if content exists
                try:
                    error_detail = response.json().get("detail", "")
                except ValueError:
                    error_detail = ""

                if error_detail in ["Invalid credentials", "No active account found with the given credentials"]:
                    # self.logger.error("Invalid login credentials provided.")
                    raise APIError(message=error_detail, status_code=401)

                elif error_detail in ["Given token not valid for any token type", "Authentication credentials were not provided."]:
                    # self.logger.warning("Access token expired. Attempting to refresh...")

                    if self.token_manager.refresh_token():
                        # self.logger.info("Token refreshed successfully. Retrying request...")
                        raise APIError(message="Given token not valid for any token type", status_code=401) # Retry the failed request automatically

                    # self.logger.error("Token refresh failed. Please log in again.")
                    raise APIError(message="Token refresh failed. Please log in again.", status_code=401)

            # self.logger.error(f"HTTP error: {e}")
            raise APIError(message=response.text, status_code=response.status_code)

        except ValueError:
            # self.logger.error("Failed to parse JSON response.")
            raise APIError(message="Invalid response format", status_code=response.status_code)



    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Generic request handler."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        start_time = time.time()

        # Handle file uploads by temporarily removing Content-Type header
        content_type_removed = False
        if files:
            content_type = self.session.headers.pop("Content-Type", None)
            content_type_removed = True
        
        try:
            # Build request parameters
            request_params = {
                'method': method,
                'url': url,
                'timeout': self.timeout,
                **kwargs  # Include any additional kwargs
            }
            
            # Add data and files if provided
            if data is not None:
                request_params['data'] = data
            if files is not None:
                request_params['files'] = files
                
            response = self.session.request(**request_params)
            
            return self._handle_response(response, start_time)
        except Timeout:
            raise APIError(message="Request timed out")
        except ConnectionError as e:
            raise APIError(message="Connection error")
        except RequestException as e:
            raise APIError(message="Request failed")
        finally:
            # Restore the Content-Type header if we removed it
            if content_type_removed and content_type:
                self.session.headers["Content-Type"] = content_type

    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Perform GET request."""
        return self._request(HTTPMethod.GET.value, endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Perform POST request with support for form-data uploads."""
        if files:
            # For file uploads, don't use json parameter, use data for form fields
            return self._request(HTTPMethod.POST.value, endpoint, data=data, files=files, **kwargs)
        return self._request(HTTPMethod.POST.value, endpoint, json=data, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Perform PUT request."""
        return self._request(HTTPMethod.PUT.value, endpoint, json=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Perform DELETE request."""
        return self._request(HTTPMethod.DELETE.value, endpoint, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Perform PATCH request."""
        return self._request(HTTPMethod.PATCH.value, endpoint, json=data, **kwargs)

    def health_check(self) -> bool:
        """Perform a health check."""
        try:
            response = self.get("health")
            return response is not None
        except APIError:
            return False

    def upload_file(self, endpoint: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Upload a file to the server."""
        with open(file_path, "rb") as file:
            files = {"file": file}
            return self._request(HTTPMethod.POST.value, endpoint, files=files, **kwargs)

    def download_file(self, endpoint: str, save_path: str, **kwargs) -> None:
        """Download a file from the server."""
        response = self.session.get(f"{self.base_url}/{endpoint}", stream=True, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        # self.logger.info(f"File downloaded successfully: {save_path}")

    def get_logs(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Fetch logs from the server."""
        return self.get(endpoint, params=params, **kwargs)

    def log_event(self, endpoint: str, event: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Log an event to the server."""
        return self.post(endpoint, data=event, **kwargs)
