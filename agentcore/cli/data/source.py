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
from rich import box

from agentcore.managers.datasource_manager import DatasourceManager
from agentcore.managers.data_version_manager import DataVersionManager2

from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list
from agentcore.cli.data.main import data
from agentcore.cli.data.main import beautify_datetime
install()

console = Console()

@data.command(name='view')
@BaseManager.handle_api_error
def datasources_all_view():
    """
    Datasources view command with tables formatted to match the API response structure.
    """
    from agentcore.cli.experiments.helpers import get_project_list

    # Ask user to select a project first
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
        "id", "source_type", "description", "data_source_type", "project"
    ]
    results = []
    for ds in response:
        results.append({
            "id": ds.get("id"),
            "source_type": ds.get("source_type"),
            "description": ds.get("description"),
            "data_source_type": ds.get("data_source_type"),
            "project": ds.get("projects", [{}])[0].get("name", "N/A"),  # Extract project name
        })
    table_display.display_table(
        response_data={'results': results},
        columns=columns,
        title_prefix="Datasource Summary"
    )

    # Ask if user wants to filter by datasource ID
    filter_by_id = Prompt.ask(
        "[bold]Fetch details by datasource ID?[/bold] (y/n)", 
        choices=["y", "n"], 
        default="n"
    )

    if filter_by_id == "n":
        return

    # View specific datasource by ID
    available_ids = [str(ds.get('id')) for ds in results]
    datasource_id = Prompt.ask("[bold]Enter Datasource ID[/bold]")
    if not datasource_id:
        console.print("[red]Datasource ID is required. Aborting the operation.[/red]")
        return

    if datasource_id not in available_ids:
        console.print(f"[red]Invalid Datasource ID: {datasource_id}. Available IDs are: {', '.join(available_ids)}[/red]")
        return

    response = datasource_manager.view_datasources(datasource_id=datasource_id)

    if not response:
        console.print("[yellow]No datasource found with that ID.[/yellow]")
        return
    
    response["project"] = ds.get("projects", [{}])[0].get("name", "N/A"),  # Extract project name`

    # Display the main table with core info
    table_display.display_table(
        response_data={'results': [response]},
        columns=["id", "source_type", "description", "data_source_type", "project"],
        title_prefix="Datasource"
    )

    # Check datasource type and display relevant details
    datasource_type = response.get("data_source_type")
    
    if datasource_type == 1:  # DB
        db_details = response['db_details']
        db_details.pop('connection_url', None)  # Remove sensitive data
        db_details.pop('password', None)  # Remove sensitive data
        if any(db_details.values()):  # Only display if there are any values
            console.print("[bold green]Database Details:[/bold green]")
            columns = ["db_type", "port", "host", "db_name", "db_table"]
            table_display.display_table(
                response_data={'results': [db_details]},
                columns=columns,
                title_prefix="Database Details"
            )
            
    elif datasource_type == 2:  # API
        api_details = {
            "api_url": response.get("api_url", ""),
            "api_type": response.get("api_type", ""),
        }

        if any(api_details.values()):  # Only display if there are any values
            console.print("[bold green]API Details:[/bold green]")
            columns = ["api_url", "api_type"]
            table_display.display_table(
                response_data={'results': [api_details]},
                columns=columns,
                title_prefix="API Details"
            )
            
    elif datasource_type == 3:  # File
        file_details = {
            "file_path": response['file_details'].get("file_path_source", ""),
            "file_type": response['file_details'].get("file_type", ""),
        }

        if any(file_details.values()):  # Only display if there are any values
            console.print("[bold green]File Details:[/bold green]")
            columns = ["file_path", "file_type"]
            table_display.display_table(
                response_data={'results': [file_details]},
                columns=columns,
                title_prefix="File Details"
            )

class CustomHelpCommand(click.Command):
    def get_help(self, ctx):
        console.print(
            "[bold blue]Demo Database Connection Details[/bold blue]\n"
            "database_type   : mysql\n"
            "host            : localhost\n"
            "port            : 2807\n"
            "username        : demo_user\n"
            "password        : agentcore_welcome\n"
            "database_name   : agentcore_demo_data\n"
            "table_name      :\n"
            "    - kia_sales      (timeseries)\n"
            "    - income_data    (classification)\n"
            "    - diabetes       (regression)\n"
        )
        return ""


