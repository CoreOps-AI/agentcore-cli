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
from rich.prompt import Prompt, Confirm
from typing import Optional
from datetime import datetime
import json
import time

from agentcore.managers.datasource_manager import DatasourceManager
from agentcore.managers.data_version_manager import DataVersionManager2

from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list
from agentcore.cli.data.main import data
from agentcore.cli.data.main import beautify_datetime
from agentcore.cli.data.main import get_datasource_search_list
install()

console = Console()

@data.command(name='transform')
@BaseManager.handle_api_error
def transform_data_version():
    """Transform an existing data version by applying operations and create a new version"""
    data_version_manager = DataVersionManager2()
    base_manager = BaseManager()
    # Step 1: List available data versions
    console.print("\n[bold blue]Select available data source...[/bold blue]")
    
    # Ask for specific data source ID to filter versions
    # filter_by_source = Prompt.ask(
    #     "[bold]Do you want to filter versions by data source ID?[/bold]", 
    #     choices=["y", "n"], 
    #     default="n"
    # )
    
    data_source_id = None
    # if filter_by_source.lower() == "y":
    #     # First list available datasources
    datasource_manager = DatasourceManager()
    sources = get_datasource_search_list()
    data_source_id = sources.get('id') if sources else None
    print(f"Selected Data Source ID: {data_source_id}")
    # Get versions (filtered by source if applicable)
    data_type = sources.get('data_type_name')
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
    dataversion_id, dataversion = None, None
    while not dataversion:
        dataversion_id = Prompt.ask("[bold]Enter ID from above table[/bold]")
        for version in versions:
            if str(dataversion_id) == str(version['id']):
                dataversion = version
                break
        if not dataversion:
            console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")
    
    # Step 3: Preview the source version
    preview_first = Prompt.ask(
        "[bold]Do you want to preview the source version?[/bold]", 
        choices=["y", "n"], 
        default="y"
    )

    source_version_id = dataversion_id
    preview_response = data_version_manager.preview_data_version(source_version_id)
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

    # Render operations table
    operations_table = Table(title="Operations")
    operations_table.add_column("ID", justify="center")
    operations_table.add_column("Name", justify="center")
    operations_table.add_column("Description", justify="left")
    operations_table.add_column("Type", justify="center")
    operations_table.add_column("Required Params", justify="center")

    for op in operations_response:
        if op.get('data_type_name') == data_type:
            required_params = op.get('required_parameters', '[]')
            
            # Check if it's already a string. If not, parse it using json.loads()
            if isinstance(required_params, str):
                try:
                    required_params = json.loads(required_params)
                except json.JSONDecodeError:
                    pass  # If decoding fails, keep it as is
            
            operations_table.add_row(
                str(op.get('id', '')),
                op.get('name', ''),
                op.get('description', ''),
                op.get('operation_type', ''),
                json.dumps(required_params) if isinstance(required_params, list) else str(required_params)  # Convert to string if it's a list, else keep as string
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
            
            # Handle required parameters
            required_params_raw = selected_op.get('required_parameters', '[]')
            if isinstance(required_params_raw, str):
                try:
                    required_params = json.loads(required_params_raw)
                except json.JSONDecodeError:
                    required_params = []  # Fallback to empty list if JSON decoding fails
            else:
                required_params = required_params_raw
            
            # Handle default parameters
            default_params_raw = selected_op.get('default_parameters', '{}')
            if isinstance(default_params_raw, str):
                try:
                    default_params = json.loads(default_params_raw)
                except json.JSONDecodeError:
                    default_params = {}  # Fallback to empty dictionary if JSON decoding fails
            else:
                default_params = default_params_raw
            
            # Handle special cases for common operations
            if op_type == "DROP":
                available_columns = preview_response['columns']
                console.print("[bold]Enter column(s) to drop (comma-separated). Use Tab to autocomplete one at a time.[/bold]")
                columns_value = ""
                selected_columns = []

                while True:
                    col = base_manager.get_input_with_tab_completion("Column", available_columns)
                    if col not in available_columns:
                        console.print(f"[red]'{col}' is not a valid column. Please choose from the available options.[/red]")
                        continue
                    if col in selected_columns:
                        console.print(f"[yellow]'{col}' is already selected. Skipping duplicate.[/yellow]")
                    else:
                        selected_columns.append(col)

                    # Ask if user wants to add more columns
                    add_more = Confirm.ask("Add another column?", default=False)
                    if not add_more:
                        break

                op_params["columns"] = selected_columns

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
                            default=str(default_value)
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

    # Print final operations list
    console.print("[bold green]Final Operations:[/bold green]")
    console.print(json.dumps(operations, indent=4))
    
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