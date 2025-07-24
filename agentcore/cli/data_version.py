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
import json
from collections import defaultdict
import os
from datetime import datetime

from agentcore.managers.data_version_manager import DataversionManager, DataVersionManager2
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager

install()

console = Console()

@click.group()
def data_version():
    """data management commands."""
    pass


def beautify_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))  # Convert to datetime object
    return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format as 'YYYY-MM-DD HH:MM:SS'


@data_version.command(name='view')
@BaseManager.handle_api_error
def view_data_versions():
    """View all data versions with pagination (10 per page)."""

    dataversion_manager = DataversionManager()
    base_manager = BaseManager()
    response = dataversion_manager.get_all_dataversions()

    if not response:
        console.print("[yellow]No data versions found.[/yellow]")
        return

    # Format datetime
    for item in response:
        if 'created_at' in item:
            item['created_at'] = beautify_datetime(item['created_at'])
        if 'updated_at' in item:
            item['updated_at'] = beautify_datetime(item['updated_at'])

    # formatted_data = prepare_data_for_pagination(response)

    # Use the pagination function
    base_manager.paginate_data(
        data=response,
        columns=dataversion_manager.dataversion_details_columns,
        title_prefix='Data Versions List',
        row_formatter=TableDisplay().format_dataversion_row,
        page_size=10
    )


@data_version.command(name='get-data')
@BaseManager.handle_api_error
def fetch_data():
    """Fetch data of specific dataversion"""

    dataversion_id = Prompt.ask("[bold]Enter data version ID[/bold]")
    if not dataversion_id:
        console.print("[red]Data Version ID is required. Aborting operation.[/red]")
        return

    datasource_manager = DataversionManager()
    response = datasource_manager.data_fetch(dataversion_id)

    if not response:
        console.print("[yellow]No data found.[/yellow]")
        return
    console.print(f"[green]Data from data version {dataversion_id}:[/green]")
    # console.print(response)

    console.print(f"Total length: {len(response['data'])}")
    num_rows = Prompt.ask("[bold]Enter number of rows to display[/bold]", default="5")
    num_rows = int(num_rows)
    top_5_data = response.get("data", [])[:num_rows]

    # Dynamically extract column names from the first record in top_5_data
    if top_5_data:
        columns = [key.replace('_', ' ').upper() for key in top_5_data[0].keys()]
    else:
        columns = []

    console.print("[bold green]Fetched Data:[/bold green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': top_5_data},
        columns=columns,
        title_prefix="Fetched Data",
        row_formatter=table_display.format_datasource_row  # Create this method for formatting
    )

import click
import time
from rich.console import Console
from rich.table import Table
from rich.traceback import install
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
from datetime import datetime
import json


from agentcore.managers.datasource_manager import DatasourceManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager

install()

console = Console()

@click.group()
def dataversion():
    """Data version management commands."""
    pass


