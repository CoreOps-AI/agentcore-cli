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

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.traceback import install
from functools import wraps
import json
from datetime import datetime
import requests

from agentcore.managers.base import BaseManager, ConfigurationError
from agentcore.managers.client import APIError
from agentcore.utils.config import TOKEN_ENDPOINT,USERS_ENDPOINT, FORGOT_PASSWORD_ENDPOINT, VERIFY_OTP_ENDPOINT, RESET_PASSOWRD_ENDPOINT, SIGNUP_ENDPOINT


class LoginManager(BaseManager):
    """
    Class to manage all login-related operations.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
    
    @BaseManager.handle_api_error    
    def user_login(self, email: str, password: str):
        """Enhanced login method with credential saving."""

        login_data = {
            'email': email,
            'password': password
        }

        try:
            response = self._execute_with_progress(
                "Fetching Tokens...",
                lambda: self.api_client.post(endpoint=TOKEN_ENDPOINT, data=login_data)
            )
            access_token = response.get("access")
            refresh_token = response.get("refresh")
            user_id = response.get("user_id")
            logged_in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not access_token or not refresh_token:
                self.console.print("[red]Login failed: Invalid credentials or server error[/red]")
                return None

            # Save login credentials and tokens
            self.config_manager.save_login_credentials(email, password)
            self.config_manager.set_token(access_token, token_type="access")
            self.config_manager.set_token(refresh_token, token_type="refresh")
            self.config_manager.set_time(logged_in_time)
            self.config_manager.set_user_id(user_id)

            self.console.print("[green]Login successful! Tokens and credentials saved.[/green]")
            return response

        except APIError as e:
            self.console.print(Panel(
                f"[red]API Error: {e.message}[/red]\n"
                f"Status Code: {e.status_code or 'N/A'}",
                title="Error"
            ))
            return None

    @BaseManager.handle_api_error    
    def password_change(self, password_data):
        """
        Change user password with the provided credentials.
        
        Args:
            password_data (dict): Dictionary containing current_password, 
                                new_password, and confirm_password
        
        Returns:
            dict: API response on success, None on failure
        """

        response = self._execute_with_progress(
            "Changing Password...",
            lambda: self.api_client.post(endpoint=USERS_ENDPOINT + "change-password/", data=password_data)
        )

        if response :
            self.console.print("[bold green]✓ Password changed successfully![/bold green]")
            return response
        else:
            error_msg = response.get("message", "Unknown error occurred") if response else "No response from server"
            self.console.print(f"[bold red]Failed to change password: {error_msg}[/bold red]")
            return None
      
    @BaseManager.handle_api_error    
    def forgot_passowrd(self, payload):
        """
        Change user password with the OTP.
        """

        response = self._execute_with_progress(
            "Sending OTP....",
            lambda:self.api_client.post(endpoint =FORGOT_PASSWORD_ENDPOINT ,data = payload)
        )

        return response
    
    @BaseManager.handle_api_error    
    def verify_otp(self, payload):
        """
        Change user password with the OTP.
        """

        response = self._execute_with_progress(
            "Verifying OTP....",
            lambda:self.api_client.post(endpoint =VERIFY_OTP_ENDPOINT ,data = payload)
        )

        return response
    
    @BaseManager.handle_api_error    
    def reset_password(self, payload):
        """
        Change user password with the OTP.
        """

        response = self._execute_with_progress(
            "Reseting the Password....",
            lambda:self.api_client.post(endpoint =RESET_PASSOWRD_ENDPOINT ,data = payload)
        )

        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def user_signup(self, payload):
        """
        Sign up a new user with the provided credentials.
        
        Args:
            payload (dict): Dictionary containing user details for signup
        
        Returns:
            dict: API response on success, None on failure
        """

        response = self._execute_with_progress(
            "Signing Up...",
            lambda: self.api_client.post(endpoint=SIGNUP_ENDPOINT, data=payload)
        )

        return response


