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

from agentcore.utils.config import CREDENTIALS_ENDPOINT, CREDENTIALS_TYPES
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.utils.config import CREDENTIALS_USERS
from datetime import datetime, timezone, timedelta


class CredentialsManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.columns = [
            "access_key", "Secret_key"
        ]
    
    @BaseManager.handle_api_error
    def store_credentials(self, access_key=None, secret_key=None):
        if access_key is None:
            self.console.print("[bold blue]Store your AWS Credentials (interactive mode)[/bold blue]")
            access_key = Prompt.ask("[bold]Access key[/bold]")
            secret_key = Prompt.ask("[bold]Secret key[/bold]")
        
        credentials_data = {
            'access_key': access_key,
            'secret_key': secret_key
        }

        response = self._execute_with_progress(
            "Saving Credentials...",
            lambda: self.api_client.post(endpoint=CREDENTIALS_ENDPOINT, data=credentials_data)
        )

        if response:
            self.console.print("[green]Credentials Stored successfully![/green]")
        return None


class CredentialManager(BaseManager):
    def __init__(self):
        super().__init__()
        self.columns = ["ID", "Name", "Credential Type Name", "Created At"]
        self._credential_types_cache = None
        self.aws_credentials_columns = ['ID', 'Name', 'Credential Type Name', 'Access Token', 'Secret Key']
        self.github_token_credentials_columns = ['ID', 'Name', 'Credential Type Name', 'URL', 'PAT Token']
        self.github_credentials_columns = ['ID', 'Name', 'Credential Type Name', 'URL']
        self.github_credentials_credentials_columns = ['ID', 'Name', 'Git Email', 'Git Username', 'Github Token']

    @BaseManager.handle_api_error
    def create_user_credential(self, user_id, payload):
        """
        Create a new credential for the user.

        Args:
            user_id (str): ID of the user.
            payload (dict): Credential payload.

        Returns:
            dict or None: Created credential details if successful, otherwise None.
        """
        endpoint = CREDENTIALS_USERS.format(user_id=user_id)
        response = self._execute_with_progress(
            f"Creating credential for user {user_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response

    def _enrich_credential_response(self, response, credential_type_id):
        """
        Enrich the response with credential type information if missing.
        
        Args:
            response (dict): The API response
            credential_type_id: The ID of the credential type
            
        Returns:
            dict: Enriched response with credential type name
        """
        try:
            # Check if credential_type is missing or incomplete
            if not response.get("credential_type") or response.get("credential_type") == "-":
                # Fetch credential types if not cached
                if not self._credential_types_cache:
                    self._credential_types_cache = self._get_credential_types()
                
                # Find the matching credential type
                for cred_type in self._credential_types_cache:
                    if cred_type.get("id") == credential_type_id:
                        response["credential_type"] = cred_type.get("name", "Unknown")
                        break
                else:
                    response["credential_type"] = "Unknown"
                    
        except Exception as e:
            # If enrichment fails, keep original response
            print(f"Warning: Could not enrich credential type: {e}")
            
        return response

    def get_credential_types(self):
        """
        Fetch available credential types from the API.
        
        Returns:
            list: List of credential types
        """
        
        response = self._execute_with_progress(
            f"Fetching credential types...",
            lambda: self.api_client.get(endpoint=CREDENTIALS_TYPES)
        )

        return response

    @BaseManager.handle_api_error
    def get_user_credentials(self, user_id):
        """
        Get all credentials for a user.
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            dict or None: User credentials if successful, otherwise None
        """
        endpoint = CREDENTIALS_USERS.format(user_id=user_id)
        response = self._execute_with_progress(
            f"Fetching credentials for user {user_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        return response

    def _format_datetime(self, datetime_string):
        """
        Format ISO datetime string to IST timezone and readable format.
        
        Args:
            datetime_string (str): ISO format datetime string (UTC)
            
        Returns:
            str: Formatted datetime string in IST
        """
        try:
            # Parse the UTC datetime string
            if datetime_string.endswith('Z'):
                # Remove Z and create UTC datetime
                dt_utc = datetime.fromisoformat(datetime_string[:-1]).replace(tzinfo=timezone.utc)
            else:
                dt_utc = datetime.fromisoformat(datetime_string).replace(tzinfo=timezone.utc)
            
            # Convert to IST (UTC + 5:30)
            ist_timezone = timezone(timedelta(hours=5, minutes=30))
            dt_ist = dt_utc.astimezone(ist_timezone)
            
            # Format to a more readable format in IST
            return dt_ist.strftime("%b %d, %Y at %I:%M %p IST")
        except Exception as e:
            # If formatting fails, return original string
            print(f"Date formatting error: {e}")
            return datetime_string