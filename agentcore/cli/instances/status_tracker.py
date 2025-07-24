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

from rich.live import Live
import time

from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list
from agentcore.cli.instances.utils import beautify_datetime


install()

console = Console()

@BaseManager.handle_api_error
def fetch_status(task_id=None,instance_id = None):
    "Fetch Status by Task ID"

    instance_manager = InstanceManager()
    table_display = TableDisplay()
    if not task_id:
        task_id = Prompt.ask("\n[bold]Enter Task ID[/bold]")
    
    if not task_id:
        console.print("[red]Error: Task ID is required. Aborting operation.[/red]")
        exit(1)

    console.print("\n[yellow]Monitoring task status... Press Ctrl+C to stop[/yellow]")
    
    # Initial setup
    table = None
    live = None
    
    try:
        while True:
            response = instance_manager.instance_status(task_id)
            if instance_id:
                instance_response = instance_manager.instance_show(instance_id=instance_id)
            if not response:
                if live:
                    live.stop()
                console.print("[red]Failed to get response[/red]")
                return None
            
            if isinstance(response, dict):
                # Beautify datetime fields
                if response.get("created_at"):
                    response["created_at"] = beautify_datetime(response["created_at"])
                if response.get("updated_at"):
                    response["updated_at"] = beautify_datetime(response["updated_at"])
                
                # Create new table for this update
                new_table = Table(title="\nTask Status Summary", title_style="bold green")
                new_table.add_column("Field", style="cyan", no_wrap=True)
                new_table.add_column("Value", style="white")

                new_table.add_row("Task ID", response.get("task_id", "N/A"))
                new_table.add_row("Task Status", response.get("status", "N/A"))
                new_table.add_row("Created At", response.get("created_at", "N/A"))
                new_table.add_row("Updated At", response.get("updated_at", "N/A"))
                if instance_id:
                    new_table.add_row("Instance State", instance_response.get("state", "N/A"))

                result = response.get("result", {})
                if result:
                    # new_table.add_row("Instance State-2", result.get("state", "N/A"))
                    new_table.add_row("Result Status", result.get("status", "N/A"))
                    new_table.add_row("Message", result.get("message", "N/A"))
                    new_table.add_row("Instance ID", str(result.get("instance_id", "N/A")))

                # If this is the first time, create the Live display
                if live is None:
                    live = Live(new_table, console=console, refresh_per_second=1)
                    live.start()
                else:
                    # Update the existing live display
                    live.update(new_table)
                
                # If result exists, stop live and break
                if result:
                    live.stop()
                    # console.print(new_table)
                    break

                table = new_table
                
            else:
                if live:
                    live.stop()
                console.print("[red]Unexpected response format[/red]")
                if response:
                    console.print(response)
                break
            
            # Wait for 5 seconds before next update
            import time
            time.sleep(5)
            
    except KeyboardInterrupt:
        if live:
            live.stop()
        console.print("\n[yellow]Monitoring stopped by user[/yellow]\n")
    except Exception as e:
        if live:
            live.stop()
        console.print(f"[red]Error occurred: {e}[/red]")

@BaseManager.handle_api_error
def fetch_instance_details(instance_id = None):
    "Fetch intance details by ID"

    instance_manager = InstanceManager()
    table_display = TableDisplay()

    if not instance_id:
        instance_id = Prompt.ask("\n[bold]Enter Instance ID[/bold]")
        if not instance_id:
            console.print("[red]Error: Instance ID is required. Aborting operation.[/red]")
            exit(1)

    response = instance_manager.instance_show(instance_id)
    if not response:
        console.print("[red]No Instance found with given ID[/red]\n")
        return None
    
    response['project_id'] = response['project']

    if response:
        table_display.display_table(
            response_data={'results': [response], 'count': 1},
            columns=instance_manager.columns,
            title_prefix='Instance',
            row_formatter=table_display.format_instance_row
        )

@BaseManager.handle_api_error
def fetch_instance_details_project_id():
    "Fetch intances by Project ID"

    instance_manager = InstanceManager()
    table_display = TableDisplay()

    project = get_project_list()
    if not project:
        return None
    project_id = project['id']
    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        exit(1)

    response = instance_manager.project_instance_show(project_id)

    if response:
        filtered_columns = [col for col in instance_manager.project_instance_columns
                            if col not in ['CPU Count', 'Memory Size', 'Stopped At', 'AWS Region', 'OS Type']]

    console.print(f"\n[blue]Instances of Project: [green]{project['name']}[/green][/blue]")
    table_display.display_table(
                response_data={'results': response['instances'], 'count': len(response['instances'])},
                columns=filtered_columns,
                title_prefix='Project Instance',
                row_formatter=table_display.format_instance_row
            )