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
from agentcore.utils.config import (AWS_INSTANCE_ENDPOINT, AWS_PRICING_ENDPOINT,AWS_INSTANCE_TYPES_ENDPOINT,AWS_REGIONS_ENDPOINT,
                                    PROJECT_INSTANCE_VIEW,INSTANCE_STATUS, INSTANCE_UPDATE, AWS_CREDENTIALS_ENDPOINT)
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from rich.panel import Panel
import json
from datetime import datetime
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.client import APIError
from agentcore.utils.config import OS_TYPES_ENDPOINT

class InstanceManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.columns = [
            "ID", "Name", "Project ID", "Stage", "State", "IP Address", 
            "Instance Type", "Provider Type"
        ]

        self.project_instance_columns = [
            "ID", "Name", "Stage", "State", "Instance Type", "IP Address", 
            "CPU Count", "Memory Size", "Created At", "Updated At", "Destroyed At", "Running Since", "Stopped At",
            "AWS Region", "OS Type"
        ]

        
        

    @BaseManager.handle_api_error
    def get_aws_credentials_by_project(self, project_id):
        """Fetch AWS credentials for a specific project."""
        
        if not project_id:
            self.console.print("[red]Error: Project ID is required.[/red]")
            return None

        endpoint = f"{AWS_CREDENTIALS_ENDPOINT}?project_id={project_id}"
        
        try:
            response = self._execute_with_progress(
                "Fetching AWS credentials...",
                lambda: self.api_client.get(endpoint)
            )
            
            if not response:
                self.console.print(f"[red]No AWS credentials found for project ID: {project_id}[/red]")
                return None
            
            # The response should be a list of credentials
            if isinstance(response, list) and len(response) > 0:
                return response
            else:
                self.console.print(f"[yellow]No AWS credentials available for project ID: {project_id}[/yellow]")
                return None
            
        except Exception as e:
            self.console.print(f"[red]Error fetching AWS credentials: {str(e)}[/red]")
            return None

    @BaseManager.handle_api_error(show_details=True)
    def instance_create(self, instance_data):
        "Create an instance for a project."
    
        response = self._execute_with_progress(
            "Creating Instance...",
            lambda: self.api_client.post(endpoint=AWS_INSTANCE_ENDPOINT , data=instance_data)
        )

        return response
    
    @BaseManager.handle_api_error
    def instance_start(self, instance_id, action):
        "Start an instance for a project."

        data = {
            "action": action
        }

        response = self._execute_with_progress(
            "Starting Instance..." if action == "start" else "Stopping Instance...",
            lambda: self.api_client.post(endpoint=AWS_INSTANCE_ENDPOINT + f"{instance_id}/action/", data=data)
        )

        return response


    @BaseManager.handle_api_error
    def instance_show(self, instance_id):
        "Create an instance for a project."

        # AWS_INSTANCE_ENDPOINT = "https://127.0.0.1:8000/api/aws/instances/"
        endpoint=AWS_INSTANCE_ENDPOINT + f"{instance_id}/"
        # print(endpoint)
        response = self._execute_with_progress(
            "Fetching Instance...",
            lambda: self.api_client.get(endpoint)
        )

        if response:
            action = response.get("action")
            status = response.get("status")
            if action:
                self.console.print(f"[green]Instance action: {action}[/green]")
            elif status == "failure":
                self.console.print(f"[red]Instance action failed![/red]")
                

            return response

        return None
    
    @BaseManager.handle_api_error
    def project_instance_show(self, project_id):
        "Show all the instances associated with project."

        # AWS_INSTANCE_ENDPOINT = "https://127.0.0.1:8000/api/aws/instances/"
        endpoint= PROJECT_INSTANCE_VIEW + f"{project_id}/"
        response = self._execute_with_progress(
            "Fetching Instance...",
            lambda: self.api_client.get(endpoint)
        )

        if response:
            action = response.get("action")
            status = response.get("status")
            if action:
                self.console.print(f"[green]Instance action: {action}[/green]")
            elif status == "failure":
                self.console.print(f"[red]Instance action failed![/red]")
                

            return response

        return None
    
    @BaseManager.handle_api_error
    def pricing(self, provider, instance_type, region):
        """Fetch cloud pricing for the given provider, instance type, and region."""

        if not provider or not instance_type or not region:
            self.console.print("[red]Error: Missing required parameters.[/red]")
            return None

        endpoint = AWS_PRICING_ENDPOINT + f"?provider={provider}&instance_type={instance_type}&region={region}"

        data = self._execute_with_progress(
                "Fetching pricing data...",
                lambda: self.api_client.get(endpoint)
            )
        return data


    @BaseManager.handle_api_error
    def regions_aws(self):
        """Fetch AWS instance regions."""

        endpoint = AWS_REGIONS_ENDPOINT
        response = self._execute_with_progress(
            "Getting Regions...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response


    @BaseManager.handle_api_error
    def instance_type_aws(self, region):
        """Fetch AWS instance types of a region."""

        if not region:
            return None  

        endpoint = AWS_INSTANCE_TYPES_ENDPOINT + "?region=" + region
        response = self._execute_with_progress(
            "Getting Instance types...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        if not response or "instance_types" not in response:
            return None
        
        return response

        # try:
            
        
        # except Exception as e:
        #     # self.console.print(f"[red]Error: Failed to fetch instance types for region '{region}'.[/red]")
        #     self.console.print(f"[red]API Response: {str(e)}[/red]")
        #     return None
        

    @BaseManager.handle_api_error
    def get_os_types(self):
        """Fetch available OS types from API."""
        response = self._execute_with_progress(
            "Fetching OS types...",
            lambda: self.api_client.get(endpoint=OS_TYPES_ENDPOINT)
        )
        return response if response else []

    
    @BaseManager.handle_api_error
    def instance_status(self,task_id):
        "Fetches the status of an instance"

        endpoint = INSTANCE_STATUS + task_id + "/"
        response = self._execute_with_progress(
            "Fetching status of instance", lambda: self.api_client.get(endpoint)
        )
        return response
    
    @BaseManager.handle_api_error
    def instance_update(self,payload):
        "Update an instance"

        response = self._execute_with_progress(
            "Updating the instance...", lambda: self.api_client.post(INSTANCE_UPDATE, payload)
        )
        return response