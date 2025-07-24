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
from agentcore.utils.config import DATA_ENDPOINT
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
import mimetypes
from datetime import datetime
from rich.prompt import Prompt
from rich.console import Console

class DataManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.columns = []

    @BaseManager.handle_api_error
    def upload_data_files(self, name, file_path):
        """Upload file to server."""

        endpoint = DATA_ENDPOINT + "files/save-file/"

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default to binary if unknown

        with open(file_path, "rb") as file:
            files = {"file": (file.name, file, mime_type)}  # Ensure correct format
            data_payload = {"name": name}  

            response = self._execute_with_progress(
                "Uploading file...",
                lambda: self.api_client.post(endpoint, data=data_payload, files=files)
            )

        file_id = response.get("id")
        if not file_id:
            raise ValueError("Failed to retrieve file ID from response.")
        
        upload_endpoint = DATA_ENDPOINT + f"files/upload-to-azure/{file_id}/"

        upload_response = self._execute_with_progress(
            "Uploading data to Azure...",
            lambda: self.api_client.post(upload_endpoint)
        )

        return upload_response
    
    @BaseManager.handle_api_error
    def upload_data_source(self, payload):
        """Upload file to server."""

        endpoint = DATA_ENDPOINT + "datasources/add/"

        response = self._execute_with_progress(
            "Uploading datasource creds...",
            lambda: self.api_client.post(endpoint, data=payload)
        )

        data_id = response.get("data", {}).get("id")
        if not data_id:
            raise ValueError("Failed to retrieve file ID from response.")
        
        upload_endpoint = DATA_ENDPOINT + f"datasources/{data_id}/export-csv/"

        upload_response = self._execute_with_progress(
            "Uploading data to Azure...",
            lambda: self.api_client.get(upload_endpoint)
        )

        return upload_response




        