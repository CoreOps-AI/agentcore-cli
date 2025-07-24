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

import time
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
import re
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
import signal
import sys
from rich.live import Live
import json
import hashlib


from agentcore.managers.base import BaseManager
from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.experiment_manager import ExperimentManager
from agentcore.managers.experiments_manager import ExperimentsManager
from agentcore.managers.credentials_manager import CredentialManager


install()

console = Console()



######### For EveryThing ###########
@BaseManager.handle_api_error
def get_project_list():
    """Get project list with tab completion using project_name(id) format and return full project dict."""
    project_manager = ProjectManager()
    base_manager = BaseManager()
    response = project_manager.view_projects()
    if not response:
        console.print("[red]No Projects found.[/red]\n")
        return None
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{project['name']}({project['id']})": project
        for project in response if "name" in project and "id" in project
    }
    formatted_projects = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter Project Name/ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        
        if len(formatted_projects) == 1:
            selected_project = formatted_projects[0]
            console.print(f"[green]Automatically selected the only available project:[/green] {selected_project}")
        else:
            selected_project = base_manager.get_input_with_tab_completion("Projects", formatted_projects)
        if selected_project in formatted_map:
            project = formatted_map[selected_project]
            if 'project_type' in project and isinstance(project['project_type'], dict):
                project['project_type_details'] = project['project_type']
                project['project_type_id'] = project['project_type'].get('id', 'N/A')
                project['project_type'] = project['project_type'].get('type_name', 'N/A')

                # Format date-time fields
                if project.get("start"):
                    project["start"] = beautify_datetime(project["start"],date_only = True)
                if project.get("finish"):
                    project["finish"] = beautify_datetime(project["finish"], date_only = True)


            console.print(f"\n[green]✅ Selected Project: {project['name']} (ID: {project['id']})[/green]")
            console.print("[bold]Selected Project Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [project]},
                columns=project_manager.columns,
                title_prefix="Selected Project",
                row_formatter=table_display.format_project_row
            )

            return project
        else:
            console.print(f"\n[yellow]⚠️ '{selected_project}' is not a valid project entry.[/yellow]")
            suggestions = [p for p in formatted_projects if selected_project.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_project_type_search_list():
    """Get project list with tab completion using project_name(id) format and return full project type dict."""

    experiments_manager = ExperimentsManager()
    base_manager = BaseManager()

    response = experiments_manager.list_project_types()
    if not response:
        console.print("[red]No Project Types found.[/red]")
        return None
    
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{project_type['type_name']}({project_type['id']})": project_type
        for project_type in response if "type_name" in project_type and "id" in project_type
    }
    formatted_project_types = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter Project Type Name/ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        selected_project_type = base_manager.get_input_with_tab_completion("Projects Types", formatted_project_types)
        if selected_project_type in formatted_map:
            project_type = formatted_map[selected_project_type]

            console.print(f"\n[green]✅ Selected Project Type: {project_type['type_name']} (ID: {project_type['id']})[/green]")
            console.print("[bold]Selected Project Type Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [project_type]},
                columns=experiments_manager.experiments_project_types_columns,
                title_prefix="Selected Project Type",
                row_formatter=table_display.format_experiments_row
            )

            return project_type
        else:
            console.print(f"\n[yellow]⚠️ '{selected_project_type}' is not a valid project type entry.[/yellow]")
            suggestions = [p for p in formatted_project_types if selected_project_type.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_model_search_list(response = None):
    """Get Model list with tab completion using model_name(id) format and return full Model dict."""
    
    experiment_manager = ExperimentManager()
    base_manager = BaseManager()
    if not response:
        response = experiment_manager.all_model_types()
    if not response:
        console.print("[red]No Models found.[/red]")
        return None
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{model['model_name']}({model['id']})": model
        for model in response if "model_name" in model and "id" in model
    }
    formatted_models = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter Model Name/ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        selected_model = base_manager.get_input_with_tab_completion("Models", formatted_models)
        if selected_model in formatted_map:
            model = formatted_map[selected_model]

            console.print(f"\n[green]✅ Selected Model: {model['model_name']} (ID: {model['id']})[/green]")
            console.print("[bold]Selected Model Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [model]},
                columns=experiment_manager.all_model_types_columns,
                title_prefix="Selected Model",
                row_formatter=table_display.format_experiments_row
            )

            return model
        else:
            console.print(f"\n[yellow]⚠️ '{selected_model}' is not a valid model entry.[/yellow]")
            suggestions = [p for p in formatted_models if selected_model.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_experiments_by_project_search_list(project_id = None, data = None):
    """Get Experiment list with tab completion using experiment_group_code(version) format and return full experiment dict."""

    base_manager = BaseManager()
    experiments_manager = ExperimentManager()

    if data:
        response = data
    elif project_id:
        response = experiments_manager.display_experiment_info(project_id)
    
        if not response or 'results' not in response or not response['results']:
            console.print("[red]No Experiments found.[/red]\n")
            return None
        response = response['results']

    count = len(response)
    response.sort(key =lambda x: x['created_at'])
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{experiment['experiment_group_code']}({experiment['version']})": experiment
        for experiment in response if "experiment_group_code" in experiment and "version" in experiment
    }
    formatted_experiments = formatted_map
    # formatted_experiments = sorted(formatted_map.keys())
    console.print(f"\n[bold]Total [green]{count}[/green] Experiments found in selected project[/bold]")
    while True:
        console.print("\n[bold]Enter Experiment Group Code/Version(press Tab for suggestions and Press Enter for Selection):[/bold]")
        selected_experiment = base_manager.get_input_with_tab_completion("Experiments", formatted_experiments)
        if selected_experiment in formatted_map:
            experiment = formatted_map[selected_experiment]

            console.print(f"\n[green]✅ Selected Experiment: {experiment['experiment_group_code']} (Version: {experiment['version']})[/green]")
            console.print("[bold]Selected Experiment Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [experiment]},
                columns=experiments_manager.experiments_columns,
                title_prefix="Selected Experiment",
                row_formatter=table_display.format_experiments_row
            )

            return experiment
        else:
            console.print(f"\n[yellow]⚠️ '{selected_experiment}' is not a valid experiment entry.[/yellow]")
            suggestions = [p for p in formatted_experiments if selected_experiment.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_user_credentials_search_list(user_id):
    """Get Credentials list with tab completion using name(credential_type_name) format and return full credential type dict."""

    credential_manager = CredentialManager()
    base_manager = BaseManager()

    response = credential_manager.get_user_credentials(user_id)
    if not response:
        console.print("[red]No Credentials found. Save credentials with 'agentcore projects github', 'agentcore credentials github' commands.[/red]\n")
        return None
    
    # Create mapping: formatted string => original credential dict
    formatted_map = {
        f"{credential['id']}-{credential['name']}({credential['credential_type_name']})": credential
        for credential in response if "name" in credential and "credential_type_name" in credential and "id" in credential
    }
    formatted_credentials = sorted(formatted_map.keys())

    while True:
        console.print("\n[bold]Enter Name/Credential Type Name(press Tab for suggestions and Press Enter for Selection):[/bold]")
        selected_credential = base_manager.get_input_with_tab_completion("Credentials", formatted_credentials)
        if selected_credential in formatted_map:
            credential = formatted_map[selected_credential]

            credential['created_at'] = beautify_datetime(credential['created_at'])

            console.print(f"\n[green]✅ Selected Project Type: {credential['name']} (ID: {credential['credential_type_name']})[/green]")
            console.print("[bold]Selected Credential Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [credential]},
                columns=credential_manager.columns,
                title_prefix="Selected Credential",
                row_formatter=table_display.format_user_row
            )

            return credential
        else:
            console.print(f"\n[yellow]⚠️ '{selected_credential}' is not a valid credential entry.[/yellow]")
            suggestions = [p for p in formatted_credentials if selected_credential.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def beautify_datetime(dt_str, date_only=False):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Convert Zulu to UTC offset
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d") if date_only else dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