@data.command(name='connect', cls = CustomHelpCommand)
def datasources_create():
    """Create a datasource with improved UX"""
    datasource_manager = DatasourceManager()
    base_manager = BaseManager()
    
    console.print("[bold blue]🚀 Welcome to Datasource Creation Wizard[/bold blue]\n")
    
    # Step 1: Display and select datasource type
    datasource_type_id = _display_and_select_datasource_type(datasource_manager, base_manager)
    if not datasource_type_id:
        return None
    
    if datasource_type_id != '1':
        console.print("[blue]For trail version, only Database is available. Please select 'Database'.[/blue]\n")
        return 

    
    # Remove the old _get_datasource_type_with_validation call since we're doing it above now
    
    # Step 2: Get basic information
    console.print(f"\n[bold green]Step 2: Basic Information[/bold green]")
    description = _get_description_with_validation()
    
    # Step 3: Select project
    console.print(f"\n[bold green]Step 3: Project Selection[/bold green]")
    selected_project = get_project_list()
    if not selected_project:
        console.print("[red]Error: No project selected. Aborting.[/red]")
        return None
    
    project_id = selected_project['id']
    
    # Step 4: Get datasource-specific configuration
    console.print(f"\n[bold green]Step 4: Datasource Configuration[/bold green]")
    datasource_config = _get_datasource_config(datasource_type_id, base_manager)
    if not datasource_config:
        return None
    
    # Build final payload
    payload = {
        "data_source_type_id": int(datasource_type_id),
        "description": description,
        "project_id": project_id,
        **datasource_config
    }
    
    # Step 5: Review and confirm
    console.print(f"\n[bold green]Step 5: Review & Confirm[/bold green]")
    if not _review_and_confirm(payload):
        console.print("[yellow]✋ Datasource creation cancelled.[/yellow]")
        return None
    
    # Step 6: Create datasource
    console.print(f"\n[bold green]Step 6: Creating Datasource...[/bold green]")
    response = _create_datasource_with_error_handling(datasource_manager, payload)
    if not response:
        return
    _display_created_datasource(response)
    

    return response


def _display_and_select_datasource_type(datasource_manager, base_manager):
    """Display available datasource types with tab completion"""
    datasource_types = datasource_manager.datasource_types()

    if not datasource_types:
        console.print("[red]❌ No datasource types available.[/red]")
        return None
    
    datasource_types.sort(key=lambda x: x["id"])
    
    console.print("[bold green]Step 1: Choose Datasource Type[/bold green]")
    console.print("Available datasource types:\n")
    
    # Display options in a simple list format
    type_options = []
    type_mapping = {}
    
    for ds_type in datasource_types:
        # Special handling for MySQL - show as Database
        display_name = "Database" if ds_type['description'] == 'MySQL' else ds_type['description']
        
        # Create a readable option string
        option_text = f"{display_name} (ID: {ds_type['id']})"
        type_options.append(option_text)
        
        # Create mapping for both name and ID
        type_mapping[display_name.lower()] = ds_type['id']
        type_mapping[str(ds_type['id'])] = ds_type['id']
        type_mapping[option_text.lower()] = ds_type['id']
        
        # Also map the original description for internal use
        if ds_type['description'] == 'MySQL':
            type_mapping['mysql'] = ds_type['id']
            type_mapping['database'] = ds_type['id']
        
        # Display the option
        console.print(f"  [bold cyan]{ds_type['id']}.[/bold cyan] {display_name}")
        
        # Add helpful descriptions
        if display_name == "Database":
            console.print(f"     [dim]Connect to MySQL databases[/dim]")
        elif display_name == "API":
            console.print(f"     [dim]Connect to REST APIs[/dim]")
        elif display_name == "File":
            console.print(f"     [dim]Upload and process files (CSV, JSON, etc.)[/dim]")
    
    console.print()
    
    console.print("\n💡 Tip: Use [bold]agentcore data connect --help[/bold] to see demo database connection details\n")
    # Use tab completion to get user selection
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            selected = base_manager.get_input_with_tab_completion(
                "Select datasource type (name or ID)", 
                type_options
            )
            
            if not selected or not selected.strip():
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    console.print(f"[red]❌ Selection cannot be empty. {remaining} attempts remaining.[/red]")
                    continue
                else:
                    console.print("[red]❌ Maximum attempts exceeded. Aborting.[/red]")
                    return None
            
            # Try to find the selected type
            selected_clean = selected.strip().lower()
            
            # Check if it's a direct match
            if selected_clean in type_mapping:
                selected_id = str(type_mapping[selected_clean])
                
                # Get the display name for confirmation
                for ds_type in datasource_types:
                    if str(ds_type['id']) == selected_id:
                        display_name = "Database" if ds_type['description'] == 'MySQL' else ds_type['description']
                        console.print(f"[green]✅ Selected: {display_name}[/green]")
                        break
                
                return selected_id
            
            # Check if it's a partial match
            for key, value in type_mapping.items():
                if selected_clean in key or key in selected_clean:
                    selected_id = str(value)
                    
                    # Get the display name for confirmation
                    for ds_type in datasource_types:
                        if str(ds_type['id']) == selected_id:
                            display_name = "Database" if ds_type['description'] == 'MySQL' else ds_type['description']
                            console.print(f"[green]✅ Selected: {display_name}[/green]")
                            break
                    
                    return selected_id
            
            # If no match found
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ Invalid selection: '{selected}'. {remaining} attempts remaining.[/red]")
                console.print("[yellow]💡 Tip: Use Tab for auto-completion or enter the ID number.[/yellow]")
            else:
                console.print("[red]❌ Maximum attempts exceeded. Aborting.[/red]")
                return None
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]❌ Error during selection: {e}[/red]")
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"{remaining} attempts remaining.")
            else:
                return None
    
    return None



