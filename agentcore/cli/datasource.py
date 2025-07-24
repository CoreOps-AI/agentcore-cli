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
from rich.table import Table
from rich.traceback import install
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
from datetime import datetime
import json

from agentcore.managers.datasource_manager import DatasourceManager
from agentcore.managers.data_version_manager import DataVersionManager2

from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list

install()

console = Console()

@click.group()
def datasource():
    """Datasource management commands."""
    pass


#Helper
@BaseManager.handle_api_error
def get_datasource_search_list():
    """Get Datasource list with tab completion using id-type(description) format and return full Datasource dict."""

    datasource_manager = DatasourceManager()
    base_manager = BaseManager()
    response = datasource_manager.view_datasources()

    if not response:
        console.print("[red]No Datasources found.[/red]")
        return None
    
    # Create mapping: formatted string => original datasource dict
    formatted_map = {
        f"{datasource['id']}-{datasource['source_type']}({datasource['description']})": datasource
        for datasource in response if "source_type" in datasource and "id" in datasource and "description" in datasource
    }
    formatted_datasources = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter ID-Type(description)(press Tab for suggestions and Press Enter for Datasorce Selection):[/bold]")
        selected_datasource = base_manager.get_input_with_tab_completion("Datasources", formatted_datasources)
        if selected_datasource in formatted_map:
            datasource = formatted_map[selected_datasource]

            # Format date-time fields
            if datasource.get("created_at"):
                datasource["created_at"] = beautify_datetime(datasource["created_at"],date_only = True)
            if datasource.get("updated_at"):
                datasource["updated_at"] = beautify_datetime(datasource["updated_at"], date_only = True)


            console.print(f"\n[green]✅ Selected Datasource: {datasource['id']}-{datasource['source_type']}({datasource['description']})[/green]")
            console.print("[bold]Selected Datasource Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [datasource]},
                columns=datasource_manager.datasource_columns,
                title_prefix="Selected Project",
                row_formatter=table_display.format_datasource_row
            )

            return datasource
        else:
            console.print(f"\n[yellow]⚠️ '{selected_datasource}' is not a valid datasource entry.[/yellow]")
            suggestions = [p for p in formatted_datasources if selected_datasource.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

#CLI
@datasource.command(name='view')
@BaseManager.handle_api_error
def datasources_all_view():

    # Ask user to select a project first
    from agentcore.cli.experiments.helpers import get_project_list
    selected_project = get_project_list()
    if not selected_project:
        console.print("[red]No project selected. Aborting.[/red]")
        return
    project_id = selected_project['id']

    # Fetch all datasources for the selected project
    datasource_manager = DatasourceManager()
    response = datasource_manager.view_datasources(project_id=project_id)

    if not response:
        console.print(f"[yellow]No datasources found for project ID {project_id}.[/yellow]")
        return
    

    # Show summary table for all datasources
    console.print(f"[bold green]Datasources for Project: {selected_project['name']} (ID: {project_id})[/bold green]")
    table_display = TableDisplay(console)
    columns = [
        "id", "source_type", "description", "created_by", "created_at", "data_source_type", "project"
    ]
    results = []
    for ds in response:
        results.append({
            "id": ds.get("id"),
            "source_type": ds.get("source_type"),
            "description": ds.get("description"),
            "created_by": ds.get("created_by"),
            "created_at": beautify_datetime(ds.get("created_at")) if ds.get("created_at") else "",
            "data_source_type": ds.get("data_source_type"),
            "project": ds.get("project"),
        })
    table_display.display_table(
        response_data={'results': results},
        columns=columns,
        title_prefix="Datasource Summary"
    )
    












    """List of datasources"""
    # Ask if user wants to filter by datasource ID
    filter_by_id = Prompt.ask(
        "[bold]Fetch details by datasource ID?[/bold] (y/n)", 
        choices=["y", "n"], 
        default="n"
    )
    datasource_manager = DatasourceManager()

    if filter_by_id == "n":
        return 
        # View all datasources
        # response = datasource_manager.view_datasources()
    

        # if not response:
        #     console.print("[yellow]No datasources found.[/yellow]")
        #     return
        
        # for datasource in response:
        #     datasource['created_at'] = beautify_datetime(datasource['created_at'])

        # # Define the columns we want to display based on new payload structure

        # console.print("[bold green]Datasource Details:[/bold green]")
        # table_display = TableDisplay(console)
        # table_display.display_table(
        #     response_data={'results': response},
        #     columns=datasource_manager.datasource_columns,
        #     title_prefix="Datasource",
        #     row_formatter=table_display.format_datasource_row
        #)

    else:
        # View specific datasource by ID
        #Get available datasource IDs from the summary table 
        available_ids= [str(ds.get('id')) for ds in results]
        datasource_id = Prompt.ask("[bold]Enter Datasource ID[/bold]")
        if not datasource_id:
            console.print("[red]Datasource ID is required. Aborting the operation.[/red]")
            return
        
        if datasource_id not in available_ids:
            console.print(f"[red]Invalid Datasource ID: {datasource_id}. Available IDs are: {', '.join(available_ids)}[/red]")
            return

        response = datasource_manager.view_datasources(datasource_id)

        if not response:
            console.print("[yellow]No datasource found with that ID.[/yellow]")
            return
        response['created_at'] = beautify_datetime(response['created_at'])

        # Display the main table with core info
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [response]},
            columns=datasource_manager.datasource_columns,
            title_prefix="Datasource",
            row_formatter=table_display.format_datasource_row
        )
        
        # Check datasource type and display relevant details
        datasource_type = response.get("data_source_type")

        if datasource_type == 1:  # DB
            # DB specific details
            
            db_details = response['db_details']
            db_details.pop('connection_url', None)
            db_details.pop('password',None)

            if any(db_details.values()):  # Only display if there are any values
                console.print("[bold green]Database Details:[/bold green]")
                columns = list(db_details.keys())
                
                table_display.display_table(
                    response_data={'results': [db_details]},
                    columns=columns,
                    title_prefix="Database Details",
                    row_formatter=table_display.format_datasource_row
                )
                
        elif datasource_type == 2:  # API
            # API specific details
            api_details = {
                "api_url": response.get("api_url", ""),
                "api_type": response.get("api_type", ""),
                # Auth token intentionally excluded for security
            }
            
            if any(api_details.values()):  # Only display if there are any values
                console.print("[bold green]API Details:[/bold green]")
                columns = list(api_details.keys())
                
                table_display.display_table(
                    response_data={'results': [api_details]},
                    columns=columns,
                    title_prefix="API Details",
                    row_formatter=table_display.format_datasource_row
                )
                
        elif datasource_type == 3:  # File
            # File specific details
            file_details = {
                "file_path": response.get("file_path", "")
            }
            
            if any(file_details.values()):  # Only display if there are any values
                console.print("[bold green]File Details:[/bold green]")
                columns = list(file_details.keys())
                
                table_display.display_table(
                    response_data={'results': [file_details]},
                    columns=columns,
                    title_prefix="File Details",
                    row_formatter=table_display.format_datasource_row
                )


