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

import json
from pathlib import Path
from typing import Optional, Any,Dict
import requests
from agentcore.utils.config import VALIDATE_URL

from agentcore.utils.config import CONFIG_FILE, CONFIG_DIR
class ConfigManager:
    """
    Manages general configuration settings for the application.
    Reads and writes configurations to a persistent JSON file.
    """
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            CONFIG_FILE.write_text(json.dumps({}))
        if CONFIG_FILE.exists():
            self.config_data = self._read_config()
        else:
            self.config_data = {}

    def initialize(self):
        """
        Explicitly initialize config directory and default config file.
        """
        CONFIG_DIR.mkdir(exist_ok=True)
        if not CONFIG_FILE.exists():
            default_data = {
                "url": "https://agentcore.coreops.ai/",
                "access_token": "",  
                "refresh_token": "",  
                "login_email": "",
                "login_password": ""
            }
            self._write_config(default_data)
            self.config_data = default_data

    def _read_config(self) -> dict:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    def _write_config(self, data: dict) -> None:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieve a configuration value with an optional default.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key is not found.
        
        Returns:
            Value associated with the key or default.
        """
        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value and persist it.
        
        Args:
            key: Configuration key to set.
            value: Value to set for the key.
        """
        self.config_data[key] = value
        self._write_config(self.config_data)

    def url(self) -> str:
        return self.get("url", "")

    def token(self) -> Optional[str]:
        """Get the access token or None if not set or invalid."""
        token = self.get("access_token")
        # Return None for placeholder or empty tokens
        return None if token in (None, "", "e") else token
    
    def access_token(self) -> Optional[str]:
        """For backwards compatibility"""
        return self.token()

    def refresh_token(self) -> Optional[str]:
        token = self.get("refresh_token")
        return None if token in (None, "", "e") else token

    def set_token(self, token: str, token_type: str = "access") -> None:
        """
        Set access or refresh token.
        
        Args:
            token: Token string.
            token_type: Type of token (access or refresh).
        """
        self.set(f"{token_type}_token", token)
    
    def set_url(self, url: str) -> None:
        self.set("url", url)
    
    def set_time(self, time:str) -> None:
        self.set("login_time",time)

    def login_time(self) -> str:
        return self.get("login_time", "")
    
    def set_user_id(self, user_id: str) -> None:
        return self.set("user_id", user_id)
    
    def get_user_id(self) -> None:
        return self.get("user_id", "")
    
    def clear_details(self) -> None:
        """Clear all authentication details (for logout)"""
        self.set("access_token", None)
        self.set("refresh_token", None)
        self.set("login_email", None)
        self.set("login_password", None)
        self.set("user_id", None)
        self.set("login_time", None)
        self.set("url", "https://agentcore.coreops.ai/")  # Reset to default URL


    def save_login_credentials(self, email: str, password: str) -> None:
        """Save login credentials securely."""
        # Note: In production, consider encrypting passwords
        self.set("login_email", email)
        self.set("login_password", password)

    def get_login_credentials(self) -> Optional[Dict[str, str]]:
        """Retrieve saved login credentials."""
        email = self.get("login_email")
        password = self.get("login_password")
        return {"email": email, "password": password} if email and password else None
    
    # import requests

    # def is_django_server_running(url: str) -> bool:
    #     try:
    #         response = requests.get(url, timeout=3)
    #         return response.status_code == 200
    #     except requests.exceptions.RequestException:
    #         return False

    # # Example usage
    # if is_django_server_running("http://192.168.10.225/"):
    #     print("Django server is running.")
    # else:
    #     print("Django server is not running.")

    def validate_url(self,url):
        """Validate the URL using the direct check function."""
        try:
            url = url + VALIDATE_URL
            response = requests.get(url)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
        
    def is_demo_user(self) -> bool:
        """
        Check if the current logged-in user has DEMO role.
        
        Returns:
            bool: True if user has DEMO role, False otherwise.
        """
        if not self.token():
            return False
        
        try:
            from managers.users_manager import UserManager
            user_manager = UserManager()
            user_data = user_manager.get_user_with_role_names()
            print(user_data)
            if user_data and 'role_names' in user_data:
                role_names = user_data['role_names']
                # Check if 'DEMO' is in the role names (case-insensitive)
                return any(role.upper() == 'DEMO' for role in role_names)
            
            return False
            
        except Exception as e:
            # Log the error if you have logging set up
            # print(f"Error checking demo user status: {str(e)}")
            return False
        