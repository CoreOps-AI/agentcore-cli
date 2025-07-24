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
from agentcore.utils.config import (DEPLOY_CREATE_ENDPOINT,FETCH_DEPLOY_STATUS_ENDPOINT,FETCH_DEPLOYMENTS_ENDPOINT,FETCH_DEPLOYMENT_JOB_ID_ENDPOINT,
                                   DEPLOYMENT_PROMOTE_ENDPOINT,COMPARE_METRICS_DEPLOYMENT_ENDPOINT,DEPLOYMENT_STATUS_OVERRIDE_ENDPOINT)
from rich.prompt import Prompt
from rich.console import Console
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
import json
from datetime import datetime

class DeployManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.view_deployments_columns = ["ID", "Deploy Experiment RunID", "Experiment RunID", "User", "Is Test Passed", "Status"]
        self.details_deployment_columns = ["Step", "Status", "Message", "Timestamp"]
        self.details_compare_metric_columns = ["Artifact", "Metric", "Value", "Threshold", "Status", "Details"]


    @BaseManager.handle_api_error(show_details=True)
    def create_deploy(self, payload):
        """
        Create a Deployment.
        """
        response = self._execute_with_progress(
            "Deploying experiment...",
            lambda: self.api_client.post(endpoint=DEPLOY_CREATE_ENDPOINT, data=payload)
        )

        return response
    
    @BaseManager.handle_api_error
    def fetch_status(self, job_id):
        """
        Fetch deployment status.
        """
        endpoint = FETCH_DEPLOY_STATUS_ENDPOINT.format(job_id=job_id)
        response = self._execute_with_progress(
            "Fetching deployment status...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response
    
    @BaseManager.handle_api_error
    def view_deployments(self, project_id):
        """
        Fetch deployment status.
        """
        endpoint = FETCH_DEPLOYMENTS_ENDPOINT + f"?project={project_id}"
        response = self._execute_with_progress(
            "Fetching deployments...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def fetch_deployment_job_ids(self, project_id):
        """
        Fetch deployment job id's status.
        """
        endpoint = FETCH_DEPLOYMENT_JOB_ID_ENDPOINT + f"?status=success&project={project_id}"
        response = self._execute_with_progress(
            "Fetching deployment job id's...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def promote_production(self, payload):
        """
        Fetch deployment status.
        """
        endpoint = DEPLOYMENT_PROMOTE_ENDPOINT
        response = self._execute_with_progress(
            "Promoting to production...",
            lambda: self.api_client.post(endpoint=endpoint,data = payload)
        )

        return response
    
    @BaseManager.handle_api_error
    def metrics_compare(self, deployment_experiemnt_runid):
        """
        Fetch deployment status.
        """
        endpoint = COMPARE_METRICS_DEPLOYMENT_ENDPOINT.format(deployment_experiemnt_runid= deployment_experiemnt_runid)
        response = self._execute_with_progress(
            "Fetching compare metrics...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response

    @BaseManager.handle_api_error
    def override_status(self, experiment_job_id,payload):
        """
        Fetch deployment status.
        """
        endpoint = DEPLOYMENT_STATUS_OVERRIDE_ENDPOINT.format(experiment_job_id= experiment_job_id)
        response = self._execute_with_progress(
            "Overriding the status...",
            lambda: self.api_client.patch(endpoint=endpoint, data = payload)
        )

        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def promote_production_staus(self, promotion_id):
        """
        Fetch deployment status.
        """
        endpoint = DEPLOYMENT_PROMOTE_ENDPOINT + promotion_id
        response = self._execute_with_progress(
            "Fetching live status of production...",
            lambda: self.api_client.get(endpoint=endpoint)
        )

        return response