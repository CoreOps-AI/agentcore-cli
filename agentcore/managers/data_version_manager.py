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
from agentcore.utils.config import DATAVERSION_ENDPOINT,DATA_VERSION_ENDPOINT, DATA_VERSION_PROCESSED_ENDPOINT,DATA_SOURCE_ENDPOINT,FETCH_DATA_MONGO_ENDPOINT
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
import mimetypes
from datetime import datetime
from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel
from agentcore.managers.client import APIError
from agentcore.utils.config import OPERATIONS_ENDPOINT

class DataversionManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.dataversion_details_columns = ["Id", "Data Source", "Created By", "Updated By", "Created At", "Updated At"]

    
    @BaseManager.handle_api_error
    def get_all_dataversions(self):
        """Fetch all data versions."""

        response = self._execute_with_progress(
            "Fetching all data versions...",
            lambda: self.api_client.get(endpoint=f"{DATA_VERSION_ENDPOINT}")
        )

        # Ensure the response is a list
        if not isinstance(response, list):
            raise ValueError("Unexpected response format: Expected a list of data versions.")

        return response
    
    
    @BaseManager.handle_api_error
    def data_fetch(self,dataversion_id):
        """
        Fetch data from MongoDB with Dataversion ID
        """

        response = self._execute_with_progress(
            "Fetching data........",
            lambda: self.api_client.get(endpoint=f"{FETCH_DATA_MONGO_ENDPOINT}{dataversion_id}/")
        )

        return response


from typing import Optional, Dict, List, Any
import json
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.utils.config import (
    DATA_VERSION_ENDPOINT,
    TASK_STATUS_ENDPOINT,
    PREVIEW_DATA_SOURCE_ENDPOINT,
    PREVIEW_DATA_VERSION_ENDPOINT,
    TRANSFORM_DATA_VERSION_ENDPOINT,
    FETCH_INITIAL_DATA_ENDPOINT,
    OPERATIONS_ENDPOINT,
    DIAGNOSE_DATA_VERSION_ENDPOINT,
    HISTORY_DATA_VERSION_ENDPOINT,
)

class DataVersionManager2(BaseManager):
    """
    Manager for data version operations including fetching, transforming, and diagnosing data.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.data_version_columns = ["ID", "Data Source Description", "Created By", "Created At", "Stage"]
    
    @BaseManager.handle_api_error
    def list_data_versions(self, data_source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available data versions, optionally filtered by data source.
        
        Args:
            data_source_id: Optional ID of the data source to filter versions by
            
        Returns:
            List of data version objects
        """
        endpoint = DATA_VERSION_ENDPOINT
        params = {}
        if data_source_id:
            params['data_source'] = data_source_id
        
        response = self._execute_with_progress(
            "Fetching data versions...",
            lambda: self.api_client.get(endpoint=endpoint, params=params)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def preview_data_source(self, data_source_id: str) -> Dict[str, Any]:
        """
        Preview data from a source without creating a version.
        
        Args:
            data_source_id: ID of the data source to preview
            
        Returns:
            Dictionary containing preview data, columns, and stats
        """
        # Updated to match the URL pattern with data_source_id as path parameter
        endpoint = f"{PREVIEW_DATA_SOURCE_ENDPOINT}{data_source_id}/"
        
        response = self._execute_with_progress(
            "Previewing data source...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def preview_data_version(self, version_id: str, limit: int = 10, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Preview data from an existing data version.
        
        Args:
            version_id: ID of the data version to preview
            limit: Maximum number of rows to preview (default: 10)
            columns: Optional list of columns to include in the preview
            
        Returns:
            Dictionary containing preview data, columns, and stats
        """
        # Updated to use the correct URL format with version_id
        endpoint = PREVIEW_DATA_VERSION_ENDPOINT.format(version_id=version_id)
        
        params = {'limit': limit}
        if columns:
            params['columns'] = ','.join(columns)
            
        response = self._execute_with_progress(
            "Previewing data version...",
            lambda: self.api_client.get(endpoint=endpoint, params=params)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def fetch_initial_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from a source and create an initial RAW data version.
        
        Args:
            payload: Dictionary containing:
                - data_source_id: ID of the data source
                - operations: List of operations to apply (optional)
                
        Returns:
            Dictionary with version_id, task_id, and status
        """
        response = self._execute_with_progress(
            "Initiating data fetch...",
            lambda: self.api_client.post(endpoint=FETCH_INITIAL_DATA_ENDPOINT, data=payload)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def transform_data_version(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform an existing data version by applying operations and create a new version.
        
        Args:
            payload: Dictionary containing:
                - source_version_id: ID of the source data version
                - operations: List of operations to apply
                
        Returns:
            Dictionary with source_version_id, target_version_id, task_id, and status
        """
        response = self._execute_with_progress(
            "Initiating data transformation...",
            lambda: self.api_client.post(endpoint=TRANSFORM_DATA_VERSION_ENDPOINT, data=payload)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def list_operations(self) -> List[Dict[str, Any]]:
        """
        Get available data transformation operations.
        
        Returns:
            List of operation objects with id, name, description, and parameters
        """
        response = self._execute_with_progress(
            "Fetching available operations...",
            lambda: self.api_client.get(endpoint=OPERATIONS_ENDPOINT)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def diagnose_data_version(self, version_id: str) -> Dict[str, Any]:
        """
        Diagnose data quality issues from an existing data version.
        
        Args:
            version_id: ID of the data version to diagnose
            
        Returns:
            Dictionary containing data quality metrics and recommendations
        """
        # Updated to use the correct URL format with version_id
        endpoint = DIAGNOSE_DATA_VERSION_ENDPOINT.format(version_id=version_id)
        
        response = self._execute_with_progress(
            "Diagnosing data quality...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of an async task.
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Dictionary with task status information
        """
        # Updated to use the correct task status endpoint
        endpoint = f"{TASK_STATUS_ENDPOINT}{task_id}/"
        
        response = self._execute_with_progress(
            "Checking task status...",
            lambda: self.api_client.get(endpoint=endpoint),
        )
        
        return response
    
    @BaseManager.handle_api_error
    def get_data_version(self, version_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific data version.
        
        Args:
            version_id: ID of the data version to retrieve
            
        Returns:
            Dictionary with data version details
        """
        endpoint = f"{DATA_VERSION_ENDPOINT}{version_id}/"
        
        response = self._execute_with_progress(
            "Fetching data version details...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def view_data_version_history(self, version_id: str) -> Dict[str, Any]:
        """
        Get the history of a specific data version.
        
        Args:
            version_id: ID of the data version to retrieve history for
            
        Returns:
            Dictionary with data version history
        """
        endpoint = f"{HISTORY_DATA_VERSION_ENDPOINT}.".format(version_id=version_id)
        
        response = self._execute_with_progress(
            "Fetching data version history...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error    
    def get_operations(self):
        """
        Fetch all available operations from the API.
        
        Returns:
            list: List of operations on success, None on failure
        """
        try:
            response = self._execute_with_progress(
                "Fetching operations...",
                lambda: self.api_client.get(endpoint=OPERATIONS_ENDPOINT)
            )
            
            if response:
                self.console.print(f"[green]✓ Successfully fetched {len(response)} operations[/green]")
                return response
            else:
                self.console.print("[red]No operations data received from server[/red]")
                return None

        except APIError as e:
            self.console.print(Panel(
                f"[red]API Error: {e.message}[/red]\n"
                f"Status Code: {e.status_code or 'N/A'}",
                title="Error"
            ))
            return None
        except Exception as e:
            self.console.print(f"[red]Unexpected error occurred: {str(e)}[/red]")
            return None
    