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
from agentcore.utils.config import OPERATIONS_FE_ENDPOINT
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
from datetime import datetime

class DatapipelineManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.list_columns = ["ID", "File Type", "Description", "File Path Source", "User Visible", "Created By", "Updated By", "Created At", "Updated At"]

    
    @BaseManager.handle_api_error
    def operations_fe(self,payload):
        """Operations on RAW data"""

        response = self._execute_with_progress(
            "Running operations...",
            lambda: self.api_client.post(OPERATIONS_FE_ENDPOINT,data=payload)
        )

        return response