@data_version.command(name='fetch')
@BaseManager.handle_api_error
def fetch_initial_data():
    """Fetch data from a source and create an initial RAW data version"""
    datasource_manager = DatasourceManager()
    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data sources
    response = datasource_manager.view_datasources()
    
    if not response:
        console.print("[yellow]No datasources found. Please create a datasource first.[/yellow]")
        return
    
    # Display available datasources
    console.print("[bold green]Available Datasources:[/bold green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': response},
        columns=datasource_manager.datasource_columns,
        title_prefix="Datasource",
        row_formatter=table_display.format_datasource_row
    )
    
    # Step 2: Ask for data source ID
    data_source_id = Prompt.ask("[bold]Enter Data Source ID[/bold]")
    if not data_source_id:
        console.print("[red]Data Source ID is required. Aborting the operation.[/red]")
        return
    
    # Step 3: Ask if user wants to preview the data source first
    preview_first = Prompt.ask(
        "[bold]Do you want to preview the data source first?[/bold]", 
        choices=["y", "n"], 
        default="y"
    )
    
    if preview_first.lower() == "y":
        preview_response = data_version_manager.preview_data_source(data_source_id)
        if not preview_response:
            console.print("[yellow]Unable to preview data source.[/yellow]")
        else:
            # Display preview data
            console.print("[bold green]Data Preview:[/bold green]")
            
            # Print statistics
            stats = preview_response.get('stats', {})
            console.print(Panel(
                f"Total Rows: {stats.get('total_rows', 'N/A')}\n"
                f"Total Columns: {stats.get('total_columns', 'N/A')}",
                title="Data Statistics"
            ))
            
            # Create a table for the preview data
            preview_table = Table(title="Data Preview")
            
            # Add columns to the table
            columns = preview_response.get('columns', [])
            for column in columns:
                preview_table.add_column(column)
            
            # Add data rows to the table
            preview_data = preview_response.get('preview', [])
            for row in preview_data:
                preview_table.add_row(*[str(row.get(col, '')) for col in columns])
            
            console.print(preview_table)
    
    # Step 4: Ask for operations (optional)
    apply_operations = Prompt.ask(
        "[bold]Do you want to apply operations during fetch?[/bold]", 
        choices=["y", "n"], 
        default="n"
    )
    
    operations = []
    if apply_operations.lower() == "y":
        # Get available operations
        operations_response = data_version_manager.list_operations()
        
        if operations_response:
            console.print("[bold green]Available Operations:[/bold green]")
            operations_table = Table(title="Operations")
            operations_table.add_column("ID")
            operations_table.add_column("Name")
            operations_table.add_column("Description")
            operations_table.add_column("Type")
            
            for op in operations_response:
                operations_table.add_row(
                    str(op.get('id', '')),
                    op.get('name', ''),
                    op.get('description', ''),
                    op.get('operation_type', '')
                )
            
            console.print(operations_table)
            
            continue_adding = True
            while continue_adding:
                op_id = Prompt.ask("[bold]Enter Operation ID (or leave empty to finish)[/bold]")
                if not op_id:
                    continue_adding = False
                    continue
                
                # Get operation parameters and type
                op_params = {}
                op_type = None
                
                for op in operations_response:
                    if str(op.get('id', '')) == op_id:
                        op_type = op.get('operation_type')
                        
                        # Get required and optional parameters
                        required_params = json.loads(op.get('required_parameters', '[]'))
                        default_params = json.loads(op.get('default_parameters', '{}'))
                        
                        for param_name in required_params:
                            param_value = Prompt.ask(f"[bold]Enter value for {param_name}[/bold]")
                            if not param_value:
                                console.print(f"[red]Parameter {param_name} is required.[/red]")
                                continue
                                
                            # Handle special parameter types based on operation type
                            if op_type == "DROP" and param_name == "columns":
                                # Convert comma-separated string to list for columns parameter
                                param_value = [col.strip() for col in param_value.split(',')]
                            elif op_type == "RENAME" and param_name == "rename_dict":
                                # Handle rename dictionary format: "old_name:new_name,old_name2:new_name2"
                                rename_dict = {}
                                pairs = param_value.split(',')
                                for pair in pairs:
                                    if ':' in pair:
                                        old, new = pair.split(':', 1)
                                        rename_dict[old.strip()] = new.strip()
                                param_value = rename_dict
                            
                            op_params[param_name] = param_value
                        
                        # Optional parameters
                        for param_name, default_value in default_params.items():
                            if param_name not in required_params:
                                param_value = Prompt.ask(
                                    f"[bold]Enter value for {param_name} (optional)[/bold]",
                                    default=""
                                )
                                
                                if param_value:
                                    if op_type == "DROP" and param_name == "columns":
                                        # Convert comma-separated string to list for columns parameter
                                        param_value = [col.strip() for col in param_value.split(',')]
                                    elif op_type == "RENAME" and param_name == "rename_dict":
                                        # Handle rename dictionary format: "old_name:new_name,old_name2:new_name2"
                                        rename_dict = {}
                                        pairs = param_value.split(',')
                                        for pair in pairs:
                                            if ':' in pair:
                                                old, new = pair.split(':', 1)
                                                rename_dict[old.strip()] = new.strip()
                                        param_value = rename_dict
                                    
                                    op_params[param_name] = param_value
                
                if op_type:
                    # Add operation to the list with the proper format
                    # CHANGED: Use operation ID instead of operation type
                    operations.append({
                        'operation_id': int(op_id),  # Use the operation ID as an integer
                        'parameters': op_params
                    })
                    console.print(f"[green]Added operation: ID {op_id}[/green]")
                else:
                    console.print(f"[red]Could not find operation type for ID {op_id}[/red]")
                
                add_more = Prompt.ask(
                    "[bold]Add another operation?[/bold]", 
                    choices=["y", "n"], 
                    default="n"
                )
                continue_adding = add_more.lower() == "y"
    
    # Step 5: Confirm and initiate the fetch
    console.print("\n[bold]Fetch Summary:[/bold]")
    console.print(f"Data Source ID: {data_source_id}")
    console.print(f"Operations: {json.dumps(operations, indent=2) if operations else 'None'}")
    
    confirm = Prompt.ask(
        "\n[bold]Start data fetch?[/bold]", 
        choices=["yes", "no"], 
        default="yes"
    )
    
    if confirm.lower() == "no":
        console.print("[yellow]Data fetch cancelled.[/yellow]")
        return
    
    # Step 6: Start the fetch process
    fetch_response = data_version_manager.fetch_initial_data({
        'data_source_id': int(data_source_id),
        'operations': operations
    })
    
    if not fetch_response:
        console.print("[red]Failed to initiate data fetch.[/red]")
        return
    
    version_id = fetch_response.get('version_id')
    task_id = fetch_response.get('task_id')
    
    console.print(f"[green]Data fetch initiated:[/green]")
    console.print(f"Version ID: {version_id}")
    console.print(f"Task ID: {task_id}")
    
    # Step 7: Poll the task status
    console.print("\n[bold]Monitoring task progress...[/bold]")
    completed = False
    
    with console.status("[bold green]Processing...[/bold green]") as status:
        while not completed:
            time.sleep(2)  # Poll every 2 seconds
            task_status = data_version_manager.get_task_status(task_id)
            
            if not task_status:
                console.print("[yellow]Could not retrieve task status. Retrying...[/yellow]")
                continue
                
            status_value = task_status.get('status', '')
            console.print(f"Status: {status_value}")
            
            # Check if task is complete - convert to uppercase for comparison
            if status_value.upper() in ['COMPLETED', 'FAILED', 'ERROR']:
                # Exit the polling loop
                completed = True
                # Break out of the while loop explicitly
                break
                
    # Process the final status outside the polling loop
    if task_status and status_value.upper() == 'COMPLETED':
        console.print("[bold green]✓ Data fetch completed successfully![/bold green]")
        
        # Display result information
        result = task_status.get('result', {})
        if result:
            console.print("[bold green]Fetch Result:[/bold green]")
            console.print(Panel(
                f"Total Rows: {result.get('rows', 'N/A')}\n"
                f"Status: {result.get('status', 'N/A')}\n"
                f"Columns: {', '.join(result.get('columns', []))}\n"
                f"Version ID: {result.get('version_id', 'N/A')}",
                title="Result Details"
            ))
        
        # Preview the data version
        preview_version = Prompt.ask(
            "[bold]Do you want to preview the data version?[/bold]", 
            choices=["y", "n"], 
            default="y"
        )
        
        if preview_version.lower() == "y":
            # Get version_id from the result if available
            result_version_id = result.get('version_id', version_id)
            preview_response = data_version_manager.preview_data_version(result_version_id)
            
            if preview_response:
                # Display preview data
                console.print("[bold green]Data Version Preview:[/bold green]")
                
                # Print statistics
                stats = preview_response.get('stats', {})
                console.print(Panel(
                    f"Total Rows: {stats.get('total_rows', 'N/A')}\n"
                    f"Total Columns: {stats.get('total_columns', 'N/A')}",
                    title="Data Statistics"
                ))
                
                # Create a table for the preview data
                preview_table = Table(title="Data Preview")
                
                # Add columns to the table
                columns = preview_response.get('columns', [])
                for column in columns:
                    preview_table.add_column(column)
                
                # Add data rows to the table
                preview_data = preview_response.get('preview', [])
                for row in preview_data:
                    preview_table.add_row(*[str(row.get(col, '')) for col in columns])
                
                console.print(preview_table)
    elif task_status:
        console.print(f"[bold red]✗ Data fetch failed: {task_status.get('message', 'Unknown error')}[/bold red]")


