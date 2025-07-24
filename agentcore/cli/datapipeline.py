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

from agentcore.managers.datapipeline_manager import DatapipelineManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager

install()

console = Console()

@click.group()
def datapipeline():
    """Datapipeline management commands."""
    pass
    
@datapipeline.command(name='operations')
@BaseManager.handle_api_error
def fe_operations():
    """Operations on RAW data"""
    
    source_data_version_id = Prompt.ask("[bold]Enter Data Version ID[/bold]")
    if not source_data_version_id:
        console.print("[red]Source Data Version ID is required. Aborting operation.[/red]")
        return
    
    source_stage = Prompt.ask("[bold]Enter Source Stage[/bold]")
    if not source_stage:
        console.print("[red]Source Stage is required. Aborting operation.[/red]")
        return
    
    operation_name = Prompt.ask("[bold]Enter Operation Name[/bold]")
    if not operation_name:
        console.print("[red]Operation Name is required. Aborting operation.[/red]")
        return
    
    output_description = Prompt.ask("[bold]Enter Output Description[/bold]")
    if not output_description:
        console.print("[red]Output Description is required. Aborting operation.[/red]")
        return
    
    console.print("[bold]Enter Operation Details:")
    function_name = Prompt.ask("[bold]Enter Function Name[/bold]")
    if not function_name:
        console.print("[red]Function Name is required. Aborting operation.[/red]")
        return
    
    columns_input = Prompt.ask("[bold]Enter Columns (comma-separated)[/bold]")
    if not columns_input:
        console.print("[red]Columns are required. Aborting operation.[/red]")
        return
    columns = [col.strip() for col in columns_input.split(",")]
    
    new_col_name_prefix = Prompt.ask("[bold]Enter New Column Name Prefix[/bold]")
    if not new_col_name_prefix:
        console.print("[red]New Column Name Prefix is required. Aborting operation.[/red]")
        return
    
    transform_type = Prompt.ask("[bold]Enter Transform Type[/bold]")
    if not transform_type:
        console.print("[red]Transform Type is required. Aborting operation.[/red]")
        return
    
    # Create payload
    payload = {
        "source_data_version_id": int(source_data_version_id),
        "source_stage": source_stage,
        "operations": [
            {
                "function_name": function_name,
                "columns": columns,
                "parameters": {
                    "new_col_name_prefix": new_col_name_prefix,
                    "transform_type": transform_type
                }
            }
        ],
        "operation_name": operation_name,
        "output_description": output_description
    }
    
    # Call operations_fe function from DataPipelineManager
    console.print("[bold blue]Operation input summary:[/bold blue]")
    console.print(json.dumps(payload, indent=2))

    if Prompt.ask("\n[bold yellow]Do you want to proceed with this operation?[/bold yellow]", choices=["yes", "no"], default="no") == "no":
        console.print("[yellow]Operation cancelled by user.[/yellow]")
        return None
    
    # Call the operations_fe function
    datasource_manager = DatapipelineManager()
    result = datasource_manager.operations_fe(payload)
    
    # Display the result
    if not result:
        console.print("[red]Operation Failed[/red]")

    console.print("[bold green]Operation completed successfully![/bold green]")
    console.print(result)



if __name__ == "__main__":
    datapipeline()