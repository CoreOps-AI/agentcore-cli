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

from typing import Optional
import urllib
from agentcore.utils.config import PROJECTS_ENDPOINT,PROJECT_TYPES_ENDPOINT,PROJECT_ARCHIVE_ENDPOINT, PROJECT_METRICS_GET, PROJECT_METRICS_POST, METRIC_DEFINITIONS_ENDPOINT,PROJECT_DETAILS_ENDPOINT
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
from datetime import datetime

class ProjectManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.columns = [
            "ID", "Name", "Status", "Start", "Finish", 
            "Description", "Users", "User Count","Project Type","Is Archived"
        ]
        self.project_types_columns = ["ID", "Type Name", "Description"]
        self.metrics_columns = [
            "ID", "Metrics Name", "Threshold Value", "Description", "Created At", "Updated At"]


    @BaseManager.handle_api_error(show_details=True)
    def create_project(self, project_data):
        """
        Create a new project.
        """
        response = self._execute_with_progress(
            "Creating project...",
            lambda: self.api_client.post(endpoint=PROJECTS_ENDPOINT, data=project_data)
        )

        return response

    @BaseManager.handle_api_error
    def get_project_github_url(self, project_id: int) -> str:
        """Get the current GitHub URL for a project."""
        try:
            # You might need to adjust this endpoint based on your existing API
            # This assumes you have a GET endpoint to fetch project details
            endpoint = f"/api/projects/{project_id}/"
            
            response = self._execute_with_progress(
                "Fetching project details...",
                lambda: self.api_client.get(endpoint=endpoint, verify=False)
            )
            
            if response and isinstance(response, dict):
                return response.get('github_url', '')
            
            return ''
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not fetch existing GitHub URL: {str(e)}[/yellow]")
            return ''

    @BaseManager.handle_api_error
    def set_project_details(
        self,
        project_id: int,
        github_repo: str,
        operation: str = "create"
    ) -> bool:
        """Set or update GitHub repository URL for a project."""
        try:
            # Use the new endpoint for GitHub URL updates
            endpoint = PROJECT_DETAILS_ENDPOINT

            # # Debug: Print input parameters
            # self.console.print("\n[yellow]Input Parameters:[/yellow]")
            # self.console.print(f"Project ID: {project_id}")
            # self.console.print(f"GitHub Repository URL: {github_repo}")
            # self.console.print(f"Operation: {operation}")
        
            # Prepare the data with the new format
            data = {
                "project_id": project_id,
                "github_repo_url": github_repo,
            }

            # # Debug: Print request details
            # self.console.print(f"\n[yellow]API Endpoint: {endpoint}[/yellow]")
            # self.console.print(f"[yellow]HTTP Method: {'POST' if operation == 'create' else 'PUT'}[/yellow]")

            # Choose the appropriate HTTP method based on operation
            if operation == "create":
                # Use POST for creating new GitHub URL
                response = self._execute_with_progress(
                    "Creating GitHub repository URL...",
                    lambda: self.api_client.post(endpoint=endpoint, data=data, verify=False)
                )
            else:
                # Use PUT for updating existing GitHub URL
                response = self._execute_with_progress(
                    "Updating GitHub repository URL...",
                    lambda: self.api_client.put(endpoint=endpoint, data=data, verify=False)
                )
        
            # Handle response
            if response == -1:
                self.console.print("[red]Failed to set project details: Maximum retry attempts reached[/red]")
                return False

            if not response:
                self.console.print("[red]Empty response received from server[/red]")
                return False

            # Check if we got a valid response
            if response and response.get('data'):
                self.console.print(f"[green]{response.get('message', 'Operation completed successfully!')}[/green]")
                
                # Show additional details if available
                data = response.get('data', {})
                if data.get('project_id'):
                    self.console.print(f"[green]Project: {data.get('name', 'N/A')}[/green]")
                    self.console.print(f"[green]Updated at: {data.get('updated_at', 'N/A')}[/green]")
                
                # Show old URL if this was an update operation
                if operation == "update" and response.get('old_url'):
                    self.console.print(f"[yellow]Previous URL: {response.get('old_url')}[/yellow]")
                
                return True
            else:
                self.console.print("[red]Failed to set project details: Invalid response from server[/red]")
                
                # Show error details if available
                if response.get('error'):
                    self.console.print(f"[red]Error: {response.get('error')}[/red]")
                
                if response.get('details'):
                    self.console.print(f"[red]Details: {response.get('details')}[/red]")
                
                return False

        except Exception as e:
            self.console.print(f"[red]Failed to set project details: {str(e)}[/red]")
            return False
    # @BaseManager.handle_api_error
    # def view_projects(self, url=PROJECTS_ENDPOINT):
    #     """
    #     Fetch a page of projects from the API.

    #     Args:
    #         url (str): The endpoint to fetch from.

    #     Returns:
    #         dict or list: Project data from the API
    #     """
    #     if url is None:
    #         endpoint = PROJECTS_ENDPOINT
    #     else:
    #         # Extract the endpoint portion from the full URL
    #         # This assumes urls are in the format http://server/api/projects/?page=2
    #         from urllib.parse import urlparse
    #         parsed_url = urlparse(url)
    #         endpoint = parsed_url.path
    #         if parsed_url.query:
    #             endpoint += f"?{parsed_url.query}"
        
    #     response = self._execute_with_progress(
    #         f"Fetching project details...",
    #         lambda: self.api_client.get(endpoint=endpoint)
    #     )

    #     return response

    @BaseManager.handle_api_error
    def view_projects(self):
        """
        Fetch a page of projects from the API.

        Args:
            url (str): The endpoint to fetch from.

        Returns:
            dict or list: Project data from the API
        """
        
        
        response = self._execute_with_progress(
            f"Fetching project details...",
            lambda: self.api_client.get(endpoint=PROJECTS_ENDPOINT)
        )

        return response 

    @BaseManager.handle_api_error
    def update_project(self, project_id, updated_data):
        """
        Update an existing project by its ID.

        Args:
            project_id (str): The project ID to update.
            updated_data (dict): The updated project details.

        Returns:
            dict or None: Updated project details if successful, otherwise None.
        """
        response = self._execute_with_progress(
            f"Updating project {project_id}...",
            lambda: self.api_client.patch(endpoint=f"{PROJECTS_ENDPOINT}{project_id}/", data=updated_data)
        )

        return response

    @BaseManager.handle_api_error
    def fetch_project(self, project_id):
        """
        Fetch project details by its ID.
        """
        response = self._execute_with_progress(
            f"Fetching project {project_id} details...",
            lambda: self.api_client.get(endpoint=f"{PROJECTS_ENDPOINT}{project_id}/")
        )

        return response
    
    @BaseManager.handle_api_error
    def users_assign(self, project_id,payload):
        """
        Assigns users to the project after enter respective ID's
        """

        assign_details = self._execute_with_progress(
            f"Assigning and removing users to project {project_id}...",
            lambda: self.api_client.patch(endpoint=f"{PROJECTS_ENDPOINT}assign/",data=payload)
        )
        
        return assign_details
    
    @BaseManager.handle_api_error
    def project_types(self):
        """
        Fetch Project types
        """

        response = self._execute_with_progress(
            f"Fetching Project types...",
            lambda: self.api_client.get(endpoint=PROJECT_TYPES_ENDPOINT)
        )
        
        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def project_archive(self,project_id,payload):
        """
        Fetch Project types
        """
        if payload['is_archived']:
            message = "Archiving"
        else:
            message = "Unarchiving"
        endpoint = PROJECT_ARCHIVE_ENDPOINT.format(project_id = project_id)
        response = self._execute_with_progress(
            f"{message} project...",
            lambda: self.api_client.post(endpoint=endpoint,data= payload)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def project_metrics(self, project_id):
        """
        Fetch Project metrics
        """
        endpoint = PROJECT_METRICS_GET.format(project_id=project_id)
        response = self._execute_with_progress(
            f"Fetching project metrics for project {project_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    def post_project_metrics(self ,payload):
        """
        Post Project metrics
        """
    
        response = self._execute_with_progress(
            f"Posting project metrics...",
            lambda: self.api_client.post(endpoint=PROJECT_METRICS_POST, data=payload)
        )
        return response

    def fetch_metric_definitions(self):
        """
        Fetch metric definitions.
        """
        response = self._execute_with_progress(
            "Fetching metric definitions...",
            lambda: self.api_client.get(endpoint=METRIC_DEFINITIONS_ENDPOINT)
        )

        return response
    
    def delete_project_metrics(self, project_id, id):
        """
        Delete project metrics by project_id and metric id.
        """
        endpoint = f"{PROJECT_METRICS_POST}?project_id={project_id}&id={id}"
        response = self._execute_with_progress(
            "Deleting project metrics...",
            lambda: self.api_client.delete(endpoint=endpoint)
        )
        return response

    
    def update_project_metrics(self ,payload):
        """
        Update Project metrics
        """
    
        response = self._execute_with_progress(
            f"Updating project metrics...",
            lambda: self.api_client.patch(endpoint=PROJECT_METRICS_POST, data=payload)
        )
        return response
