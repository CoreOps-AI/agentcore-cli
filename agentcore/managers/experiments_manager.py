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
from agentcore.utils.config import (EXPERIMENTS_ENDPOINT, HYPERPARAMETERS_ENDPOINT,
PROJECT_TYPES_ENDPOINT, PROJECT_TYPE_MODELS_ENDPOINT, EXPERIMENTS_METRICS_ENDPOINT,
PROJECT_TYPES_ENDPOINT, PROJECT_TYPE_MODELS_ENDPOINT,EXPERIMENT_SETUP_ENDPOINT,EXPERIMENT_RUN_ENDPOINT,EXPERIMENT_IMAGE_ENDPOINT,
MODEL_TYPES_ENDPOINT, EXPERIMENT_FETCH)


class ExperimentsManager(BaseManager):
    def __init__(self):
        super().__init__()
        self.console = Console()
        self.experiment_run_columns = ["Message", "Instance ID", "User ID", "Model ID", "Experiment ID"]
        self.experiment_setup_columns = ["Message", "Instance ID", "User ID", "Model ID", "Model Name"]
        self.experiment_list_by_project_columns = ["ID", "Project Name", "Run At"]
        self.experiment_metrics_columns = ["ID"]
        self.experiments_project_types_columns = ["ID", "Type Name", "Description"]


    

