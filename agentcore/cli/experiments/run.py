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

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.traceback import install
from rich.table import Table
from typing import List, Dict, Tuple, Optional, Any
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from datetime import datetime
from rich.box import MINIMAL_HEAVY_HEAD
from rich.panel import Panel
import os
import csv
from datetime import datetime
import os
import csv
from rich.panel import Panel
from rich.table import Table
from rich import box
import json
import yaml
import tempfile
import os
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from textual.app import App
from textual.widgets import TextArea
from textual.widgets import TextArea, Footer, Button
from textual.containers import Vertical, Horizontal
import yaml
import tempfile

import copy
import yaml


from agentcore.managers.experiment_manager import ExperimentManager
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.experiments_manager import ExperimentsManager
from agentcore.cli.experiments.logs import LogMonitor
from agentcore.cli.experiments.helpers import *
from agentcore.cli.experiments.main import *



@experiments.command(name="run", help="Run an experiment with selected project, instance, and data version.")
@BaseManager.handle_api_error
def run():
    """List experiments for a selected project and its instances, table-style."""
    experiment_manager = ExperimentManager()
    project_manager = ProjectManager()
    instance_manager = InstanceManager()
    table_display = TableDisplay()
    
    # Step 1: Get available projects
    # Step 2: Select project

    selected_project = get_project_list()
    
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")
    
    # Step 3: Show instances for the selected project
    console.print(f"\n[bold blue]Instances for project ID {project_id}:[/bold blue]")
    response = instance_manager.project_instance_show(project_id)
    
    if response and response.get('instances'):
        instances = response['instances']
        table_display.display_table(
            response_data={'results': instances, 'count': len(instances)},
            columns=instance_manager.project_instance_columns,
            title_prefix=f'Project Instances (Project ID: {project_id})',
            row_formatter=table_display.format_instance_row
        )
        
        # Step 4: Select an instance
        instance_id = select_instance(instances)
        if instance_id:
            console.print(f"[bold green]Selected Instance ID: {instance_id}[/bold green]")
        else:
            console.print("[yellow]No instance selected. Exiting.[/yellow]")
            return
    else:
        console.print("[yellow]No instances found for this project.[/yellow]")
        return
    
    # Step 5: Fetch and display data versions
    console.print(f"\n[bold blue]Data Versions for project ID {project_id}:[/bold blue]")
    data_versions = experiment_manager.list_data_versions(project_id)

    # Create a direct Table instead of using TableDisplay
    from rich.table import Table

    version_table = Table(title="Data Versions")
    version_table.add_column("ID")
    version_table.add_column("Data Source")
    version_table.add_column("Created By")
    version_table.add_column("Updated By")
    version_table.add_column("Created At")
    version_table.add_column("Updated At")

    for version in data_versions:
        created_at = version.get('created_at', '')
        if created_at:
            created_at = beautify_datetime(created_at)
        
        updated_at = version.get('updated_at', '')
        if updated_at:
            updated_at = beautify_datetime(updated_at)
        
        # Format the data source field to avoid multi-line dictionary spillover
        data_source = version.get('data_source', {})
        data_source_str = f"{data_source.get('description', 'N/A')} ({data_source.get('source_type', 'Unknown')})"
        
        version_table.add_row(
            str(version.get('id', '')),
            data_source_str,
            version.get('created_by', ''),
            version.get('updated_by', ''),
            created_at,
            updated_at,
        )

    console.print(version_table)

    # Step 6: Select a data version
    data_version_id = select_data_version(data_versions, table_display)
    if not data_version_id:
        console.print("[yellow]No data version selected. Exiting.[/yellow]")
        return
    
    # Extract the data source for the selected data version
    data_source = "unknown"
    for dv in data_versions:
        if dv.get("id") == data_version_id:
            data_source = str(dv.get("data_source", "unknown"))
            break
    
    # Step 7: Fetch columns for the selected data version
    console.print(f"\n[bold blue]Fetching columns for data version ID {data_version_id}...[/bold blue]")
    columns_data = experiment_manager.fetch_columns(data_version_id)
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns available for this data version.[/yellow]")
        return
    
    # Step 8: Select target column (only ask once)
    # Step 8: Select target column (enhanced UX)
    target_column = select_target_column_enhanced(columns_data)

    if not target_column:
        console.print("[yellow]No target column selected. Exiting.[/yellow]")
        return
    
    if not target_column:
        console.print("[yellow]No target column selected. Exiting.[/yellow]")
        return
        
    console.print(f"\n[bold green]Successfully selected target column: {target_column}[/bold green]")
        
    # Step 9: Select feature columns
    console.print("\n[bold]Now, let's select feature columns for your experiment:[/bold]")
    console.print("[dim]These are the columns that will be used to predict the target.[/dim]")
    
    # Step 9: Select feature columns (enhanced UX)
    feature_columns = select_feature_columns_enhanced(columns_data, target_column)

    if not feature_columns:
        if Confirm.ask("\n[yellow]No feature columns selected. Would you like to use all available columns (except target)?[/yellow]"):
            # Use all columns except the target as features
            feature_columns = [c for c in columns_data.get('columns', []) if c != target_column]
            console.print(f"[green]Using all {len(feature_columns)} non-target columns as features[/green]")
        else:
            console.print("[yellow]No feature columns selected. Exiting.[/yellow]")
            return
    
    # Step 10: Get and select model type
    console.print(f"\n[bold blue]Available Model Types for Project Type ID {project_type_id}:[/bold blue]")
    model_types = experiment_manager.get_model_types(project_type_id)
    
    if not model_types:
        console.print("[yellow]No model types available for this project type. Exiting.[/yellow]")
        return
    
    model = get_model_search_list(model_types)
    
    if not model:
        console.print("[yellow]No model type selected. Exiting.[/yellow]")
        return
    model_type_id = model['id']
    selected_model = model
    
    # Ensure selected_model is a dictionary
    if selected_model is None:
        selected_model = {"model_name": "Unknown"}
    elif not isinstance(selected_model, dict):
        selected_model = {"model_name": str(selected_model)}
    
    # Step 11: Get and collect hyperparameters
    console.print(f"\n[bold blue]Hyperparameters for Model Type {selected_model.get('model_name')}:[/bold blue]")
    hyperparameters = experiment_manager.get_model_hyperparameters(model_type_id)
    
    hyperparameter_values = collect_hyperparameters(hyperparameters)
    
    # Step 12: Ask for train-test split ratio
    train_test_split = 0.8  # Default value
    train_test_split_input = Prompt.ask("[bold blue]Enter train-test split ratio (default is 0.8): [/bold blue]")
    if train_test_split_input:
        try:
            train_test_split = float(train_test_split_input)
            if not (0 < train_test_split < 1):
                console.print("[yellow]Invalid train-test split ratio. Using default value of 0.8.[/yellow]")
                train_test_split = 0.8
        except ValueError:
            console.print("[yellow]Invalid train-test split ratio. Using default value of 0.8.[/yellow]")
    
    # Step 13: Enter experiment name and description
    from datetime import datetime
    default_name = f"Experiment-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    experiment_name = Prompt.ask("[bold]Enter experiment name (leave blank for default):[/bold] ")
    if not experiment_name:
        experiment_name = default_name
        
    default_description = f"Experiment created by CLI on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    description = Prompt.ask("[bold blue]Enter experiment description (leave blank for default):[bold blue] ")
    if not description:
        description = default_description
    
    # Step 14: Show complete experiment configuration
    console.print("\n[bold]Complete Experiment Configuration:[/bold]")
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Property", style="bold cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Experiment Name", experiment_name)
    summary_table.add_row("Description", description)
    summary_table.add_row("Project ID", str(project_id))
    summary_table.add_row("Project Type ID", str(project_type_id))
    summary_table.add_row("Instance ID", str(instance_id))
    summary_table.add_row("Data Version ID", str(data_version_id))
    summary_table.add_row("Target Column", str(target_column))
    summary_table.add_row("Feature Columns", f"{len(feature_columns)} columns selected")
    summary_table.add_row("Data Source ID", str(eval(data_source).get("id", "N/A")) if isinstance(data_source, str) else str(data_source.get("id", "N/A")))
    summary_table.add_row("Train-Test Split", str(train_test_split))
    summary_table.add_row("Model Type", f"{selected_model.get('model_name', 'N/A')} (ID: {str(model_type_id)})")
    summary_table.add_row("Hyperparameters", f"{len(hyperparameter_values)} parameters configured")
    
    console.print(summary_table)
    
    if Confirm.ask("\n[bold]Proceed with creating this experiment?[/bold]"):
        console.print("[green]Creating experiment...[/green]")
        
        # Prepare API payload according to the specified format
        import json
        
        # Convert any numeric IDs to integers in the payload
        try:
            instance_id = int(instance_id)
        except (ValueError, TypeError):
            pass
            
        try:
            data_version_id = int(data_version_id)
        except (ValueError, TypeError):
            pass
            
        try:
            project_type_id = int(project_type_id)
        except (ValueError, TypeError):
            pass
            
        # Format the experiment payload
        experiment_payload = {
            "experiment_name": str(experiment_name),
            "description": str(description),
            "instance_id": instance_id,
            "data_version_id": data_version_id,
            "hyperparameters": hyperparameter_values,
            "target_column": str(target_column),
            "feature_columns": [str(col) for col in feature_columns],
            "date_column": None,  # As specified, keep it None
            "source": str(data_source),
            "train_test_split": train_test_split,
            "project_type_id": project_type_id,
            "sub_model_id" : model_type_id,
            "project_id": project_id,
        }
        
        
            
        # ... (your existing experiment creation code) ...
        
        result = experiment_manager.run_experiment(experiment_payload)
        console.print("[green]Experiment created successfully![/green]")
        
        table_display.display_table(
            response_data={'results': [result], 'count': 1},
            columns=list(result.keys()),
            title_prefix="Experiment Creation Result"
        )
        
        # Enhanced log monitoring
        if Confirm.ask("\n[bold blue]Would you like to monitor logs for this experiment?[/bold blue]"):
            # Extract experiment details from result
            experiment_group_code = result.get('experiment_group_code') or result.get('group_code')
            version = result.get('version', '1.0')
            
            if experiment_group_code:
                console.print(f"\n[bold green]Starting live log monitoring...[/bold green]")
                console.print("[yellow]Press Ctrl+C to stop monitoring[/yellow]\n")
                
                # Choose display mode
                # use_live_display = Confirm.ask(
                #     "[bold]Use live table display? (No for simple console output)[/bold]",
                #     default=True
                # )
                use_live_display = False
                # Initialize and start log monitor
                log_monitor = LogMonitor(
                    experiment_manager=experiment_manager,
                    project_id=project_id,
                    experiment_group_code=experiment_group_code,
                    version=version
                )
                
                try:
                    log_monitor.start_monitoring(use_live_display=use_live_display)
                except Exception as e:
                    console.print(f"[red]Error during log monitoring: {str(e)}[/red]")
                finally:
                    # Show summary after monitoring ends
                    summary = log_monitor.get_log_summary()
                    if summary:
                        console.print(f"\n[bold]Log Summary:[/bold]")
                        console.print(f"Total logs collected: {summary['total_logs']}")
                        console.print(f"Log levels: {summary['levels']}")
                        console.print(f"Sources: {summary['sources']}")
            else:
                console.print("[yellow]Could not extract experiment group code from result. Log monitoring unavailable.[/yellow]")
    else:
        console.print("[yellow]Experiment creation cancelled.[/yellow]")
        
        
        