@BaseManager.handle_api_error
def beautify_datetime(dt_str, date_only=False):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Convert Zulu to UTC offset
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d") if date_only else dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

@datasource.command(name='create')
def datasources_create():
    """Create a datasource"""

    datasource_manager = DatasourceManager()
    base_manager = BaseManager()
    data_version_manager = DataVersionManager2()
    datasource_types = datasource_manager.datasource_types()
    datasource_types.sort(key=lambda x: x["id"])

    if not datasource_types:
        console.print("[red]Datasource types are empty.[/red]")
        return None

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': datasource_types},
        columns=datasource_manager.datasource_types_column,
        title_prefix="Datasource Types",
        row_formatter=table_display.format_datasource_row
    )

    data_source_type_id = Prompt.ask("[bold]Enter Datasource Type ID[/bold]")
    if not data_source_type_id:
        console.print(f"[red]Error: Datasource Type is required. Aborting the operation.[/red]")
        return

    description = Prompt.ask("[bold]Enter Description[/bold]")
    selected_project = get_project_list()
 
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")

    payload = {
        "data_source_type_id": int(data_source_type_id),
        "description": description,
        "project_id": project_id
    }
    
    for key, value in payload.items():
        if value in [None, "", []]:  # Check for empty values
            console.print(f"[red]Error: '{key}' cannot be empty. Aborting the operation.[/red]")
            return None

    # Prompt based on type
    if data_source_type_id == "1":  # DB
        db_type = Prompt.ask("[bold]Enter Database type[/bold]").lower()
        host = Prompt.ask("[bold]Enter Host[/bold]")
        port = int(Prompt.ask("[bold]Enter Port[/bold]"))
        user_name = Prompt.ask("[bold]Enter Username[/bold]")
        password = base_manager.masked_input("\n[bold]Enter password:[/bold] ")
        db_name = Prompt.ask("[bold]Enter Database name[/bold]")
        db_table = Prompt.ask("[bold]Enter Table name[/bold]")

        if not db_type or not db_name:
            console.print(f"[red]Error: Database Type nor Database Name cannot be empty. Aborting the operation.[/red]")
            return None

        payload.update({
            "db_type": db_type,
            "port": port,
            "host": host,
            "user_name": user_name,
            "password": password,
            "db_name": db_name,
            "db_table": db_table
        })

    elif data_source_type_id == "2":  # API
        api_url = Prompt.ask("[bold]Enter API URL[/bold]")
        api_type = Prompt.ask("[bold]Enter API Type (GET/POST/PUT)[/bold]", choices=["GET", "POST", "PUT"])
        auth_token = Prompt.ask("[bold]Enter Auth Token[/bold]")
        payload.update({
            "api_url": api_url,
            "api_type": api_type,
            "auth_token": auth_token
        })
        
    elif data_source_type_id == "3":  # File
        file_path = Prompt.ask("[bold]Enter File Path[/bold]")
        payload.update({
            "file_path": file_path
        })

    console.print("\n[bold]Datasource Summary:[/bold]")
    for key, value in payload.items():
        if key == "password":
            console.print(f"{key}: ******")  # Don't show password in summary
        else:
            console.print(f"{key}: {value}")

    if Prompt.ask("\n[bold]Create Datasource?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Datasource creation cancelled.[/yellow]")
        return None
    print(payload)
    response = datasource_manager.create_datasource(payload)

    if isinstance(response, str):
        try:
            response = json.loads(response)
        except Exception as e:
            console.print(f"[red]Failed to parse response: {e}[/red]")
            return None

    if not isinstance(response, dict):
        console.print(f"[red]Unexpected response format: {response}[/red]")
        return None

    table_display.display_table(
        response_data={'results': [response]},
        columns=datasource_manager.datasource_columns,
        title_prefix="Datasource",
        row_formatter=table_display.format_datasource_row
    )
    data_source_id = response.get('id')
    preview_data = data_version_manager.preview_data_source(data_source_id)
    if not preview_data:
        console.print("[bold red]Invalid or missing data source credentials. Please verify and try again.[/bold red]")
        return
    data = preview_data['preview']
    columns = preview_data['columns']
    total_rows = preview_data['stats']['total_rows']
    total_columns = preview_data['stats']['total_columns']
    console.print(f"\n[bold green]✅ Data from Data source fetched successfully![/bold green]")
    console.print(f"[yellow]Total Rows:[/yellow] {total_rows}")
    console.print(f"[yellow]Total Columns:[/yellow] {total_columns}\n")

    console.print("[bold blue]Columns in the dataset:[/bold blue]")
    for idx, col in enumerate(columns, start=1):
        console.print(f"  {idx}. {col}")

    if len(columns) > 10:
        console.print(f"\n[bold red]Note:[/bold red] More than 10 columns found. Displaying only the first 10 columns for preview.\n")
        columns = columns[:10]
        data = [{col: row[col] for col in columns} for row in data]

    console.print(f"\n[bold green]🔍 Preview of data from the datasource[/bold green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': data},
        columns=columns,
        title_prefix="Preview Data",
        # row_formatter=table_display.format_datasource_row
    )
    

if __name__ == "__main__":
    datasource()