# Add this method to your ExperimentsManager class

    @BaseManager.handle_api_error
    def list_all_experiments(self) -> Optional[Dict[str, Any]]:
        """Fetch all pipeline experiment records from the database.
        
        Returns:
            Dict containing list of all experiments or None if failed
        """
        try:
            # Use _execute_with_progress for the API call - assuming it returns parsed data directly
            data = self._execute_with_progress(
                "Fetching all pipeline experiment records...",
                lambda: self.api_client.get(EXPERIMENTS_ENDPOINT)
            )
            
            if data == -1:
                return None
                
            # Handle the case where the API returns a list directly
            if isinstance(data, list):
                self.console.print("[green]Retrieved all pipeline experiments successfully![/green]")
                return {"results": data}
            elif isinstance(data, dict):
                self.console.print("[green]Retrieved all pipeline experiments successfully![/green]")
                return data
            else:
                self.console.print(f"[yellow]Unexpected data type: {type(data)}[/yellow]")
                return {"results": [], "error": f"Unexpected data type: {type(data)}"}
            
        except Exception as e:
            self.console.print(f"[red]Failed to fetch pipeline experiments: {str(e)}[/red]")
            return None
        
    @BaseManager.handle_api_error
    def list_experiments_by_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch all experiment records for a specific project from the database.
        
        Args:
            project_id: The ID of the project to fetch experiments for
            
        Returns:
            Dict containing list of project experiments or None if failed
        """
        try:
            # Construct the endpoint URL with the project_id
            endpoint = f"/api/projects/{project_id}/experiments/artifacts/"
            
            # Use _execute_with_progress for the API call
            data = self._execute_with_progress(
                f"Fetching experiment records for project {project_id}...",
                lambda: self.api_client.get(endpoint)
            )
            
            if data == -1:
                return None
                
            # Handle the case where the API returns a list directly
            if isinstance(data, list):
                self.console.print(f"[green]Retrieved all experiments for project {project_id} successfully![/green]")
                return {"results": data}
            elif isinstance(data, dict):
                self.console.print(f"[green]Retrieved all experiments for project {project_id} successfully![/green]")
                return data
            else:
                self.console.print(f"[yellow]Unexpected data type: {type(data)}[/yellow]")
                return {"results": [], "error": f"Unexpected data type: {type(data)}"}
            
        except Exception as e:
            self.console.print(f"[red]Failed to fetch experiments for project {project_id}: {str(e)}[/red]")
            return None
        
    @BaseManager.handle_api_error
    def list_hyperparameters_by_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch hyperparameters for a specific project from the database.
        
        Args:
            project_id: The ID of the project to fetch hyperparameters for
            
        Returns:
            Dict containing list of hyperparameters or None if failed
        """
        try:
            # Construct the endpoint URL with the project_id
            endpoint = f"{HYPERPARAMETERS_ENDPOINT}?project_id={project_id}"
            
            # Use _execute_with_progress for the API call
            data = self._execute_with_progress(
                f"Fetching hyperparameters for project {project_id}...",
                lambda: self.api_client.get(endpoint)
            )
            
            if data == -1:
                return None
            
            # Debug print to understand the data structure
            # self.console.print(f"[yellow]Raw data type: {type(data)}[/yellow]")
            # self.console.print(f"[yellow]Raw data: {data}[/yellow]")
            
            # Adjust data processing to handle different possible response formats
            if data is None:
                return {"results": []}
            
            # If data is a dictionary and contains 'hyperparameters' key
            if isinstance(data, dict) and 'hyperparameters' in data:
                results = data['hyperparameters']
            # If data is a list, use it directly
            elif isinstance(data, list):
                results = data
            # If data is a dictionary, try to extract results
            elif isinstance(data, dict):
                results = list(data.values())[0] if data else []
            else:
                self.console.print(f"[yellow]Unexpected data type: {type(data)}[/yellow]")
                return {"results": [], "error": f"Unexpected data type: {type(data)}"}
            
            # Ensure results is a list
            if not isinstance(results, list):
                results = [results]
            
            self.console.print(f"[green]Retrieved hyperparameters for project {project_id} successfully![/green]")
            return {"results": results}
            
        except Exception as e:
            self.console.print(f"[red]Failed to fetch hyperparameters for project {project_id}: {str(e)}[/red]")
            return None

    # def experiment_setup(self, payload: dict, project_id: str) -> dict:
    #     """Handles the experiment setup by transferring experiment records."""

    #     endpoint = f"{EXPERIMENTS_ENDPOINT}{project_id}/transfer/"

    #     response = self._execute_with_progress(
    #         f"Transferring experiment records for project {project_id}...",
    #         lambda: self.api_client.post(endpoint, payload)
    #     )

    #     return response
    
    # def run_experiment(self, payload: dict, project_id: str) -> dict:
    #     endpoint = f"{HYPERPARAMETERS_ENDPOINT}?project_id={project_id}"
    #     response = self._execute_with_progress(
    #         f"Running experiment records for project {project_id}...",
    #         lambda: self.api_client.post(endpoint, payload)
    #     )
        
    #     return response

    @BaseManager.handle_api_error
    def list_project_types(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all project types from the database.
        
        Returns:
            List of project types or None if failed
        """
        try:
            data = self._execute_with_progress(
                "Fetching project types...",
                lambda: self.api_client.get(PROJECT_TYPES_ENDPOINT)
            )
            
            if data == -1:
                return None
            
            # Ensure we return a list of project types
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            elif isinstance(data, list):
                return data
            else:
                self.console.print(f"[yellow]Unexpected data type: {type(data)}[/yellow]")
                return None
        
        except Exception as e:
            self.console.print(f"[red]Failed to fetch project types: {str(e)}[/red]")
            return None

    @BaseManager.handle_api_error
    def get_models_for_project_type(self, project_type_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch models for a specific project type.
        
        Args:
            project_type_id (int): ID of the project type
        
        Returns:
            List of models or None if failed
        """
        try:
            endpoint = MODEL_TYPES_ENDPOINT.format(project_type_id=project_type_id)
            data = self._execute_with_progress(
                f"Fetching models for project type {project_type_id}...",
                lambda: self.api_client.get(endpoint)
            )
            
            return data
        
        except Exception as e:
            self.console.print(f"[red]Failed to fetch models for project type: {str(e)}[/red]")
            return None
    

    
    @BaseManager.handle_api_error
    def get_experiment_details(self, experiment_id: str = None) -> Optional[Dict[str, Any]]:
            """Fetch details for a specific experiment or all experiments.
            
            Args:
                experiment_id: Optional ID of the experiment to fetch details for
            
            Returns:
                Dict containing experiment details or None if failed
            """
            try:
                # Construct the endpoint URL for experiment details
                endpoint = EXPERIMENTS_METRICS_ENDPOINT
                
                # Add experiment_id parameter if provided
                params = {}
                if experiment_id:
                    params['experiment_id'] = experiment_id
                
                # Use _execute_with_progress for the API call
                data = self._execute_with_progress(
                    f"Fetching {'experiment ' + experiment_id if experiment_id else 'all experiments'} metrics...",
                    lambda: self.api_client.get(endpoint, params=params)
                )
                
                return data
            except Exception as e:
                self.console.print(f"[red]Failed to fetch metrics: {str(e)}[/red]")
                return None
    
    def experiment_setup(self, payload):
        """Handles the experiment setup by transferring experiment records."""

        response = self._execute_with_progress(
            f"Set's up experiment records...",
            lambda: self.api_client.post(EXPERIMENT_SETUP_ENDPOINT, payload)
        )

        return response
    
    def run_experiment(self, payload):
        "Runs experiment"
        response = self._execute_with_progress(
            f"Running experiment records...",
            lambda: self.api_client.post(EXPERIMENT_RUN_ENDPOINT, payload)
        )
        
        return response
    
    def get_images(self, experiment_id: str) -> Optional[str]:
        """Download images for a specific experiment as a zip file.
        
        Args:
            experiment_id: ID of the experiment to fetch images for
                
        Returns:
            Path to the downloaded zip file or None if failed
        """
        try:
            # Construct the endpoint URL for experiment images
            endpoint = f"{EXPERIMENT_IMAGE_ENDPOINT}{experiment_id}/images/download/"
            print(f"Endpoint: {endpoint}")
            
            # Default filename based on experiment ID
            filename = f"experiment_{experiment_id}_images.zip"
            
            # Get the default downloads directory
            if os.name == 'nt':  # Windows
                import winreg
                sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
                downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                    download_dir = winreg.QueryValueEx(key, downloads_guid)[0]
            else:  # Linux, MacOS, etc.
                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
                
            download_path = os.path.join(download_dir, filename)
            
            # Function to handle the download
            def download_file():
                # Make sure we're getting the raw response without automatic JSON parsing
                response = self.api_client.get(
                    endpoint, 
                    stream=True,
                    raw_response=True  # Add this parameter if your API client supports it
                )

                print(f"Response: {response}")
                
                # Check if directory exists
                os.makedirs(os.path.dirname(download_path), exist_ok=True)
                
                # Write the file
                with open(download_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return download_path
                
            # Execute with progress tracking
            result = self._execute_with_progress(
                f"Downloading experiment {experiment_id} images...",
                download_file
            )
            
            # Verify the file exists and has content
            if os.path.exists(download_path) and os.path.getsize(download_path) > 0:
                return download_path
            else:
                self.console.print("[yellow]Warning: Downloaded file appears to be empty or missing[/yellow]")
                return None
            
        except Exception as e:
            self.console.print(f"[red]Failed to download images: {str(e)}[/red]")
            return None
        
    def view_images(self, experiment_id: str) -> bool:
        """
        Fetch and display images for a specific experiment.
        
        Args:
            experiment_id: ID of the experiment to fetch images for
                
        Returns:
            True if successful, False otherwise
        """
        try:
            import io
            import base64
            from PIL import Image
            
            # Import platform-specific libraries
            try:
                # For GUI display
                if os.name == 'nt':  # Windows
                    import tkinter as tk
                    from tkinter import Toplevel
                    from PIL import ImageTk
                else:
                    import matplotlib.pyplot as plt
            except ImportError as e:
                self.console.print(f"[red]Missing required library: {str(e)}[/red]")
                self.console.print("[yellow]Please install PIL, tkinter (for Windows) or matplotlib (for Unix)[/yellow]")
                return False
            
            # Construct the endpoint URL for experiment image details
            endpoint = f"{EXPERIMENT_IMAGE_ENDPOINT}{experiment_id}/images-details/"
            
            # Function to fetch the image data
            def fetch_image_data():
                response = self.api_client.get(endpoint)
                if not response:
                    raise Exception("Failed to fetch image data from the API")
                return response
            
            # Execute with progress tracking
            image_data = self._execute_with_progress(
                f"Fetching experiment {experiment_id} images...",
                fetch_image_data
            )
            
            # Check if we have data for any images
            has_images = False
            for img_key in ['train_image', 'test_image', 'future_image']:
                if image_data.get(img_key):
                    has_images = True
                    break
                    
            if not has_images:
                self.console.print("[yellow]No images found for this experiment.[/yellow]")
                return False
            
            # Function to display the images
            def display_images():
                if os.name == 'nt':  # Windows - use Tkinter
                    root = tk.Tk()
                    root.withdraw()  # Hide the main window
                    
                    for img_name, img_key in [
                        ('Training Data', 'train_image'),
                        ('Test Results', 'test_image'),
                        ('Future Predictions', 'future_image')
                    ]:
                        if image_data.get(img_key):
                            try:
                                # Decode the base64 string
                                img_bytes = base64.b64decode(image_data[img_key])
                                img = Image.open(io.BytesIO(img_bytes))
                                
                                # Create a new window for this image
                                window = Toplevel(root)
                                window.title(f"Experiment {experiment_id} - {img_name}")
                                
                                # Convert PIL Image to Tkinter PhotoImage
                                tk_img = ImageTk.PhotoImage(img)
                                
                                # Create a label and add the image to it
                                label = tk.Label(window, image=tk_img)
                                label.image = tk_img  # Keep a reference to prevent garbage collection
                                label.pack()
                                
                                # Add a close button
                                close_btn = tk.Button(window, text="Close", command=window.destroy)
                                close_btn.pack(pady=10)
                                
                            except Exception as e:
                                self.console.print(f"[red]Failed to display {img_name}: {str(e)}[/red]")
                    
                    # Start the Tkinter event loop
                    root.mainloop()
                    
                else:  # Unix systems - use matplotlib
                    for img_name, img_key in [
                        ('Training Data', 'train_image'),
                        ('Test Results', 'test_image'),
                        ('Future Predictions', 'future_image')
                    ]:
                        if image_data.get(img_key):
                            try:
                                # Decode the base64 string
                                img_bytes = base64.b64decode(image_data[img_key])
                                img = Image.open(io.BytesIO(img_bytes))
                                
                                # Create a new figure and display the image
                                plt.figure(figsize=(10, 8))
                                plt.title(f"Experiment {experiment_id} - {img_name}")
                                plt.imshow(img)
                                plt.axis('off')  # Hide the axes
                                plt.show(block=False)  # Non-blocking to show multiple images
                                
                            except Exception as e:
                                self.console.print(f"[red]Failed to display {img_name}: {str(e)}[/red]")
                    
                    # Keep the plot windows open until manually closed
                    plt.show()
                
                return True
            
            # Show a message about what's happening
            self.console.print(f"[green]Opening image viewer for experiment {experiment_id}...[/green]")
            
            # Execute display function (not with progress bar since it opens windows)
            return display_images()
            
        except Exception as e:
            self.console.print(f"[red]Failed to view images: {str(e)}[/red]")
            return False
    
    @BaseManager.handle_api_error
    def get_experiment_metrics(self, project_id: int, experiment_group_code: str = None, data_version: str = None, data_source: str = None):
        endpoint = EXPERIMENT_FETCH

        # Dynamically build payload based on available filters
        payload = {
            "project_id": project_id,
            "artifacts": True
        }

        if experiment_group_code:
            payload["experiment_group_code"] = experiment_group_code
        if data_version:
            payload["data_version"] = data_version
        if data_source:
            payload["data_source"] = data_source

        response = self._execute_with_progress(
            f"Fetching experiment metrics...",
            lambda: self.api_client.post(endpoint, payload)
        )
        
        return response


 
