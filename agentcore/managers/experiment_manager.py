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
import urllib.parse
import time
from typing import Dict, Any, Optional, Generator
from rich.panel import Panel

from agentcore.utils.config import (
    DATA_VERSIONS_ENDPOINT,
    FETCH_COLUMNS_ENDPOINT,
    MODEL_HYPERPARAMETERS_ENDPOINT,
    MODEL_TYPES_ENDPOINT,
    RUN_EXPERIMENT_ENDPOINT,
    METRICS_POST,
    ARTIFACTS_ENDPOINT,
    ARTIFACT_DOWNLOAD_ENDPOINT,
    METRICS_GET,
    EXPERIMENT_STATUS,
    ALL_MODEL_TYPES_ENDPOINT,
    EXPERIMENT_FETCH,
    EXPERIMENT_FETCH,
    ALL_MODEL_TYPES_ENDPOINT,
    EXPERIMENT_FETCH,
    ALL_MODEL_TYPES_ENDPOINT,
    FETCH_LOGS_ENDPOINT,
    PROMOTE_ENDPOINT,
    RERUN_EXPERIMENT_ENDPOINT,
    GITPUSH_EXPERIMENT_ENDPOINT,
)




class ExperimentManager(BaseManager):
    """
    Manager for experiment operations including data versions, columns, models, and hyperparameters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.model_hyperparameter_columns = ["ID", "Name", "Description", "Type"]
        self.all_model_types_columns = ["ID", "Model Name", "Description"]
        self.experiments_columns = ["Experiment Group Code", "Version", "Data Version", "Data Source", "Instance ID", "Model", "Executed By", "Created At", "Status"]
    
    @BaseManager.handle_api_error
    def list_data_versions(self, project_id: int) -> List[Dict[str, Any]]:
        """
        List available data versions for a specific project.
        
        Args:
            project_id: ID of the project to fetch data versions for
            
        Returns:
            List of data version objects
        """
        endpoint = DATA_VERSIONS_ENDPOINT.format(project_id=project_id)
        response = self._execute_with_progress(
            description="Fetching data versions...",
            operation=lambda: self.api_client.get(endpoint=endpoint),
        )
        return response
    
    @BaseManager.handle_api_error
    def fetch_columns(self, data_source_id: int) -> Dict[str, Any]:
        """
        Fetch available columns for a data source.
        
        Args:
            data_source_id: ID of the data source
            
        Returns:
            Dictionary containing columns and table name
        """
        endpoint = FETCH_COLUMNS_ENDPOINT.format(data_source_id=data_source_id)
        
        response = self._execute_with_progress(
            f"Fetching columns for data source {data_source_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def get_model_hyperparameters(self, model_type_id: int) -> List[Dict[str, Any]]:
        """
        Get available hyperparameters for a specific model type.
        
        Args:
            model_type_id: ID of the model type
            
        Returns:
            List of hyperparameter objects
        """
        endpoint = MODEL_HYPERPARAMETERS_ENDPOINT.format(model_type_id=model_type_id)
        
        response = self._execute_with_progress(
            f"Fetching hyperparameters for model type {model_type_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def get_model_types(self, project_type_id: int) -> List[Dict[str, Any]]:
        """
        Get available model types for a specific project type.
        
        Args:
            project_type_id: ID of the project type
            
        Returns:
            List of model type objects
        """
        endpoint = MODEL_TYPES_ENDPOINT.format(project_type_id=project_type_id)
        
        response = self._execute_with_progress(
            f"Fetching model types for project type {project_type_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error
    def run_experiment(self, payload):
        """
        Run an experiment with the provided payload.
        
        Args:
            payload: Dictionary containing experiment parameters
            
        Returns:
            Response from the API
        """
        endpoint = RUN_EXPERIMENT_ENDPOINT
        response = self._execute_with_progress(
            f"Running experiment...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response
    
   
    
    def post_metrics(self, payload):
        """
        Post metrics for a specific experiment.
        
        Args:
            payload: Dictionary containing metrics data
            
        Returns:
            Response from the API
        """
        endpoint = METRICS_POST
        response = self._execute_with_progress(
            f"Posting metrics...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response
    

    def get_experiment_artifact_list(self, instance_id: int, experiment_id: str) -> Dict[str, Any]:
        """
        Get the list of artifacts for a specific experiment.
        
        Args:
            instance_id: ID of the instance (integer)
            experiment_id: ID of the experiment (UUID string)
                
        Returns:
            Dictionary with 'success' and 'files' keys
        """
        endpoint = ARTIFACTS_ENDPOINT.format(
            instance_id=instance_id,
            experiment_id=experiment_id
        )
        
        response = self._execute_with_progress(
            f"Fetching artifacts for experiment {experiment_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    
    def download_experiment_artifact(self, instance_id: int, experiment_id: str, filename: str, save_path: str = None) -> bool:
        """
        Download a specific artifact file from an experiment and open images automatically.
        
        Args:
            instance_id: ID of the instance
            experiment_id: ID of the experiment (UUID string)
            filename: Name of the artifact file to download
            save_path: Optional path where to save the file. If None, saves to current directory.
                
        Returns:
            True if download was successful, False otherwise
        """
        endpoint = ARTIFACT_DOWNLOAD_ENDPOINT.format(
            instance_id=instance_id,
            experiment_id=experiment_id,
            filename=urllib.parse.quote(filename)  # URL encode the filename to handle special characters
        )
        
        # Determine where to save the file
        if save_path is None:
            save_path = os.path.join(os.getcwd(), filename)
        elif os.path.isdir(save_path):
            save_path = os.path.join(save_path, filename)
        
        console = Console()
        try:
            # Use the api_client to get the file
            console.print(f"Downloading {filename}...")
            
            # Use requests directly to stream the file
            response = self.api_client.session.get(
                url=f"{self.api_client.base_url}{endpoint}",
                stream=True
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Write the file in chunks
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Check if it's an image file and open it with cv2
            _, ext = os.path.splitext(filename.lower())
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
            
            if ext in image_extensions:
                try:
                    import cv2
                    
                    # Open the image with OpenCV
                    image = cv2.imread(save_path)
                    
                    if image is not None:
                        # Get image dimensions
                        height, width = image.shape[:2]
                        
                        # Resize image if it's too large (keeping aspect ratio)
                        max_dimension = 1000
                        if height > max_dimension or width > max_dimension:
                            scale = min(max_dimension / width, max_dimension / height)
                            new_width = int(width * scale)
                            new_height = int(height * scale)
                            image = cv2.resize(image, (new_width, new_height))
                        
                        # Create a window with a name
                        window_name = f"Image: {filename}"
                        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                        
                        # Show the image
                        cv2.imshow(window_name, image)
                        
                        console.print(f"[bold green]Image opened with OpenCV. Press any key in the image window to close it.[/bold green]")
                        
                        # Wait for a key press to close the window
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    else:
                        console.print(f"[yellow]Could not open image with OpenCV. The file may be corrupt or in an unsupported format.[/yellow]")
                except ImportError:
                    console.print(f"[yellow]OpenCV (cv2) not installed. Cannot display image.[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]Error opening image with OpenCV: {str(e)}[/yellow]")
            
            console.print(f"[bold green]File successfully downloaded to: {save_path}[/bold green]")
            return True
                
        except Exception as e:
            console.print(f"[red]Error downloading file: {str(e)}[/red]")
            return False
        

    def get_metrics(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get metrics for a specific experiment.
        
        Args:
            experiment_id: ID of the experiment (UUID string)
                
        Returns:
            Dictionary with metrics data
        """
        endpoint = METRICS_GET.format(experiment_id=experiment_id)
    
        response = self._execute_with_progress(
            f"Fetching metrics for experiment {experiment_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        
        return response
    
    def post_metrics(self, payload):
        """
        Post metrics for a specific experiment.
        
        Args:
            payload: Dictionary containing metrics data
            
        Returns:
            Response from the API
        """
        endpoint = METRICS_POST
        response = self._execute_with_progress(
            f"Posting metrics...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response
    
    def experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific experiment.
        
        Args:
            experiment_id: ID of the experiment (UUID string)
                
        Returns:
            Dictionary with experiment status
        """
        endpoint = EXPERIMENT_STATUS.format(experiment_id=experiment_id)
        payload = {"status": "Ready for Promotion"}
        
        response = self._execute_with_progress(
            f"Fetching status for experiment {experiment_id}...",
            lambda: self.api_client.patch(endpoint=endpoint, data= payload)
        )
        
        return response
    
    def all_model_types(self,model_id=None):
        """
        Get all available model types.
        
        Returns:
            List of all model type objects
        """
        endpoint = ALL_MODEL_TYPES_ENDPOINT
        if model_id:
            endpoint = ALL_MODEL_TYPES_ENDPOINT + f"{model_id}/"

        response = self._execute_with_progress(
            f"Fetching all model types...",
            lambda: self.api_client.get(endpoint)
        )
        
        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def fetch_experiments(self, project_id: str) -> Dict[str, Any]:
        """
        Fetch details of a specific experiment.
        
        Args:
            experiment_id: ID of the experiment (UUID string)
                
        Returns:
            Dictionary with experiment details
        """
        payload = {"project_id": project_id}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching experiments for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def display_experiment_info(self, project_id: int) -> Dict[str, Any]:
        """
        Display experiment information for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with experiment information
        """
        payload = {"project_id": project_id, "config": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching experiment information for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def display_plots(self, project_id: int) -> Dict[str, Any]:
        """
        Display experiment information for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with experiment information
        """
        payload = {"project_id": project_id, "images": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching experiment information for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Fetch metrics for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with metrics data
        """
        payload = {"project_id": project_id, "artifacts": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching metrics for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
        
        
    def all_model_types(self,model_id=None):
        """
        Get all available model types.
        
        Returns:
            List of all model type objects
        """
        endpoint = ALL_MODEL_TYPES_ENDPOINT
        if model_id:
            endpoint = ALL_MODEL_TYPES_ENDPOINT + f"{model_id}/"

        response = self._execute_with_progress(
            f"Fetching all model types...",
            lambda: self.api_client.get(endpoint)
        )
        
        return response
    

    # def fetch_experiments(self, project_id: str) -> Dict[str, Any]:
    #     """
    #     Fetch details of a specific experiment.
        
    #     Args:
    #         experiment_id: ID of the experiment (UUID string)
                
    #     Returns:
    #         Dictionary with experiment details
    #     """
    #     payload = {"project_id": project_id}
    #     endpoint = EXPERIMENT_FETCH
    #     print(endpoint, payload)
    #     response = self._execute_with_progress(
    #         f"Fetching experiments for project {project_id}...",
    #         lambda: self.api_client.post(endpoint=endpoint, data=payload)
    #     )
    #     return response
    
    def display_experiment_info(self, project_id: int) -> Dict[str, Any]:
        """
        Display experiment information for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with experiment information
        """
        payload = {"project_id": project_id, "config": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching experiment information for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def display_plots(self, project_id: int) -> Dict[str, Any]:
        """
        Display experiment information for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with experiment information
        """
        payload = {"project_id": project_id, "images": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching experiment information for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Fetch metrics for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with metrics data
        """
        payload = {"project_id": project_id, "artifacts": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching metrics for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
    
    def fetch_logs(self, project_id: int, experiment_group_code: str, version: str) -> Dict[str, Any]:
        """
        Fetch logs for a specific experiment group and version.
        
        Args:
            project_id: ID of the project
            experiment_group_code: Code of the experiment group
            version: Version number
            
        Returns:
            Dictionary with logs data
        """
        endpoint = FETCH_LOGS_ENDPOINT.format(
            project_id=project_id,
            experiment_group_code=experiment_group_code,
            version=version
        )
        
        try:
            response = self._execute_with_progress(
                f"Fetching logs for project {project_id}, group {experiment_group_code}, version {version}...\n[yellow]Press Ctrl+C to stop...[/yellow]",
                lambda: self.api_client.get(endpoint=endpoint)
            )
            return response
        except Exception as e:
            # Log and re-raise the error for better debugging
            print(f"Error fetching logs: {str(e)}")
            raise

    def poll_experiment_logs(self, project_id: int, experiment_group_code: str, version: str, 
                             poll_interval: int = 5, max_polls: int = 120) -> Generator[str, None, None]:
        """
        Poll experiment logs continuously until completion or timeout.
        
        Args:
            project_id: ID of the project
            experiment_group_code: Code of the experiment group
            version: Version number
            poll_interval: Seconds between polls (default: 5)
            max_polls: Maximum number of polls before timeout (default: 120 = 10 minutes)
            
        Yields:
            Log content as string
        """
        polls_count = 0
        last_log_content = ""
        
        # Completion indicators for experiment status
        completion_indicators = [
            '✅ model execution complete',
            'experiment completed',
            'pipeline finished',
            'error:',
            'failed'
        ]
        
        while polls_count < max_polls:
            try:
                # Fetch the current logs
                response = self.fetch_logs(project_id, experiment_group_code, version)
                current_log = response.get('log', '')
                
                # Only yield new content if it has changed
                if current_log != last_log_content:
                    yield current_log
                    last_log_content = current_log
                
                # Check for completion indicators
                if any(indicator in current_log.lower() for indicator in completion_indicators):
                    yield "Experiment logs indicate completion or an error. Stopping polling."
                    break
                
                # Increment poll count and wait before the next poll
                polls_count += 1
                time.sleep(poll_interval)
            
            except Exception as e:
                # Handle any exceptions during polling
                yield f"Error fetching logs: {str(e)}"
                break
        
        # Handle polling timeout
        if polls_count >= max_polls:
            yield "Polling timeout reached. Use 'experiments logs' command to check the current status."
        
    def system_metrics(self, project_id: int) -> Dict[str, Any]:
        """
        Fetch system metrics for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with system metrics data
        """
        payload = {"project_id": project_id, "system_metrics": True}
        endpoint = EXPERIMENT_FETCH
        response = self._execute_with_progress(
            f"Fetching system metrics for project {project_id}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        return response
 
    def promote_experiment(self, project_id : int , experiment_group_code: str, version: str) -> Dict[str, Any]:
        """
        Promote an experiment to production.
        
        Args:
            experiment_group_code: Code of the experiment group
            version: Version number
            
        Returns:
            Dictionary with promotion status
        """
        endpoint = PROMOTE_ENDPOINT
        payload = {
            "project_id": project_id,
            "experiment_group_code": experiment_group_code,
            "version": version
        }
        
        response = self._execute_with_progress(
            f"Promoting experiment {experiment_group_code} version {version}...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response
    
    def get_promoted_experiments(self, project_id: int = None) -> Dict[str, Any]:
        """
        Get a list of promoted experiments for a specific project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with promoted experiments data
        """
        endpoint = PROMOTE_ENDPOINT
        
        if project_id is not None:
            endpoint += f"?project_id={project_id}"
        response = self._execute_with_progress(
            f"Fetching promoted experiments for project {project_id}...",
            lambda: self.api_client.get(endpoint=endpoint)
        )
        return response
    
    def rerun_experiment(self, payload):
        """
        Rerun an experiment with the provided payload.
        
        Args:
            payload: Dictionary containing experiment parameters
            
        Returns:
            Response from the API
        """
        endpoint = RERUN_EXPERIMENT_ENDPOINT
        response = self._execute_with_progress(
            f"Rerunning experiment...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )
        
        return response
    
    @BaseManager.handle_api_error(show_details=True)
    def experiment_gitpush(self,payload):
        "Push experiment to GIT"

        endpoint = GITPUSH_EXPERIMENT_ENDPOINT
        response = self._execute_with_progress(
            f"Pushing experiment to GIT...",
            lambda: self.api_client.post(endpoint=endpoint, data=payload)
        )

        return response
    