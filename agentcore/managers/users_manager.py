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
from rich.prompt import Prompt
from rich.traceback import install
from rich.panel import Panel

from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.utils.config import USERS_ENDPOINT, ROLES_ENDPOINT, USER_ME_ENDPOINT
from agentcore.managers.client import APIError
from functools import wraps
from rich.console import Console

console = Console()

install()

class UserManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.columns = [
            "ID", "Username", "Email", "First Name", "Last Name", "Active Status", "Roles"
        ]
    
    def get_display_columns(self, response_data):
        """
        Get the columns to display based on the response data.
        Adds Password column if generated_password exists in any result.
        """
        columns = list(self.columns)  # Convert to list to modify
        results = response_data
        
        if any('generated_password' in result for result in results):
            columns.append('Password')
            
        return columns

    @BaseManager.handle_api_error
    def view_users(self):
        """Fetch all users."""
        return self._execute_with_progress(
            "Fetching users...",
            lambda: self.api_client.get(USERS_ENDPOINT)
        )

    @BaseManager.handle_api_error
    def view_roles(self):
        """Fetch all roles."""
        return self._execute_with_progress(
            "Fetching roles...",
            lambda: self.api_client.get(ROLES_ENDPOINT)
        )
    
    @BaseManager.handle_api_error
    def user_create(self, user_data):
        """Create a new user by calling the API."""
        response = self._execute_with_progress(
            "Creating user...",
            lambda: self.api_client.post(endpoint=USERS_ENDPOINT, data=user_data)
        )
        return response
    
    def assign_role(self, payload_data):
        """ 
        Add and Remove roles to An user
        """

        response = self._execute_with_progress(
            "Assigning and Removing Roles...",
            lambda: self.api_client.patch(endpoint=USERS_ENDPOINT + "assign/", data=payload_data)
        )

        return response
    
    def get_roles(self):
        """Fetch all available roles."""

        response = self._execute_with_progress(
            "Fetching Roles...",
            lambda: self.api_client.get(endpoint=ROLES_ENDPOINT)
        )
        return response

    @BaseManager.handle_api_error
    def fetch_user(self, user_id):
        """
        Fetch user details by their ID.
        """
        response = self._execute_with_progress(
            f"Fetching user {user_id} details...",
            lambda: self.api_client.get(endpoint=f"{USERS_ENDPOINT}{user_id}/")
        )
       
        return response
 
   
    def update_user(self, user_data,user_id):
        """
        Update an existing user.
       
        Args:
            user_data (dict): Dictionary containing user data to update
           
        Returns:
            dict: Updated user data if successful, None otherwise
        """
           
        response = self._execute_with_progress(
            "Updating user...",
            lambda: self.api_client.patch(endpoint=f"{USERS_ENDPOINT}{user_id}/", data=user_data)
            # lambda: self.api_client.put(endpoint=f"{USERS_ENDPOINT}{user_id}/", data=user_data)
        )
       
        return response
   
    def delete_user(self, user_id):
        """
        Delete an existing user by ID.
       
        Args:
            user_id (str): ID of the user to delete
           
        Returns:
            dict: Response data if successful, None otherwise
        """
        if not user_id:
            return None
           
        response = self._execute_with_progress(
            "Deleting user...",
            lambda: self.api_client.delete(endpoint=f"{USERS_ENDPOINT}{user_id}/")
        )
       
        return response
    
    @BaseManager.handle_api_error    
    def get_current_user(self):
        """
        Fetch current logged-in user information.
        
        Returns:
            dict: API response containing user data on success, None on failure
        """

        
        response = self._execute_with_progress(
            "Fetching User Information...",
            lambda: self.api_client.get(endpoint=USER_ME_ENDPOINT)
        )
        
        return response
        
    @BaseManager.handle_api_error
    def get_user_with_role_names(self):
        """
        Fetch current user information with role names instead of IDs.
        
        Returns:
            dict: User data with role_names field added, or None on failure
        """
        user_data = self.get_current_user()
        if not user_data:
            return None
        
        # Fetch roles data
        roles_data = self.view_roles()
        if roles_data:
            # Create a mapping of role ID to role name
            role_mapping = {role['id']: role['name'] for role in roles_data}
            
            # Add role names to user data
            user_role_ids = user_data.get('roles', [])
            role_names = []
            
            for role_id in user_role_ids:
                role_name = role_mapping.get(role_id, f"Unknown Role ({role_id})")
                role_names.append(role_name)
            
            # Add role names to user data
            user_data['role_names'] = role_names
            user_data['roles_with_names'] = [
                {'id': role_id, 'name': role_mapping.get(role_id, f"Unknown ({role_id})")} 
                for role_id in user_role_ids
            ]
        
        return user_data
    
    def is_demo_user(self) -> bool:
        """
        Check if the current logged-in user has DEMO role.
        
        Returns:
            bool: True if user has DEMO role, False otherwise.
        """
        try:
            user_data = self.get_user_with_role_names()
            if user_data and 'role_names' in user_data:
                role_names = user_data['role_names']
                # Check if 'DEMO' is in the role names (case-insensitive)
                return any(role.upper() == 'DEMO' for role in role_names)
            
            return False
            
        except Exception as e:
            # Log the error if you have logging set up
            # print(f"Error checking demo user status: {str(e)}")
            return False
        

def demo_user_check(func):

    """Decorator to check if user is demo user and prevent access to certain features."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = UserManager()
        if user.is_demo_user():
            console.print("[red]This feature is not available in the trial version[/red]")
            return None
        return func(*args, **kwargs)
    return wrapper