@data_version.command(name='transform')
@BaseManager.handle_api_error
def transform_data_version():
    """Transform an existing data version by applying operations and create a new version"""
    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data versions
    console.print("[bold green]Fetching available data versions...[/bold green]")
    
    # Ask for specific data source ID to filter versions
    filter_by_source = Prompt.ask(
        "[bold]Do you want to filter versions by data source ID?[/bold]", 
        choices=["y", "n"], 
        default="n"
    )
    
    data_source_id = None
    if filter_by_source.lower() == "y":
        # First list available datasources
        datasource_manager = DatasourceManager()
        sources = datasource_manager.view_datasources()
        
        if sources:
            console.print("[bold green]Available Datasources:[/bold green]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': sources},
                columns=datasource_manager.datasource_columns,
                title_prefix="Datasource",
                row_formatter=table_display.format_datasource_row
            )
            
            data_source_id = Prompt.ask("[bold]Enter Data Source ID[/bold]")
    
    # Get versions (filtered by source if applicable)
    versions = data_version_manager.list_data_versions(data_source_id)
    
    if not versions:
        console.print("[yellow]No data versions found. Please fetch data first.[/yellow]")
        return
    
    # Display available versions
    console.print("[bold green]Available Data Versions:[/bold green]")
    version_table = Table(title="Data Versions")
    version_table.add_column("ID")
    version_table.add_column("Data Source Description")  # Changed column name for clarity
    version_table.add_column("Created By")
    version_table.add_column("Updated By")
    version_table.add_column("Created At")
    version_table.add_column("Updated At")

    for version in versions:
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
            data_source_str,  # Use formatted string
            version.get('created_by', ''),
            version.get('updated_by', ''),
            created_at,
            updated_at,
        )

    console.print(version_table)
    
    # Step 2: Select source version ID
    source_version_id = Prompt.ask("[bold]Enter Source Version ID[/bold]")
    if not source_version_id:
        console.print("[red]Source Version ID is required. Aborting the operation.[/red]")
        return
    
    # Step 3: Preview the source version
    preview_first = Prompt.ask(
        "[bold]Do you want to preview the source version?[/bold]", 
        choices=["y", "n"], 
        default="y"
    )
    
    if preview_first.lower() == "y":
        preview_response = data_version_manager.preview_data_version(source_version_id)
        if not preview_response:
            console.print("[yellow]Unable to preview data version.[/yellow]")
        else:
            # Display preview data
            console.print("[bold green]Source Version Preview:[/bold green]")
            
            # Print statistics
            stats = preview_response.get('stats', {})
            console.print(Panel(
                f"Total Rows: {stats.get('total_rows', 'N/A')}\n"
                f"Total Columns: {stats.get('total_columns', 'N/A')}",
                title="Data Statistics"
            ))
            
            # Create a table for the preview data
            preview_table = Table(title="Data Preview")
            
            # Add columns to the table
            columns = preview_response.get('columns', [])
            for column in columns:
                preview_table.add_column(column)
            
            # Add data rows to the table
            preview_data = preview_response.get('preview', [])
            for row in preview_data:
                preview_table.add_row(*[str(row.get(col, '')) for col in columns])
            
            console.print(preview_table)
    
    # Step 4: Set up operations
    console.print("[bold]Setting up transformation operations[/bold]")
    operations = []
    
    # Get available operations
    operations_response = data_version_manager.list_operations()
    
    if not operations_response:
        console.print("[yellow]No operations available.[/yellow]")
        return
    
    console.print("[bold green]Available Operations:[/bold green]")
    operations_table = Table(title="Operations")
    operations_table.add_column("ID")
    operations_table.add_column("Name")
    operations_table.add_column("Description")
    operations_table.add_column("Type")
    operations_table.add_column("Required Params")
    
    for op in operations_response:
        required_params = op.get('required_parameters', '[]')
        operations_table.add_row(
            str(op.get('id', '')),
            op.get('name', ''),
            op.get('description', ''),
            op.get('operation_type', ''),
            required_params
        )
    
    console.print(operations_table)
    
    # Add operations
    continue_adding = True
    while continue_adding:
        op_id = Prompt.ask("[bold]Enter Operation ID (or leave empty to finish)[/bold]")
        if not op_id:
            continue_adding = False
            continue
        
        # Get operation parameters and type
        op_params = {}
        selected_op = None
        
        for op in operations_response:
            if str(op.get('id', '')) == op_id:
                selected_op = op
                break
        
        if selected_op:
            op_type = selected_op.get('operation_type')
            # Get required and optional parameters
            required_params = json.loads(selected_op.get('required_parameters', '[]'))
            default_params = json.loads(selected_op.get('default_parameters', '{}'))
            
            # Handle special cases for common operations
            if op_type == "DROP":
                columns_value = Prompt.ask("[bold]Enter column(s) to drop (comma-separated)[/bold]")
                op_params["columns"] = [col.strip() for col in columns_value.split(',')]
            elif op_type == "RENAME":
                rename_value = Prompt.ask("[bold]Enter rename mappings (format: old_name:new_name,old_name2:new_name2)[/bold]")
                rename_dict = {}
                pairs = rename_value.split(',')
                for pair in pairs:
                    if ':' in pair:
                        old, new = pair.split(':', 1)
                        rename_dict[old.strip()] = new.strip()
                op_params["rename_dict"] = rename_dict
            else:
                # Generic parameter handling for other operation types
                for param_name in required_params:
                    param_value = Prompt.ask(f"[bold]Enter value for {param_name}[/bold]")
                    if not param_value:
                        console.print(f"[red]Parameter {param_name} is required.[/red]")
                        continue
                    
                    # Try to convert to appropriate type if possible
                    if param_name == "columns" and param_value:
                        # Convert comma-separated string to list for columns parameter
                        op_params[param_name] = [col.strip() for col in param_value.split(',')]
                    else:
                        op_params[param_name] = param_value
                
                # Optional parameters from default params
                for param_name, default_value in default_params.items():
                    if param_name not in required_params and param_name not in op_params:
                        param_value = Prompt.ask(
                            f"[bold]Enter value for {param_name} (optional)[/bold]",
                            default=""
                        )
                        
                        if param_value:
                            # Try to convert to appropriate type
                            if param_name == "columns" and param_value:
                                op_params[param_name] = [col.strip() for col in param_value.split(',')]
                            else:
                                op_params[param_name] = param_value
            
            # Add operation to the list with the proper format using the ID instead of type
            operations.append({
                'operation_id': int(op_id),
                'parameters': op_params
            })
            console.print(f"[green]Added operation: ID {op_id} with parameters: {json.dumps(op_params)}[/green]")
        else:
            console.print(f"[red]Could not find operation with ID {op_id}[/red]")
        
        add_more = Prompt.ask(
            "[bold]Add another operation?[/bold]", 
            choices=["y", "n"], 
            default="n"
        )
        continue_adding = add_more.lower() == "y"
    
    # Step 5: Confirm and initiate the transformation
    if not operations:
        console.print("[red]No operations specified. At least one operation is required.[/red]")
        return
    
    console.print("\n[bold]Transformation Summary:[/bold]")
    console.print(f"Source Version ID: {source_version_id}")
    console.print(f"Operations: {json.dumps(operations, indent=2)}")
    
    confirm = Prompt.ask(
        "\n[bold]Start data transformation?[/bold]", 
        choices=["yes", "no"], 
        default="yes"
    )
    
    if confirm.lower() == "no":
        console.print("[yellow]Data transformation cancelled.[/yellow]")
        return
    
    # Step 6: Start the transformation process
    transform_response = data_version_manager.transform_data_version({
        'source_version_id': int(source_version_id),
        'operations': operations
    })
    
    if not transform_response:
        console.print("[red]Failed to initiate data transformation.[/red]")
        return
    
    source_version_id = transform_response.get('source_version_id')
    target_version_id = transform_response.get('target_version_id')
    task_id = transform_response.get('task_id')
    
    console.print(f"[green]Data transformation initiated:[/green]")
    console.print(f"Source Version ID: {source_version_id}")
    console.print(f"Target Version ID: {target_version_id}")
    console.print(f"Task ID: {task_id}")
    
    # Step 7: Poll the task status
    console.print("\n[bold]Monitoring transformation progress...[/bold]")
    completed = False
    with console.status("[bold green]Processing...[/bold green]") as status:
        while not completed:
            time.sleep(2)  # Poll every 2 seconds
            task_status = data_version_manager.get_task_status(task_id)
            if not task_status:
                console.print("[yellow]Could not retrieve task status. Retrying...[/yellow]")
                continue
            
            status_value = task_status.get('status', '')
            console.print(f"Status: {status_value}")
            
            # Check if task is complete - convert to uppercase for comparison
            if status_value.upper() in ['COMPLETED', 'FAILED', 'ERROR']:
                # Exit the polling loop
                completed = True
                # Break out of the while loop explicitly
                break

    # Process the final status outside the polling loop
    if task_status and status_value.upper() == 'COMPLETED':
        console.print("[bold green]✓ Data transformation completed successfully![/bold green]")
        # Display result information
        result = task_status.get('result', {})
        if result:
            console.print("[bold green]Transformation Result:[/bold green]")
            console.print(Panel(
                f"Total Rows: {result.get('rows', 'N/A')}\n"
                f"Status: {result.get('status', 'N/A')}\n"
                f"Columns: {', '.join(result.get('columns', []))}\n"
                f"Version ID: {result.get('version_id', 'N/A')}",
                title="Result Details"
            ))
        
        # Preview the transformed version
        preview_version = Prompt.ask(
            "[bold]Do you want to preview the transformed version?[/bold]",
            choices=["y", "n"],
            default="y"
        )
        
        if preview_version.lower() == "y":
            # Get version_id from the result if available
            result_version_id = result.get('version_id', target_version_id)
            preview_response = data_version_manager.preview_data_version(result_version_id)
            
            if preview_response:
                # Display preview data
                console.print("[bold green]Transformed Version Preview:[/bold green]")
                # Print statistics
                stats = preview_response.get('stats', {})
                console.print(Panel(
                    f"Total Rows: {stats.get('total_rows', 'N/A')}\n"
                    f"Total Columns: {stats.get('total_columns', 'N/A')}",
                    title="Data Statistics"
                ))
                
                # Create a table for the preview data
                preview_table = Table(title="Data Preview")
                # Add columns to the table
                columns = preview_response.get('columns', [])
                for column in columns:
                    preview_table.add_column(column)
                # Add data rows to the table
                preview_data = preview_response.get('preview', [])
                for row in preview_data:
                    preview_table.add_row(*[str(row.get(col, '')) for col in columns])
                console.print(preview_table)
    elif task_status:
        console.print(f"[bold red]✗ Data transformation failed: {task_status.get('message', 'Unknown error')}[/bold red]")