def _get_datasource_type_with_validation(datasource_manager):
    """Get datasource type with validation and retry logic"""
    datasource_types = datasource_manager.datasource_types()
    valid_ids = [str(dt["id"]) for dt in datasource_types]
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        data_source_type_id = Prompt.ask(
            f"[bold]Enter Datasource Type ID ({'/'.join(valid_ids)})[/bold]"
        )
        
        if data_source_type_id in valid_ids:
            return data_source_type_id
        
        remaining = max_attempts - attempt - 1
        if remaining > 0:
            console.print(f"[red]❌ Invalid ID. Valid options: {', '.join(valid_ids)}. {remaining} attempts remaining.[/red]")
        else:
            console.print("[red]❌ Maximum attempts exceeded. Aborting.[/red]")
    
    return None


def _get_description_with_validation():
    """Get description with validation"""
    max_attempts = 3
    
    for attempt in range(max_attempts):
        description = Prompt.ask("[bold]Enter Description[/bold]")
        
        if description and description.strip():
            return description.strip()
        
        remaining = max_attempts - attempt - 1
        if remaining > 0:
            console.print(f"[red]❌ Description cannot be empty. {remaining} attempts remaining.[/red]")
        else:
            console.print("[red]❌ Maximum attempts exceeded. Using default description.[/red]")
            return "Auto-generated datasource"
    
    return "Auto-generated datasource"


def _get_datasource_config(datasource_type_id, base_manager):
    """Get configuration based on datasource type"""
    if datasource_type_id == "1":  # Database
        return _get_database_config(base_manager)
    elif datasource_type_id == "2":  # API
        return _get_api_config()
    elif datasource_type_id == "3":  # File
        return _get_file_config()
    else:
        console.print(f"[red]❌ Unsupported datasource type: {datasource_type_id}[/red]")
        return None


def _get_database_config(base_manager):
    """Get database configuration with validation and trial version restrictions"""
    console.print("[bold cyan]📊 Database Configuration[/bold cyan]")
    
    # Database type with validation and trial restrictions
    console.print("\n[bold]Available database types:[/bold]")
    console.print("  [bold green]1.[/bold green] MySQL [green](Available)[/green]")
    console.print("  [dim]2. PostgreSQL (Not available in trial version)[/dim]")
    console.print("  [dim]3. SQLite (Not available in trial version)[/dim]")
    console.print("  [dim]4. Oracle (Not available in trial version)[/dim]")
    console.print("  [dim]5. SQL Server (Not available in trial version)[/dim]")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        db_type_input = Prompt.ask("\n[bold]Enter Database type[/bold]", default="mysql").lower().strip()
        
        if db_type_input in ['mysql', '1']:
            db_type = 'mysql'
            break
        elif db_type_input in ['postgresql', 'postgres', 'sqlite', 'oracle', 'mssql', 'sqlserver', '2', '3', '4', '5']:
            console.print(f"[yellow]⚠️  {db_type_input.upper()} is not available in the trial version.[/yellow]")
            console.print("[blue]💡 Upgrade to the full version to access all database types.[/blue]")
            
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[yellow]Please select MySQL. {remaining} attempts remaining.[/yellow]")
                continue
            else:
                console.print("[red]❌ Only MySQL is available in trial version. Aborting.[/red]")
                return None
        else:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ Invalid database type. {remaining} attempts remaining.[/red]")
                console.print("[yellow]💡 Enter 'mysql' or '1' for MySQL.[/yellow]")
            else:
                console.print("[red]❌ Maximum attempts exceeded. Aborting.[/red]")
                return None
    
    # Continue with the rest of the database configuration...
    # Host
    host = _get_input_with_validation(
        "[bold]Enter Host[/bold]",
        default="localhost",
        validator=lambda x: len(x.strip()) > 0,
        error_msg="Host cannot be empty"
    )
    
    # Port with validation (MySQL default)
    port = _get_port_with_validation('mysql')  # Always MySQL in trial
    if not port:
        return None
    
    # Username
    user_name = _get_input_with_validation(
        "[bold]Enter Username[/bold]",
        validator=lambda x: len(x.strip()) > 0,
        error_msg="Username cannot be empty"
    )
    
    # Password
    password = _get_password_with_validation(base_manager)
    if not password:
        return None
    
    # Database name
    db_name = _get_input_with_validation(
        "[bold]Enter Database name[/bold]",
        validator=lambda x: len(x.strip()) > 0,
        error_msg="Database name cannot be empty"
    )
    
    # Table name
    db_table = _get_input_with_validation(
        "[bold]Enter Table name[/bold]",
        validator=lambda x: len(x.strip()) > 0,
        error_msg="Table name cannot be empty"
    )
    
    if not all([db_type, host, user_name, db_name, db_table]):
        console.print("[red]❌ Missing required database configuration.[/red]")
        return None
    
    connection_url = f"{db_type}://{user_name}:{password}@{host}:{port}/{db_name}"
    
    return {
        "connection_url": connection_url,
        "db_type": db_type,
        "port": port,
        "host": host,
        "user_name": user_name,
        "password": password,
        "db_name": db_name,
        "db_table": db_table,
        "data_type_id": 1,
    }

