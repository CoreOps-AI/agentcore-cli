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
from agentcore.utils.config import AWS_CONFIG_CREDENTIALS

class ConfigManager2(BaseManager):
    def __init__(self):
        super().__init__()
        self.console = Console()

    @BaseManager.handle_api_error
    def post_aws_config_credentials(self, payload):
        endpoint = AWS_CONFIG_CREDENTIALS
        response = self._execute_with_progress(
        "Posting AWS credentials...",
        lambda: self.api_client.post(endpoint, payload)
        )

        return response
    
    @BaseManager.handle_api_error
    def get_aws_config_credentials(self):
        endpoint = AWS_CONFIG_CREDENTIALS
        response = self._execute_with_progress(
            "Fetching AWS credentials...",
            lambda: self.api_client.get(endpoint)
        )
        return response