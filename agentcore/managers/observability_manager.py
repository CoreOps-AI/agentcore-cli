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

from .base import BaseManager
from rich.console import Console
from typing import Dict, List, Any, Optional
import os
import requests
from agentcore.managers.table_manager import TableDisplay
import time
import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.traceback import install
from functools import wraps
import json
from agentcore.managers.base import BaseManager, ConfigurationError
from agentcore.managers.client import APIError
from agentcore.utils.config import OPERATION_METRICS_ENDPOINT, OBSERVABILITY_METRICS_ENDPOINT, DEPLOYMENT_LISTING_ENDPOINT


class ObservabilityManager(BaseManager):
    """
    Class to manage all metrics-related operations.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
    
    @BaseManager.handle_api_error    
    def get_operation_metrics(self, model_id: str):
        """
        Fetch operation metrics for a specific production model.
        
        Args:
            model_id (str): The model ID for the production model
            
        Returns:
            dict: API response containing metrics data on success, None on failure
        """
        
        # Construct the endpoint with model_id
        endpoint = f"{OPERATION_METRICS_ENDPOINT}/{model_id}"

        try:
            response = self._execute_with_progress(
                "Fetching Production Model Metrics...",
                lambda: self.api_client.get(endpoint=endpoint)
            )
            
            if response:
                self.console.print("[bold green]✓ Production metrics fetched successfully![/bold green]")
                return response
            else:
                self.console.print("[bold red]Failed to fetch metrics: No data received[/bold red]")
                return None

        except APIError as e:
            self.console.print(Panel(
                f"[red]API Error: {e.message}[/red]\n"
                f"Status Code: {e.status_code or 'N/A'}",
                title="Error"
            ))
            return None
          
        except Exception as e:
            self.console.print(Panel(
                f"[red]Unexpected Error: {str(e)}[/red]",
                title="Error"
            ))
            return None

        
    def performance_metrics(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a given experiment.
        """
        endpoint = f"api/monitoring/regression/?experiment_id={experiment_id}"
        try:
            response = self._execute_with_progress(
                "Fetching Performance Metrics...",
                lambda: self.api_client.get(endpoint=endpoint)
            )
            if response:
                return response
            else:
                self.console.print(f"Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            self.console.print(f"Error: {e}")

            return None
        
    def get_new_metrics(self, experiment_id: str):
        """
        Fetch new metrics for a specific experiment.
        
        Args:
            experiment_id (str): The ID of the experiment
            
        Returns:
            dict: API response containing new metrics data on success, None on failure
        """
        
        # Construct the endpoint with experiment_id
        endpoint = f"{OBSERVABILITY_METRICS_ENDPOINT}/{experiment_id}"
        response = self._execute_with_progress(
            "Fetching Metrics...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response if response else None
    

    def get_listing(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch the listing of deployments for a given project.
        
        Args:
            project_id (str): The ID of the project
            
        Returns:
            List[Dict[str, Any]]: List of deployment details on success, None on failure
        """
        
        endpoint = f"{DEPLOYMENT_LISTING_ENDPOINT}/{project_id}/"
        print(endpoint)
        reponse = self._execute_with_progress(
            "Fetching Deployment Listing...",
            lambda: self.api_client.get(endpoint=endpoint)
        )  
        return reponse if reponse else None