@experiments.command(name="logs", help="View live logs for a running experiment.")
@BaseManager.handle_api_error
def logs():
    """Display live logs for a running experiment."""
    import time
    import threading
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    
    experiment_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay()
    
    # Step 1: Get available projects
    selected_project = get_project_list()
 
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
 
    console.print(f"[bold green]Selected Project ID: {project_id}[/bold green]")

    # Step 3: Get experiment group code and version from user

    selected_experiment = get_experiments_by_project_search_list(project_id)
    if not selected_experiment:
        return None
    
    experiment_group_code = selected_experiment['experiment_group_code']
    version = selected_experiment['version']
    
    # Step 4: Start live log polling
    console.print(f"\n[bold green]Starting live log monitoring for Project {project_id}, Group {experiment_group_code}, Version {version}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
    
    from datetime import datetime

    def fetch_and_display_logs():
        previous_log_content = ""
        
        while True:
            try:
                # Fetch logs
                response = experiment_manager.fetch_logs(project_id, experiment_group_code, version)
                logs = response.get("logs", [])
                
                # Format each log line
                current_log_content = "\n".join([
                    f"{datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')} "
                    f"[{log['level']}] {log['source']}: {log['message']}"
                    for log in logs
                ]) if logs else "[dim]No logs available yet...[/dim]"
                
                # Only update if content has changed
                if current_log_content != previous_log_content:
                    console.clear()
                    console.print(
                        f"[bold blue]Live Logs - Project: {project_id} | Group: {experiment_group_code} | Version: {version}[/bold blue]"
                    )
                    console.print("[yellow]Press Ctrl+C to stop...[/yellow]\n")
                    
                    console.print(current_log_content)
                    previous_log_content = current_log_content
                
                time.sleep(2)
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Log monitoring stopped by user.[/yellow]\n")
                break
            
            except Exception as e:
                console.print(f"\n[red]Error fetching logs: {str(e)}[/red]")
                time.sleep(5)

    
    try:
        fetch_and_display_logs()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting log viewer...[/yellow]")




    return payload
if __name__ == "__main__":
    experiments()