def _get_api_config():
    """Get API configuration with validation"""
    console.print("[bold cyan]🌐 API Configuration[/bold cyan]")
    
    # API URL with validation
    api_url = _get_input_with_validation(
        "[bold]Enter API URL[/bold]",
        validator=lambda x: x.startswith(('http://', 'https://')),
        error_msg="API URL must start with http:// or https://"
    )
    
    # API Type
    api_type = Prompt.ask(
        "[bold]Enter API Type[/bold]", 
        choices=["GET", "POST", "PUT"], 
        default="GET"
    )
    
    # Auth Token (optional)
    auth_token = Prompt.ask("[bold]Enter Auth Token (optional)[/bold]", default="")
    
    if not api_url:
        console.print("[red]❌ Missing required API configuration.[/red]")
        return None
    
    return {
        "api_url": api_url,
        "api_type": api_type,
        "auth_token": auth_token
    }


def _get_file_config():
    """Get file configuration with actual file upload support"""
    console.print("[bold cyan]📁 File Configuration[/bold cyan]")
    console.print("[dim]This will upload a file to the server for processing.[/dim]\n")
    
    # Show supported file types
    console.print("[bold]Supported file types:[/bold]")
    console.print("  • CSV files (.csv)")
    console.print("  • JSON files (.json)")
    console.print("  • Excel files (.xlsx, .xls)")
    console.print("  • Text files (.txt)")
    console.print()
    
    # Get file path with validation
    max_attempts = 3
    file_path = None
    
    for attempt in range(max_attempts):
        file_path = Prompt.ask("[bold]Enter the full path to your file[/bold]")
        
        if not file_path or not file_path.strip():
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ File path cannot be empty. {remaining} attempts remaining.[/red]")
                continue
            else:
                console.print("[red]❌ File path is required. Aborting.[/red]")
                return None
        
        file_path = file_path.strip()
        
        # Expand user path (handles ~/ on Unix systems)
        import os
        file_path = os.path.expanduser(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ File not found: {file_path}. {remaining} attempts remaining.[/red]")
                console.print("[yellow]💡 Make sure to provide the full path to the file.[/yellow]")
                continue
            else:
                console.print(f"[red]❌ File not found: {file_path}. Aborting.[/red]")
                return None
        
        # Check if it's a file (not directory)
        if not os.path.isfile(file_path):
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ Path is not a file: {file_path}. {remaining} attempts remaining.[/red]")
                continue
            else:
                console.print(f"[red]❌ Path is not a file: {file_path}. Aborting.[/red]")
                return None
        
        # Check file size (optional - you can adjust the limit)
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB limit
        if file_size > max_size:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                console.print(f"[red]❌ File too large: {file_size:,} bytes. Maximum allowed: {max_size:,} bytes. {remaining} attempts remaining.[/red]")
                continue
            else:
                console.print(f"[red]❌ File too large: {file_size:,} bytes. Maximum allowed: {max_size:,} bytes. Aborting.[/red]")
                return None
        
        # File exists and is valid
        console.print(f"[green]✅ File found: {file_path}[/green]")
        break
    
    if not file_path:
        return None
    
    # Get file info
    import os
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower()
    
    console.print(f"[dim]File: {file_name}[/dim]")
    console.print(f"[dim]Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)[/dim]")
    console.print(f"[dim]Type: {file_ext}[/dim]")
    
    # Validate file extension
    supported_extensions = ['.csv', '.json', '.xlsx', '.xls', '.txt']
    if file_ext not in supported_extensions:
        console.print(f"[yellow]⚠️  Warning: {file_ext} might not be supported. Supported types: {', '.join(supported_extensions)}[/yellow]")
        
        if not Prompt.ask(
            "[bold]Continue anyway?[/bold]", 
            choices=["yes", "no"], 
            default="no"
        ) == "yes":
            console.print("[yellow]File upload cancelled.[/yellow]")
            return None
    
    # Confirm upload
    if not Prompt.ask(
        f"[bold]Upload this file?[/bold]", 
        choices=["yes", "no"], 
        default="yes"
    ) == "yes":
        console.print("[yellow]File upload cancelled.[/yellow]")
        return None
    
    return {
        "file_path": file_path,
        "file_name": file_name
    }

def _get_input_with_validation(prompt, validator=None, error_msg="Invalid input", default=None, max_attempts=3):
    """Generic input validation helper"""
    for attempt in range(max_attempts):
        if default:
            value = Prompt.ask(f"{prompt} (default: {default})", default=default)
        else:
            value = Prompt.ask(prompt)
        
        if not validator or validator(value):
            return value
        
        remaining = max_attempts - attempt - 1
        if remaining > 0:
            console.print(f"[red]❌ {error_msg}. {remaining} attempts remaining.[/red]")
        else:
            console.print(f"[red]❌ {error_msg}. Maximum attempts exceeded.[/red]")
    
    return None


def _get_port_with_validation(db_type):
    """Get port with database-specific defaults"""
    default_ports = {
        'mysql': 3306,
        'postgresql': 5432,
        'sqlite': None,
        'oracle': 1521,
        'mssql': 1433
    }
    
    default_port = default_ports.get(db_type)
    
    for attempt in range(3):
        if default_port:
            port_input = Prompt.ask(f"[bold]Enter Port (default: {default_port})[/bold]", default=str(default_port))
        else:
            port_input = Prompt.ask("[bold]Enter Port[/bold]")
        
        try:
            port = int(port_input)
            if 1 <= port <= 65535:
                return port
            else:
                console.print("[red]❌ Port must be between 1 and 65535.[/red]")
        except ValueError:
            console.print("[red]❌ Port must be a valid number.[/red]")
        
        remaining = 3 - attempt - 1
        if remaining > 0:
            console.print(f"[yellow]{remaining} attempts remaining.[/yellow]")
    
    console.print("[red]❌ Invalid port. Using default if available.[/red]")
    return default_port


def _review_and_confirm(payload):
    """Display summary and get confirmation"""
    console.print("\n[bold blue]📋 Datasource Summary:[/bold blue]")
    
    # Group related fields for better readability
    sensitive_fields = ["password", "connection_url", "auth_token"]
    
    for key, value in payload.items():
        if key in sensitive_fields and value:
            console.print(f"  [dim]{key}:[/dim] [yellow]******[/yellow]")
        else:
            console.print(f"  [dim]{key}:[/dim] {value}")
    
    console.print()
    return Prompt.ask(
        "[bold]🤔 Create this datasource?[/bold]", 
        choices=["yes", "no"], 
        default="yes"
    ) == "yes"


def _create_datasource_with_error_handling(datasource_manager, payload):
    """Create datasource with comprehensive error handling and file upload support"""
    
    # Check if this is a file upload (datasource type 3)
    is_file_upload = payload.get("data_source_type_id") == 3
    
    if is_file_upload and "file_path" in payload:
        # Create a copy of the payload to avoid modifying the original
        upload_payload = payload.copy()
        
        # Extract file information but keep other fields
        file_path = upload_payload.pop("file_path")
        file_name = upload_payload.pop("file_name", None)
        
        # Call the datasource manager with file upload
        response = datasource_manager.create_datasource_with_file(upload_payload, file_path, file_name)
    else:
        # Regular datasource creation without file upload
        response = datasource_manager.create_datasource(payload)
    
    return response


def _display_created_datasource(response, datasource_manager=None):
    """Display the created datasource in an optimized format"""
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    
    # Check if this is a file upload response (different structure)
    is_file_upload = 'data_source_id' in response and 'file_info' in response
    
    if is_file_upload:
        _display_file_upload_response(response)
    else:
        _display_standard_datasource_response(response)


def _display_file_upload_response(response):
    """Display file upload datasource response"""
    from rich.table import Table
    from rich import box
    
    # Main success message
    console.print(f"\n[bold green]🎉 File Datasource Created Successfully![/bold green]")
    console.print(f"[bold blue]Datasource ID:[/bold blue] {response.get('data_source_id')}")
    console.print(f"[green]{response.get('message', '')}[/green]\n")
    
    # Create main info table
    main_table = Table(
        title="📊 Datasource Information",
        box=box.ROUNDED,
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta"
    )
    
    main_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    main_table.add_column("Value", style="white", width=40)
    
    # Add main datasource information
    main_table.add_row("Datasource ID", str(response.get('data_source_id', 'N/A')))
    main_table.add_row("Project ID", str(response.get('project_id', 'N/A')))
    main_table.add_row("Data Type", response.get('data_type', 'N/A'))
    main_table.add_row("Files Uploaded", str(response.get('files_uploaded', 0)))
    main_table.add_row("File Sources Created", str(response.get('file_sources_created', 0)))
    
    # Format total size
    total_size = response.get('total_size_bytes', 0)
    if total_size > 0:
        size_mb = total_size / (1024 * 1024)
        main_table.add_row("Total Size", f"{total_size:,} bytes ({size_mb:.2f} MB)")
    
    console.print(main_table)
    
    # Display file details
    file_info = response.get('file_info', [])
    if file_info:
        _display_uploaded_file_details(file_info)


def _display_uploaded_file_details(file_info):
    """Display uploaded file details"""
    from rich.table import Table
    from rich import box
    
    file_table = Table(
        title="📁 Uploaded File Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    file_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    file_table.add_column("Value", style="white", width=50)
    
    for i, file_detail in enumerate(file_info):
        if i > 0:
            file_table.add_row("", "")  # Add separator for multiple files
            
        file_table.add_row("Original Name", file_detail.get('original_name', 'N/A'))
        file_table.add_row("Stored Name", file_detail.get('stored_name', 'N/A'))
        file_table.add_row("Content Type", file_detail.get('content_type', 'N/A'))
        file_table.add_row("File Type", file_detail.get('file_type', 'N/A'))
        file_table.add_row("File Source ID", str(file_detail.get('file_source_id', 'N/A')))
        
        # Format file size
        size_bytes = file_detail.get('size_bytes', 0)
        if size_bytes > 0:
            size_mb = size_bytes / (1024 * 1024)
            file_table.add_row("File Size", f"{size_bytes:,} bytes ({size_mb:.2f} MB)")
        
        # Show storage path (masked for security)
        storage_path = file_detail.get('path', '')
        if storage_path:
            # Show only the filename part for security
            import os
            filename = os.path.basename(storage_path)
            file_table.add_row("Storage Location", f"[dim].../{filename}[/dim]")
    
    console.print(file_table)
    console.print("\n[dim]💡 Your file datasource is ready to use in data processing workflows.[/dim]")


def _display_standard_datasource_response(response):
    """Display standard datasource response (non-file uploads)"""
    from rich.table import Table
    from rich import box
    
    # Main datasource info
    console.print(f"\n[bold green]🎉 Datasource Created Successfully![/bold green]")
    console.print(f"[bold blue]Datasource ID:[/bold blue] {response.get('id')}")
    
    # Create main info table
    main_table = Table(
        title="📊 Datasource Information",
        box=box.ROUNDED,
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta"
    )
    
    main_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    main_table.add_column("Value", style="white", width=40)
    
    # Add main datasource information
    main_table.add_row("ID", str(response.get('id', 'N/A')))
    main_table.add_row("Description", response.get('description', 'N/A'))
    main_table.add_row("Source Type", response.get('source_type', 'N/A'))
    main_table.add_row("Data Source Type", str(response.get('data_source_type', 'N/A')))
    
    # Project information
    projects = response.get('projects', [])
    if projects:
        project_names = ", ".join([proj.get('name', 'Unknown') for proj in projects])
        main_table.add_row("Projects", project_names)
    
    console.print(main_table)
    
    # Display connection details based on type
    source_type = response.get('source_type', '').lower()
    
    if 'mysql' in source_type or 'database' in source_type:
        _display_database_details(response.get('db_details', {}))
    elif 'api' in source_type:
        _display_api_details(response.get('api_details', {}))
    elif 'file' in source_type:
        _display_file_details(response.get('file_details', {}))


def _display_database_details(db_details):
    """Display database connection details"""
    if not db_details:
        return
    
    db_table = Table(
        title="🗄️  Database Connection Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    db_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    db_table.add_column("Value", style="white", width=40)
    
    # Add database details (hide sensitive info)
    db_table.add_row("Database Type", db_details.get('db_type', 'N/A').upper())
    db_table.add_row("Host", db_details.get('host', 'N/A'))
    db_table.add_row("Port", str(db_details.get('port', 'N/A')))
    db_table.add_row("Database Name", db_details.get('db_name', 'N/A'))
    db_table.add_row("Table Name", db_details.get('db_table', 'N/A'))
    db_table.add_row("Username", db_details.get('user_name', 'N/A'))
    
    # Mask password and connection URL
    if db_details.get('password'):
        db_table.add_row("Password", "[yellow]••••••••[/yellow]")
    
    if db_details.get('connection_url'):
        # Show masked connection URL
        conn_url = db_details.get('connection_url', '')
        if '@' in conn_url:
            # Mask credentials in URL
            parts = conn_url.split('@')
            if len(parts) >= 2:
                masked_url = f"{parts[0].split('://')[0]}://[credentials]@{parts[1]}"
                db_table.add_row("Connection URL", f"[yellow]{masked_url}[/yellow]")
            else:
                db_table.add_row("Connection URL", "[yellow]••••••••[/yellow]")
        else:
            db_table.add_row("Connection URL", "[yellow]••••••••[/yellow]")
    
    console.print(db_table)


def _display_api_details(api_details):
    """Display API connection details"""
    if not api_details:
        return
    
    api_table = Table(
        title="🌐 API Connection Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    api_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    api_table.add_column("Value", style="white", width=40)
    
    api_table.add_row("API URL", api_details.get('api_url', 'N/A'))
    api_table.add_row("API Type", api_details.get('api_type', 'N/A'))
    
    # Mask auth token
    if api_details.get('auth_token'):
        api_table.add_row("Auth Token", "[yellow]••••••••[/yellow]")
    else:
        api_table.add_row("Auth Token", "Not provided")
    
    console.print(api_table)


def _display_file_details(file_details):
    """Display file connection details"""
    if not file_details:
        return
    
    file_table = Table(
        title="📁 File Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    file_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    file_table.add_column("Value", style="white", width=40)
    
    file_table.add_row("File Path", file_details.get('file_path_source', 'N/A'))
    file_table.add_row("File Type", file_details.get('file_type', 'N/A'))
    
    # Display metadata if available
    metadata = file_details.get('metadata')
    if metadata:
        if isinstance(metadata, dict):
            metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
        else:
            metadata_str = str(metadata)
        file_table.add_row("Metadata", metadata_str)
    else:
        file_table.add_row("Metadata", "None")
    
    console.print(file_table)

def _display_database_details(db_details):
    """Display database connection details"""
    if not db_details:
        return
    
    db_table = Table(
        title="🗄️  Database Connection Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    db_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    db_table.add_column("Value", style="white", width=40)
    
    # Add database details (hide sensitive info)
    db_table.add_row("Database Type", db_details.get('db_type', 'N/A').upper())
    db_table.add_row("Host", db_details.get('host', 'N/A'))
    db_table.add_row("Port", str(db_details.get('port', 'N/A')))
    db_table.add_row("Database Name", db_details.get('db_name', 'N/A'))
    db_table.add_row("Table Name", db_details.get('db_table', 'N/A'))
    db_table.add_row("Username", db_details.get('user_name', 'N/A'))
    
    # Mask password and connection URL
    if db_details.get('password'):
        db_table.add_row("Password", "[yellow]••••••••[/yellow]")
    
    if db_details.get('connection_url'):
        # Show masked connection URL
        conn_url = db_details.get('connection_url', '')
        if '@' in conn_url:
            # Mask credentials in URL
            parts = conn_url.split('@')
            if len(parts) >= 2:
                masked_url = f"{parts[0].split('://')[0]}://[credentials]@{parts[1]}"
                db_table.add_row("Connection URL", f"[yellow]{masked_url}[/yellow]")
            else:
                db_table.add_row("Connection URL", "[yellow]••••••••[/yellow]")
        else:
            db_table.add_row("Connection URL", "[yellow]••••••••[/yellow]")
    
    console.print(db_table)


def _display_api_details(api_details):
    """Display API connection details"""
    if not api_details:
        return
    
    api_table = Table(
        title="🌐 API Connection Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    api_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    api_table.add_column("Value", style="white", width=40)
    
    api_table.add_row("API URL", api_details.get('api_url', 'N/A'))
    api_table.add_row("API Type", api_details.get('api_type', 'N/A'))
    
    # Mask auth token
    if api_details.get('auth_token'):
        api_table.add_row("Auth Token", "[yellow]••••••••[/yellow]")
    else:
        api_table.add_row("Auth Token", "Not provided")
    
    console.print(api_table)


def _display_file_details(file_details):
    """Display file connection details"""
    if not file_details:
        return
    
    file_table = Table(
        title="📁 File Details",
        box=box.ROUNDED,
        title_style="bold green",
        show_header=True,
        header_style="bold blue"
    )
    
    file_table.add_column("Property", style="cyan", no_wrap=True, width=20)
    file_table.add_column("Value", style="white", width=40)
    
    file_table.add_row("File Path", file_details.get('file_path_source', 'N/A'))
    file_table.add_row("File Type", file_details.get('file_type', 'N/A'))
    
    # Display metadata if available
    metadata = file_details.get('metadata')
    if metadata:
        if isinstance(metadata, dict):
            metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
        else:
            metadata_str = str(metadata)
        file_table.add_row("Metadata", metadata_str)
    else:
        file_table.add_row("Metadata", "None")
    
    console.print(file_table)

# Alternative: Single comprehensive table
def _display_created_datasource_single_table(response):
    """Display the created datasource in a single comprehensive table"""
    from rich.table import Table
    from rich import box
    
    console.print(f"\n[bold green]🎉 Datasource ID {response.get('id')} Created Successfully![/bold green]")
    
    table = Table(
        title="📊 Datasource Summary",
        box=box.DOUBLE_EDGE,
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
        min_width=80
    )
    
    table.add_column("Category", style="bold cyan", no_wrap=True, width=18)
    table.add_column("Property", style="yellow", no_wrap=True, width=18)
    table.add_column("Value", style="white", width=44)
    
    # Basic info
    table.add_row("Basic Info", "ID", str(response.get('id', 'N/A')))
    table.add_row("", "Description", response.get('description', 'N/A'))
    table.add_row("", "Source Type", response.get('source_type', 'N/A'))
    table.add_row("", "Type ID", str(response.get('data_source_type', 'N/A')))
    
    # Project info
    projects = response.get('projects', [])
    if projects:
        project_names = ", ".join([proj.get('name', 'Unknown') for proj in projects])
        table.add_row("", "Projects", project_names)
    
    # Add separator
    table.add_row("", "", "")
    
    # Connection details based on type
    db_details = response.get('db_details', {})
    if db_details and any(db_details.values()):
        table.add_row("Database", "Type", db_details.get('db_type', 'N/A').upper())
        table.add_row("", "Host", db_details.get('host', 'N/A'))
        table.add_row("", "Port", str(db_details.get('port', 'N/A')))
        table.add_row("", "Database", db_details.get('db_name', 'N/A'))
        table.add_row("", "Table", db_details.get('db_table', 'N/A'))
        table.add_row("", "Username", db_details.get('user_name', 'N/A'))
        table.add_row("", "Password", "[yellow]••••••••[/yellow]" if db_details.get('password') else 'N/A')
    
    # API details
    api_details = response.get('api_details', {})
    if api_details and any(api_details.values()):
        table.add_row("API", "URL", api_details.get('api_url', 'N/A'))
        table.add_row("", "Type", api_details.get('api_type', 'N/A'))
        table.add_row("", "Auth Token", "[yellow]••••••••[/yellow]" if api_details.get('auth_token') else 'Not provided')
    
    # File details
    file_details = response.get('file_details', {})
    if file_details and any(v for v in file_details.values() if v is not None):
        table.add_row("File", "Path", file_details.get('file_path_source', 'N/A'))
        table.add_row("", "Type", file_details.get('file_type', 'N/A'))
        
        metadata = file_details.get('metadata')
        if metadata:
            if isinstance(metadata, dict):
                metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
            else:
                metadata_str = str(metadata)
            table.add_row("", "Metadata", metadata_str)
    
    console.print(table)
    console.print("\n[dim]💡 Your datasource is ready to use in data processing workflows.[/dim]")
    
    console.print(f"\n[bold green]🎉 Datasource ID {response.get('id')} created successfully![/bold green]")
    console.print("[dim]You can now use this datasource in your projects.[/dim]")

def _get_password_with_validation(base_manager, max_attempts=3):
    """Get password with validation"""
    for attempt in range(max_attempts):
        password = base_manager.masked_input("\n[bold]Enter password:[/bold] ")
        
        if password and password.strip():
            return password.strip()
        
        remaining = max_attempts - attempt - 1
        if remaining > 0:
            console.print(f"[red]❌ Password cannot be empty. {remaining} attempts remaining.[/red]")
        else:
            console.print("[red]❌ Password is required for database connection. Aborting.[/red]")
            return None
    
    return None

if __name__ == "__main__":
    data()