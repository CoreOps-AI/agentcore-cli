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
from rich.live import Live
import time
from agentcore.managers.base import BaseManager
from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.table_manager import TableDisplay



install()

console = Console()

@BaseManager.handle_api_error
def beautify_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))  # Convert to datetime object
    return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format as 'YYYY-MM-DD HH:MM:SS'

@BaseManager.handle_api_error
def get_instance_list(project_id):
    """Get instance list with tab completion using id-instance_name(state) format and return full instance dict."""

    instance_manager = InstanceManager()
    base_manager = BaseManager()

    response = instance_manager.project_instance_show(project_id)
    response = response['instances']
    
    if not response:
        console.print("[red]No Instances found.[/red]\n")
        return None
    
    # Create mapping: formatted string => original instance dict
    formatted_map = {
        f"{instance['id']}-{instance['name']}({instance['state']})": instance
        for instance in response if "name" in instance and "id" in instance and "state" in instance
    }
    formatted_instances = sorted(formatted_map.keys())

    while True:
        console.print("\n[bold]Enter Instance Name/ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        
        if len(formatted_instances) == 1:
            selected_instance = formatted_instances[0]
            console.print(f"[green]Automatically selected the only available instance:[/green] {selected_instance}")
        else:
            selected_instance = base_manager.get_input_with_tab_completion("Instances", formatted_instances)
        if selected_instance in formatted_map:
            instance = formatted_map[selected_instance]

            if response:
                filtered_columns = [col for col in instance_manager.project_instance_columns
                            if col not in ['CPU Count', 'Memory Size', 'Stopped At', 'AWS Region', 'OS Type']]

            console.print(f"\n[green]✅ Selected Instance: {instance['id']}-{instance['name']}({instance['state']})[/green]")
            console.print("[bold]Selected Instance Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [instance]},
                columns=filtered_columns,
                title_prefix="Selected Project",
                row_formatter=table_display.format_instance_row
            )

            return instance
        else:
            console.print(f"\n[yellow]⚠️ '{selected_instance}' is not a valid instance entry.[/yellow]")
            suggestions = [p for p in formatted_instances if selected_instance.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")