@data_version.command(name='diagnose')
@BaseManager.handle_api_error
def diagnose_data_version():
    """Diagnose data quality issues from an existing data version"""
    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data versions
    console.print("[bold green]Fetching available data versions...[/bold green]")
    
    # Ask for specific data source ID to filter versions
    filter_by_source = Prompt.ask(
        "[bold]Do you want to filter versions by data source ID?[/bold]", 
        choices=["y", "n"], 
        default="n"
    )
    
    data_source_id = None
    if filter_by_source.lower() == "y":
        # First list available datasources
        datasource_manager = DatasourceManager()
        sources = datasource_manager.view_datasources()
        
        if sources:
            console.print("[bold green]Available Datasources:[/bold green]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': sources},
                columns=datasource_manager.datasource_columns,
                title_prefix="Datasource",
                row_formatter=table_display.format_datasource_row
            )
            
            data_source_id = Prompt.ask("[bold]Enter Data Source ID[/bold]")
    
    # Get versions (filtered by source if applicable)
    versions = data_version_manager.list_data_versions(data_source_id)
    
    if not versions:
        console.print("[yellow]No data versions found. Please fetch data first.[/yellow]")
        return
    
    # Display available versions
    console.print("[bold green]Available Data Versions:[/bold green]")
    version_table = Table(title="Data Versions")
    version_table.add_column("ID")
    version_table.add_column("Data Source")  # Changed from "Source ID"
    version_table.add_column("Created By")
    version_table.add_column("Updated By")   # Added missing column
    version_table.add_column("Created At")
    version_table.add_column("Updated At")   # Added missing column

    for version in versions:
        created_at = version.get('created_at', '')
        if created_at:
            created_at = beautify_datetime(created_at)
        
        updated_at = version.get('updated_at', '')
        if updated_at:
            updated_at = beautify_datetime(updated_at)
        
        version_table.add_row(
            str(version.get('id', '')),
            str(version.get('data_source', '')),        # Changed from 'data_source_id'
            version.get('created_by', ''),
            version.get('updated_by', ''),              # Added missing field
            created_at,
            updated_at,                                 # Added missing field
        )

    console.print(version_table)
    
    # Step 2: Select version ID to diagnose
    version_id = Prompt.ask("[bold]Enter Version ID to diagnose[/bold]")
    if not version_id:
        console.print("[red]Version ID is required. Aborting the operation.[/red]")
        return
    
    # Step 3: Run diagnosis
    console.print(f"[bold green]Running data quality diagnosis for version {version_id}...[/bold green]")
    
    with console.status("[bold green]Analyzing data quality...[/bold green]") as status:
        diagnosis_response = data_version_manager.diagnose_data_version(version_id)
    
    if not diagnosis_response:
        console.print("[red]Failed to diagnose data version.[/red]")
        return
    
    console.print("[bold green]Data Quality Diagnosis Results:[/bold green]")

    # Step 4: Display diagnosis result
    quality_score = diagnosis_response.get('data_quality_score', 0)
    summary = diagnosis_response.get('summary', 'Not available')
    recommendations = diagnosis_response.get('recommendations', [])
    quality_metrics = diagnosis_response.get('quality_metrics', {})

    # Step 5: Print overall score and summary
    console.print(Panel(
        f"[bold]Quality Score:[/bold] {quality_score:.2f}/100\n"
        f"[bold]Summary:[/bold] {summary}",
        title="Overall Quality Summary",
        border_style="green"
    ))

    # Step 6: Display quality metrics in table form
    if quality_metrics:
        metrics_table = Table(title="Column-wise Quality Metrics", show_lines=True)
        metrics_table.add_column("Column")
        metrics_table.add_column("Missing %")
        metrics_table.add_column("Unique Count")
        metrics_table.add_column("Zero Count", justify="right")
        metrics_table.add_column("Negative Count", justify="right")
        metrics_table.add_column("Outlier Ratio", justify="right")

        for col, metrics in quality_metrics.items():
            metrics_table.add_row(
                col,
                f"{metrics.get('missing_percentage', 0):.2f}%",
                str(metrics.get('unique_count', 'N/A')),
                str(metrics.get('zero_count', 'N/A')),
                str(metrics.get('negative_count', 'N/A')),
                f"{metrics.get('outlier_ratio', 0):.2f}"
            )
        console.print(metrics_table)
    else:
        console.print("[italic]No quality metrics available.[/italic]")

    # Step 7: Show recommendations
    if recommendations:
        console.print(Panel(
            "\n".join(f"- {rec}" for rec in recommendations),
            title="Recommendations",
            border_style="yellow"
        ))
    else:
        console.print("[italic]No recommendations available.[/italic]")
    
    # Recommendations
    recommendations = diagnosis_response.get('recommendations', [])
    if recommendations:
        console.print("[bold]Recommendations:[/bold]")
        for i, rec in enumerate(recommendations, 1):
            console.print(f"{i}. {rec}")
    
    # Quality metrics
    metrics = diagnosis_response.get('quality_metrics', {})
    
    # Completeness
    completeness = metrics.get('completeness', {})
    console.print(Panel(
        f"[bold]Overall Completeness:[/bold] {completeness.get('overall_completeness', 0):.2f}%",
        title="Completeness",
        border_style="blue"
    ))
    
    # Display columns with completeness issues
    columns_with_issues = []
    for col, details in completeness.get('columns', {}).items():
        if 'issue' in details:
            columns_with_issues.append((col, details['null_percentage'], details['recommendation']))
    
    if columns_with_issues:
        console.print("[bold]Columns with Missing Values:[/bold]")
        issues_table = Table()
        issues_table.add_column("Column")
        issues_table.add_column("Missing %")
        issues_table.add_column("Recommendation")
        
        for col, percent, rec in columns_with_issues:
            issues_table.add_row(col, f"{percent:.2f}%", rec)
        
        console.print(issues_table)
    
    # Consistency
    consistency = metrics.get('consistency', {})
    duplicate_rows = consistency.get('duplicate_rows', {})
    if duplicate_rows.get('count', 0) > 0:
        console.print(Panel(
            f"[bold]Duplicate Rows:[/bold] {duplicate_rows.get('count', 0)}\n"
            f"[bold]Percentage:[/bold] {duplicate_rows.get('percentage', 0):.2f}%\n"
            f"[bold]Recommendation:[/bold] {duplicate_rows.get('recommendation', 'N/A')}",
            title="Consistency Issues",
            border_style="yellow"
        ))
    
    # Validity
    validity = metrics.get('validity', {})
    if validity:
        console.print("[bold]Validity Issues:[/bold]")
        validity_table = Table()
        validity_table.add_column("Column")
        validity_table.add_column("Issue Type")
        validity_table.add_column("Details")
        
        for col, details in validity.items():
            if 'issues' in details:
                issues = ", ".join(details['issues'])
                recommendation = details.get('recommendation', 'N/A')
                validity_table.add_row(col, issues, recommendation)
        
        console.print(validity_table)
    
    # Distribution issues
    distribution = metrics.get('distribution_issues', {})
    if distribution:
        console.print("[bold]Distribution Issues:[/bold]")
        dist_table = Table()
        dist_table.add_column("Column")
        dist_table.add_column("Dominant Value")
        dist_table.add_column("Percentage")
        dist_table.add_column("Recommendation")
        
        for col, details in distribution.items():
            dominant = details.get('dominant_value', 'N/A')
            percentage = details.get('dominant_percentage', 0)
            recommendation = details.get('recommendation', 'N/A')
            dist_table.add_row(col, str(dominant), f"{percentage:.2f}%", recommendation)
        
        console.print(dist_table)
    
    # Offer to preview the diagnosed version
    preview_version = Prompt.ask(
        "[bold]Do you want to preview this data version?[/bold]", 
        choices=["y", "n"], 
        default="n"
    )
    
    if preview_version.lower() == "y":
        preview_response = data_version_manager.preview_data_version(version_id)
        
        if preview_response:
            # Display preview data
            console.print("[bold green]Data Version Preview:[/bold green]")
            
            # Create a table for the preview data
            preview_table = Table(title="Data Preview")
            
            # Add columns to the table
            columns = preview_response.get('columns', [])
            for column in columns:
                preview_table.add_column(column)
            
            # Add data rows to the table
            preview_data = preview_response.get('preview', [])
            for row in preview_data:
                preview_table.add_row(*[str(row.get(col, '')) for col in columns])
            
            console.print(preview_table)


