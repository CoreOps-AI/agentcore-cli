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

from rich.console import Console
from rich.prompt import Prompt

from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list

from agentcore.cli.instances.status_tracker import fetch_status

console = Console()

@BaseManager.handle_api_error
def create_onprem_instance():
    """Create On-Prem instance."""

    provider_type = "VBOX"

    project = get_project_list()
    project_id = project['id']
    name = Prompt.ask("\n[bold]Enter unique Instance Name[/bold]")
    stage = Prompt.ask(
        "\n[bold]Choose a stage:[/bold]\n1. DEV\n2. STAGING\n3. PROD\n",
        choices=["1", "2", "3"]
    )

    stage_mapping = {"1": "DEV", "2": "STAGING", "3": "PROD"}
    stage = stage_mapping[stage]

    console.print(f"\nYou selected [blue]{stage}[/blue] stage.")
    
    instance_type = Prompt.ask("\n[bold]Enter Instance Type[/bold]", default="VirtualBox Instance")
    cpu_count = Prompt.ask("\n[bold]Enter CPU Count[/bold]", default="2")
    memory_size = Prompt.ask("\n[bold]Enter Memory Size (MB)[/bold]", default="1024")

    instance_data = {
        "provider_type": provider_type,
        "project_id": project_id,
        "name": name,
        "stage": stage,
        "instance_type": instance_type,
        "cpu_count": cpu_count,
        "memory_size": memory_size,
        "on_prem_server_id": 1,
    }

    missing_fields = [key for key, value in instance_data.items() if not value]

    if missing_fields:
        for key in missing_fields:
            console.print(f"[red]Error: {key} is required. Aborting operation.[/red]")
        exit(1)  # Exit with an error code

    console.print("\n[bold]Instance Summary:[/bold]")
    for key, value in instance_data.items():
        console.print(f"{key.title()}: {value}")

    if Prompt.ask("\n[bold]Create Instance?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Instance creation cancelled.[/yellow]\n")
        return None

    instance_manager = InstanceManager()
    response = instance_manager.instance_create(instance_data)
    if not response:
        console.print("[red]Instance creation failed.[/red]")
        return
    
    console.print(f"\n[cyan]📝 Message  :[/cyan] {response.get('message', 'N/A')}")
    console.print(f"[cyan]🧾 Task ID :[/cyan] {response.get('task_id', 'N/A')}\n")
    
    instance = response['instance']

    if instance:
        instance["project_id"] = instance["project"]

    if instance:
        table_display = TableDisplay()
        table_display.display_table(
            response_data={'results': [instance], 'count': 1},
            columns=instance_manager.columns,
            title_prefix='Created Instance',
            row_formatter=table_display.format_instance_row
        )
    if Prompt.ask("\n[bold]Do you want to track status?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print(f"[cyan]ℹ️ To track status with Task ID run:[/cyan] [green]'agentcore instance view'[/green]\n")
        console.print(f"[cyan]🧾 Use this Task ID :[/cyan] {response.get('task_id', 'N/A')}\n")
        return None
    
    fetch_status(response['task_id'],instance_id=instance['id'])