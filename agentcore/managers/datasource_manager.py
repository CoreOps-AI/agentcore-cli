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
from agentcore.utils.config import DATASOURCE_ENDPOINT,DATASOURCE_TYPES_ENDPOINT
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
from datetime import datetime

class DatasourceManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.datasource_columns = ["ID", "Source Type", "Description", "Created By", "Created At", "Data Source Type", "Project"]
        self.datasource_types_column = ["ID" ,"Description"]
        self.db_details_columns = ["Connection Url", "Db Type", "Port", "Host", "User Name", "Db Name", "Db Table"]



    @BaseManager.handle_api_error
    def view_datasources(self,datasource_id = None, project_id= None):
        """
        View datasources
        """

        endpoint = DATASOURCE_ENDPOINT
        if datasource_id :
            endpoint = endpoint + f"{datasource_id}/"
            response = self._execute_with_progress(
                "Fetching datasource's........",
                lambda: self.api_client.get(endpoint=endpoint)
            )
            return response
        
        #if project_id is provided , add it as a query parameter
        if project_id:
            #add ?project_id=xx or &project_id=xx depending on the endpoint
            if "?" in endpoint:
                endpoint = f"{endpoint}&project_id={project_id}"
            else:
                endpoint = f"{endpoint}?project_id={project_id}"

        response = self._execute_with_progress(
        "Fetching datasource's........",
        lambda: self.api_client.get(endpoint=endpoint)
        )
        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def create_datasource(self,payload):
        """
        Create datasource
        """

        response = self._execute_with_progress(
            "Fetching datasource's........",
            lambda: self.api_client.post(endpoint=DATASOURCE_ENDPOINT,data=payload)
        )

        return response
    
    @BaseManager.handle_api_error
    def datasource_types(self):
        """
        View datasource types
        """

        response = self._execute_with_progress(
            "Fetching datasource's........",
            lambda: self.api_client.get(endpoint=DATASOURCE_TYPES_ENDPOINT,)
        )

        return response
    


    @BaseManager.handle_api_error(show_details=True)
    def create_datasource_with_file(self, payload, file_path, file_name=None):
        """
        Create a datasource with file upload
        """
        import os
        
        if not file_name:
            file_name = os.path.basename(file_path)
        
        try:
            # Prepare the files for upload
            with open(file_path, 'rb') as file:
                files = {
                    'files': (file_name, file, 'application/octet-stream')
                }
                
                # Debug: Print what we're sending
                self.console.print(f"[dim]Uploading with payload: {payload}[/dim]")
                self.console.print(f"[dim]File: {file_name}[/dim]")
                
                # Use the existing API client's post method with file support
                response = self._execute_with_progress(
                    f"Uploading file '{file_name}' and creating datasource...",
                    lambda: self.api_client.post(
                        endpoint=DATASOURCE_ENDPOINT,
                        data=payload,  # Form data
                        files=files    # File upload
                    )
                )
                
            if response:
                self.console.print(f"[green]✅ File uploaded successfully: {file_name}[/green]")
                return response
            else:
                self.console.print(f"[red]❌ Failed to create datasource with file upload[/red]")
                return None
                
        except FileNotFoundError:
            self.console.print(f"[red]❌ File not found: {file_path}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]❌ Error uploading file: {str(e)}[/red]")
            return None