def beautify_datetime(dt_str):
    """Convert ISO format datetime to a more readable format"""
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))  # Convert to datetime object
    return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format as 'YYYY-MM-DD HH:MM:SS'


@data_version.command(name="history")
@BaseManager.handle_api_error
def history_data_version():
    """View the history (ancestry and descendants) of a data version"""
    data_version_manager = DataVersionManager2()

    # Step 1: List available data versions
    console.print("[bold green]Fetching available data versions...[/bold green]")

    # Ask for specific data source ID to filter versions
    filter_by_source = Prompt.ask(
        "[bold]Do you want to filter versions by data source ID?[/bold]",
        choices=["y", "n"],
        default="n"
    )

    data_source_id = None
    if filter_by_source.lower() == "y":
        # List available datasources
        datasource_manager = DatasourceManager()
        sources = datasource_manager.view_datasources()

        if sources:
            console.print("[bold green]Available Datasources:[/bold green]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': sources},
                columns=datasource_manager.datasource_columns,
                title_prefix="Datasource",
                row_formatter=table_display.format_datasource_row
            )

            data_source_id = Prompt.ask("[bold]Enter Data Source ID[/bold]")

    # Get versions (filtered by source if applicable)
    versions = data_version_manager.list_data_versions(data_source_id)

    if not versions:
        console.print("[yellow]No data versions found. Please fetch data first.[/yellow]")
        return

    # Display available versions
    console.print("[bold green]Available Data Versions:[/bold green]")
    version_table = Table(title="Data Versions")
    version_table.add_column("ID")
    version_table.add_column("Source ID")
    version_table.add_column("Created By")
    version_table.add_column("Created At")
    version_table.add_column("Status")

    for version in versions:
        created_at = version.get('created_at', '')
        if created_at:
            created_at = beautify_datetime(created_at)

        version_table.add_row(
            str(version.get('id', '')),
            str(version.get('data_source_id', '')),
            version.get('created_by', ''),
            created_at,
            version.get('status', '')
        )

    console.print(version_table)

    # Step 2: Select version ID to view history
    version_id = Prompt.ask("[bold]Enter Version ID to view its history[/bold]")
    if not version_id:
        console.print("[red]Version ID is required. Aborting the operation.[/red]")
        return

    # Step 3: Fetch history
    console.print(f"[bold green]Fetching history for version {version_id}...[/bold green]")

    with console.status("[bold green]Fetching data version history...[/bold green]") as status:
        history_response = data_version_manager.view_data_version_history(version_id)

    if not history_response:
        console.print("[red]Failed to fetch data version history.[/red]")
        return

    # Step 4: Display version history
    console.print("[bold green]Data Version History:[/bold green]")

    # Version Details
    created_at = beautify_datetime(history_response.get('created_at', ''))
    console.print(Panel(
        f"[bold]Version ID:[/bold] {history_response.get('version_id', 'N/A')}\n"
        f"[bold]Data Source ID:[/bold] {history_response.get('data_source_id', 'N/A')}\n"
        f"[bold]Created By:[/bold] {history_response.get('created_by', 'N/A')}\n"
        f"[bold]Created At:[/bold] {created_at}",
        title="Version Details",
        border_style="green"
    ))

    # Ancestry
    ancestry = history_response.get('ancestry', [])
    if ancestry:
        console.print("[bold]Ancestry Transformations:[/bold]")
        for ancestor in ancestry:
            ancestor_created_at = beautify_datetime(ancestor.get('created_at', ''))
            ancestor_panel = Panel(
                f"[bold]Transformation ID:[/bold] {ancestor.get('transformation_id', 'N/A')}\n"
                f"[bold]Source Version ID:[/bold] {ancestor.get('source_version_id', 'N/A')}\n"
                f"[bold]Status:[/bold] {ancestor.get('status', 'N/A')}\n"
                f"[bold]Created At:[/bold] {ancestor_created_at}",
                title=f"Ancestry - Transformation {ancestor.get('transformation_id')}",
                border_style="blue"
            )
            console.print(ancestor_panel)

            # Steps inside this transformation
            steps = ancestor.get('steps', [])
            if steps:
                steps_table = Table(title=f"Steps for Transformation {ancestor.get('transformation_id')}")
                steps_table.add_column("Order", justify="center")
                steps_table.add_column("Operation")
                steps_table.add_column("Type")
                steps_table.add_column("Stage")
                steps_table.add_column("Parameters")

                for step in steps:
                    parameters_str = json.dumps(step.get('parameters', {}), indent=2)
                    steps_table.add_row(
                        str(step.get('order', '')),
                        step.get('operation', ''),
                        step.get('type', ''),
                        step.get('stage', ''),
                        parameters_str
                    )
                console.print(steps_table)
    else:
        console.print("[yellow]No ancestry transformations found.[/yellow]")

    # Descendants
    descendants = history_response.get('descendants', [])
    if descendants:
        console.print("[bold]Descendant Versions:[/bold]")
        descendants_table = Table(title="Descendant Versions")
        descendants_table.add_column("Transformation ID")
        descendants_table.add_column("Target Version ID")
        descendants_table.add_column("Status")
        descendants_table.add_column("Created At")

        for descendant in descendants:
            descendant_created_at = beautify_datetime(descendant.get('created_at', ''))
            descendants_table.add_row(
                str(descendant.get('transformation_id', '')),
                str(descendant.get('target_version_id', '')),
                descendant.get('status', ''),
                descendant_created_at
            )
        console.print(descendants_table)
    else:
        console.print("[yellow]No descendant versions found.[/yellow]")


