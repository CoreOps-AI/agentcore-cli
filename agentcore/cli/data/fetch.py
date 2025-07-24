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

@data.command(name='fetch')
@BaseManager.handle_api_error
def fetch_initial_data():
    """Fetch data from a source and create an initial RAW data version"""
    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data versions
    console.print("[bold green]Fetching available data sources...[/bold green]")
    

    
    data_source_id = None
   
    sources = get_datasource_search_list()
    data_source_id = sources.get('id') if sources else None
    data_type = sources.get('data_type_name')
    
    # Step 3: Ask if user wants to preview the data source first
    # preview_first = Prompt.ask(
    #     "[bold]Do you want to preview the data source first?[/bold]", 
    #     choices=["y", "n"], 
    #     default="y"
    # )
    preview_first = "n"
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
    
    # Step 4: Set up operations
    console.print("[bold]Setting up transformation operations during fetch[/bold]")
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
    
    # Step 5: Confirm and initiate the fetch
    console.print("\n[bold]Fetch Summary:[/bold]")
    console.print(f"Data Source ID: {data_source_id}")
    console.print(f"Operations: {json.dumps(operations, indent=2)}")
    
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

@data.command(name='preview')
@BaseManager.handle_api_error(show_details=True)
def fetch_initial_data():
    """Fetch data from a source and create an initial RAW data version"""

    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data versions
    console.print("\n[bold blue]Select available data source...[/bold blue]")

    datasource_manager = DatasourceManager()
    sources = get_datasource_search_list()
    if not sources:
        return
    
    data_source_id = sources.get('id') if sources else None
    print(f"Selected Data Source ID: {data_source_id}")

    versions = data_version_manager.list_data_versions(data_source_id)

    for version in versions:
        version['data_source_description'] = version['data_source'].get('description')

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': versions},
        columns=data_version_manager.data_version_columns,
        title_prefix="Data Versions",
        row_formatter=table_display.format_datasource_row
    )

    dataversion_id, dataversion = None, None
    while not dataversion:
        dataversion_id = Prompt.ask("[bold]Enter ID from above table[/bold]")
        for version in versions:
            if str(dataversion_id) == str(version['id']):
                dataversion = version
                break
        if not dataversion:
            console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")

    preview_response = data_version_manager.preview_data_version(dataversion_id)

    if not preview_response:
        console.print("[bold red]❌ No data found in selected Data Version.[/bold red]")
        return

    data = preview_response.get('preview', [])
    columns = preview_response.get('columns', [])
    stats = preview_response.get('stats', {})

    total_rows = stats.get('total_rows', 0)
    total_columns = stats.get('total_columns', len(columns))

    # Format column names
    columns = [col.title() if isinstance(col, str) else col for col in columns]

    # Display stats
    console.print(f"\n[bold green]✅ Data from Data Version fetched successfully![/bold green]")
    console.print(f"[yellow]Total Rows:[/yellow] {total_rows}")
    console.print(f"[yellow]Total Columns:[/yellow] {total_columns}")

    # Display all column names
    console.print(f"\n[bold blue]📊 Columns in the dataset:[/bold blue]")
    console.print(", ".join(f"{i+1}. {col}" for i, col in enumerate(columns)))

    # Trim columns for preview if needed
    preview_columns = columns
    if len(columns) > 10:
        console.print(f"\n[bold red]Note:[/bold red] More than 10 columns found. Displaying only the first 10 columns for preview.\n")
        preview_columns = columns[:10]
        data = [{col: row.get(col, "") for col in preview_columns} for row in data]

    # Display preview table
    console.print(f"\n[bold green]🔍 Preview of data from the selected version:[/bold green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': data},
        columns=preview_columns,
        title_prefix="Data Version Preview",
        row_formatter=table_display.format_datasource_row
    )


@data.command(name="history")
@BaseManager.handle_api_error
def history_data_version():
    """View the history (ancestry and descendants) of a data version"""
    data_version_manager = DataVersionManager2()
    
    # Step 1: List available data versions
    console.print("\n[bold blue]Select available data source...[/bold blue]")

    datasource_manager = DatasourceManager()
    sources = get_datasource_search_list()
    if not sources:
        return
    
    data_source_id = sources.get('id') if sources else None
    print(f"Selected Data Source ID: {data_source_id}")

    versions = data_version_manager.list_data_versions(data_source_id)

    for version in versions:
        version['data_source_description'] = version['data_source'].get('description')

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': versions},
        columns=data_version_manager.data_version_columns,
        title_prefix="Data Versions",
        row_formatter=table_display.format_datasource_row
    )

    dataversion_id, dataversion = None, None
    while not dataversion:
        dataversion_id = Prompt.ask("[bold]Enter ID from above table[/bold]")
        for version in versions:
            if str(dataversion_id) == str(version['id']):
                dataversion = version
                break
        if not dataversion:
            console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")

    # Step 3: Fetch history
    console.print(f"[bold green]Fetching history for version {dataversion_id}...[/bold green]")

    with console.status("[bold green]Fetching data version history...[/bold green]") as status:
        history_response = data_version_manager.view_data_version_history(dataversion_id)

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