@data_version.command(name="operations")
@BaseManager.handle_api_error
def list_operations():
    """Fetch and display all available operations."""
    operations_manager = DataVersionManager2()
    
    console.print("[bold blue]Fetching available operations...[/bold blue]\n")
    
    # Fetch operations from API
    operations = operations_manager.get_operations()
    
    if not operations:
        console.print("[yellow]No operations found.[/yellow]")
        return
    
    # Display results in table format
    display_operations_table(operations)

def display_operations_table(operations):
    """Display operations in a formatted table."""
    table = Table(title="Available Operations", show_header=True, header_style="bold cyan")
    
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="bold")
    table.add_column("Stage", style="blue")
    table.add_column("Type", style="green")
    table.add_column("Description", style="white", max_width=40)
    table.add_column("Required Parameters", style="yellow", max_width=30)
    
    for operation in operations:
        # Parse required parameters for better display
        required_params = operation.get('required_parameters', '[]')
        if isinstance(required_params, str):
            try:
                required_params = json.loads(required_params)
            except json.JSONDecodeError:
                required_params = []
        
        params_display = ", ".join(required_params) if required_params else "None"
        
        table.add_row(
            str(operation.get('id', '')),
            operation.get('name', ''),
            operation.get('stage', ''),
            operation.get('operation_type', ''),
            operation.get('description', ''),
            params_display
        )
    
    console.print(table)
    console.print(f"\n[dim]Total operations: {len(operations)}[/dim]")


if __name__ == "__main__":
    data_version()