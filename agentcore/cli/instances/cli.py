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
from rich.prompt import Prompt

from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list

from agentcore.cli.instances.aws_operations import create_aws_instance, get_aws_region_list, get_aws_instance_types
from agentcore.cli.instances.onprem_operations import create_onprem_instance
from agentcore.cli.instances.status_tracker import fetch_instance_details, fetch_instance_details_project_id, fetch_status

console = Console()

@click.group()
def instances():
    """instance management commands."""
    pass

@instances.command(name='create')
@BaseManager.handle_api_error
def create_instance():
    """create  instance."""

    base_manager = BaseManager()
    
    console.print("[bold blue]Creating new Instance (interactive mode)[/bold blue]")

    # provider_mapping = {"1": "AWS", "2": "ON-PREM", "3": "AZURE"}
    # provider_choice = Prompt.ask(
    #     "\n[bold]Choose a Provider type:[/bold]\n1. AWS\n2. ON Prem\n3. AZURE\n",
    #     choices=["1", "2", "3"]
    # )

    project = get_project_list()
    if not project:
        return None
    
    providers_list = ["AWS", "ON-PREM", "AZURE", "GCP"]

    provider_type = None
    while provider_type != "AWS":
        provider_type = base_manager.get_input_with_tab_completion("Providers", providers_list)
        if not provider_type:
            console.print("[red]❌ No provider selected. Please choose from the list.[/red]\n")
            continue

        if provider_type != "AWS":
            console.print("[yellow]⚠️ For trail version, only the 'AWS' provider is available. Please select 'AWS'.[/yellow]\n")
            provider_type = None  # Reset to prompt again

    console.print(f"\nYou selected [blue]{provider_type}[/blue] provider type.")

    if provider_type == "AWS":
        create_aws_instance(project)
    else: 
        console.print("[blue]For DEMO user, only AWS provider is available.[/blue]\n")
        provider_type = None

@instances.command(name='view')
@BaseManager.handle_api_error
def show_or_view_instance():
    """Show instance details or list instances under a project (interactive mode)."""
    console.print("[bold blue]Instance Viewer (interactive mode)[/bold blue]")

    # Ask user for the mode
    # mode = Prompt.ask("\n[bold]Choose mode[/bold] (1: By Instance ID, 2: By Project ID, 3: Status by Instance ID)", choices=["1", "2", "3"], default="1")

    # if mode == "1":
    #     fetch_instance_details()
    # elif mode == "2":
    #     fetch_instance_details_project_id()
    # elif mode == "3":
    #     fetch_status()

    fetch_instance_details_project_id()

@instances.command(name='pricing')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def cloud_pricing():
    """Fetch cloud pricing for a specific provider, instance type, and region."""
 
    console.print("[bold blue]Calculate your cost (Interactive Mode)[/bold blue]\n")
 
    # Ask for provider choice
    choices = {"1": "AWS", "2": "Azure", "3": "GCP"}
    choice = Prompt.ask(
        "\n".join([f"{k} - {v}" for k, v in choices.items()]) + "\n[bold]Choose your provider[/bold]",
        choices=choices.keys(),
        default="1"
    )
    provider = choices[choice]
 
    # Ask for region
    region = get_aws_region_list()
    if not region:
        console.print("[red]Error: Region cannot be empty.[/red]")
        return
 
    # Ask for instance type
    instance_type = get_aws_instance_types(region=region)
    if not instance_type:
        console.print("[red]Error: Instance type cannot be empty.[/red]")
        return
 
    instance_manager = InstanceManager()
    pricing_data = instance_manager.pricing(provider, instance_type, region)
 
    if pricing_data is None:
        # console.print("[red]Error: Failed to fetch pricing data.[/red]")
        return
       
    if "error" in pricing_data:
        console.print(f"[red]Error: {pricing_data['error']}[/red]")
 
    elif "provider" in pricing_data:
        console.print("\n[bold green]Pricing Details:[/bold green]\n")
        console.print(f"[cyan]Provider        :[/cyan] {pricing_data.get('provider', 'N/A')}")
        console.print(f"[cyan]Instance Type   :[/cyan] {pricing_data.get('instance_type', 'N/A')}")
        console.print(f"[cyan]Region          :[/cyan] {pricing_data.get('region', 'N/A')}")
        console.print(f"[cyan]Price per Hour  :[/cyan] ${pricing_data.get('price_per_hour', 'N/A')} {pricing_data.get('currency', '')}\n")
    else:
        console.print("[yellow]No pricing data found.[/yellow]")

@instances.command(name='regions')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def cloud_regions():
    """Show cloud instance regions."""
    # Ask for provider choice
    choices = {"1": "AWS", "2": "Azure", "3": "GCP"}
    choice = Prompt.ask(
        "\n".join([f"{k} - {v}" for k, v in choices.items()]) + "\n[bold]Choose your provider[/bold]",
        choices=choices.keys(),
        default="1"
    )
    provider = choices[choice]
    
    if provider == 'AWS':
        instance_manager = InstanceManager()
        response = instance_manager.regions_aws()
                
        if isinstance(response, list):
            console.print(f"[blue]AWS Regions ({len(response)} available):[/blue]\n")
            for region in response:
                console.print(f" - {region['name']}")
        else:
            console.print("[red]Error: No regions found or invalid response.[/red]")
    elif provider in ['Azure', 'GCP']:
        console.print(f"[yellow]{provider.upper()} regions coming soon.[/yellow]")
    else:
        console.print("[red]Invalid cloud provider. Please enter aws, azure, or gcp.[/red]")

@instances.command(name='instance-types')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def aws_instance_types():
    """Show AWS instance types of a region with tab-completion and suggestions."""
    from collections import defaultdict
    
    console.print("[bold]Instance Type Selection[/bold]")

    region = get_aws_region_list()
    if not region:
        console.print("[red]Error: Region name cannot be empty.[/red]")
        return None

    instance_manager = InstanceManager()
    response = instance_manager.instance_type_aws(region)

    if not response or "instance_types" not in response:
        console.print(f"[red]Error: Region '{region}' not available or no instance types found.[/red]")
        return

    instance_categories = defaultdict(list)

    for instance in response["instance_types"]:
        category = instance.split(".")[0]  # Extract family (e.g., c6a, x1e)
        instance_categories[category].append(instance)

    console.print(f"\n[blue]Region:[/blue] {response['region']}\n")
    console.print("[blue]Instance Types by Category:[/blue]\n")

    for category, instances in sorted(instance_categories.items()):
        console.print(f"[blue]{category.upper()}:[/blue]")
        console.print(f"  - {' | '.join(instances)}\n")  # Join instances with " | "

@instances.command(name='action')
@BaseManager.handle_api_error
def start_instance():
    """Start or Stop an instance."""
    console.print("[bold blue]Start or Stop Instance (interactive mode)[/bold blue]")
    instance_manager = InstanceManager()

    project = get_project_list()
    if not project:
        console.print("[red]Erro while selecting Project")
    project_id = project['id']

    project_instances = instance_manager.project_instance_show(project_id)
    if not project_instances:
        console.print(f"[red]No Instances are found with this Project ID-{project_id}[/red]")
        return 
    
    if project_instances:
        filtered_columns = [col for col in instance_manager.project_instance_columns
                            if col not in ['CPU Count', 'Memory Size', 'Stopped At', 'AWS Region', 'OS Type']]

    console.print(f"\n[blue]Instances of Project:[green]{project['name']}[/green][/blue]")
    table_display = TableDisplay()
    table_display.display_table(
                response_data={'results': project_instances['instances']},
                columns=filtered_columns,
                title_prefix='Project Instance',
                row_formatter=table_display.format_instance_row
            )

    instances_ids = [instance['id'] for instance in project_instances['instances']]
    
    instance_id = int(Prompt.ask("[bold]Select Instance ID from above table[bold]"))
    if instance_id not in instances_ids:
        console.print("[red]Entered Instance is not from selected Project. Aborting operation.[/red]\n")
        return 
    
    instance = next((instance for instance in project_instances['instances'] if instance_id == instance['id']), None)

    # instance_id = Prompt.ask("\n[bold]Enter Instance ID[/bold]")

    if not instance_id:
        console.print("[red]Error: Instance ID is required. Aborting operation.[/red]")
        exit(1) 
    
    action = Prompt.ask(
        "\n[bold]Choose an action:[/bold]\n1. Start\n2. Stop\n",
        choices=["1", "2"]
    )
    action_mapping = {"1": "start", "2": "stop"}
    action = action_mapping[action]
    console.print(f"\nYou selected [blue]{action}[/blue] action.\n")

    instance_manager = InstanceManager()
    response = instance_manager.instance_start(instance_id, action)

    if isinstance(response, dict):
        task_id = response.get("task_id")
        message = response.get("message", "No message").rstrip(".")
        inst_id = response.get("instance_id", "N/A")

        console.print(f"[green]✓ Instance ID:[/green] {inst_id}")
        console.print(f"[green]✓ {message}[/green]")
        console.print(f"[cyan]ℹ️ Use this Task ID to track status:[/cyan] [bold]{task_id}[/bold] with [green]'agentcore instance view'[/green] command\n")

    else:
        console.print(f"[red]Unexpected response: {response}[/red]")
        return None
    
    if Prompt.ask("\n[bold]Do you want to track status?[/bold]", choices=["yes", "no"], default="yes") == "no":
        # console.print(f"[cyan]ℹ️ To track status with Task ID run:[/cyan] [green]'agentcore instance view'[/green]\n")
        # console.print(f"[cyan]🧾 Use this Task ID:[/cyan] [bold]{task_id}[/bold]\n")
        return None
    
    fetch_status(task_id=task_id,instance_id=instance_id)

    console.print("\n[green]Updated instance details:[/green]")
    fetch_instance_details(instance_id)

@instances.command(name = "update")
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def update_instance():
    "Update an instance"

    instance_manager = InstanceManager()

    project = get_project_list()
    if not project:
        console.print("[red]Erro while selecting Project")
    project_id = project['id']

    project_instances = instance_manager.project_instance_show(project_id)
    if not project_instances:
        console.print(f"[red]No Instances are found with this Project ID-{project_id}[/red]")
        return 
    
    if project_instances:
        filtered_columns = [col for col in instance_manager.project_instance_columns
                            if col not in ['CPU Count', 'Memory Size', 'Stopped At', 'AWS Region', 'OS Type']]

    console.print(f"\n[blue]Instances of Project:[green]{project['name']}[/green][/blue]")
    table_display = TableDisplay()
    table_display.display_table(
                response_data={'results': project_instances['instances']},
                columns=filtered_columns,
                title_prefix='Project Instance',
                row_formatter=table_display.format_instance_row
            )

    instances_ids = [instance['id'] for instance in project_instances['instances']]
    
    instance_id = int(Prompt.ask("[bold]Select Instance ID from above table[bold]"))
    if instance_id not in instances_ids:
        console.print("[red]Entered Instance is not from selected Project. Aborting operation.[/red]\n")
        return 
    
    instance = next((instance for instance in project_instances['instances'] if instance_id == instance['id']), None)

    if instance['provider_type'] == 'AWS':
        console.print(f"Current instance type: [green]{instance['instance_type']}[/green] from [green]{instance['aws_region']}[/green] region")
        
        instance_type = get_aws_instance_types(instance['aws_region'])
        provider_type = instance['provider_type']
        region = instance['aws_region']
    
        payload = {
            "instance_id": instance_id,
            "instance_type": instance_type
        }
        pricing = instance_manager.pricing(provider_type, instance_type, region)
        if not pricing:
            return
        console.print(f"Pricing for chosen region [green]'{region}'[/green] and instance type [green]'{instance_type}'[/green] is [green]{pricing['price_per_hour']} {pricing['currency']}[/green] per hour")

    elif instance['provider_type'] == 'VBOX':
        "Update the code here"
        console.print("[black] Feature Coming Soon[/black]")
        return None

    if Prompt.ask("\n[bold]Confirm Update?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Instance update cancelled.[/yellow]\n")
        return None
    response = instance_manager.instance_update(payload)
    if response:
        console.print("\n[bold green]✅ Instance Update Queued Successfully![/bold green]\n")
        console.print(f"[cyan]📝 Message     :[/cyan] {response.get('message', 'N/A')}")
        console.print(f"[cyan]📦 Instance ID :[/cyan] {response.get('instance_id', 'N/A')}")
        console.print(f"[cyan]🧾 Task ID     :[/cyan] {response.get('task_id', 'N/A')}\n")
    else:
        console.print("[red]❌ Instance Update failed.[/red]")
        return None

    if Prompt.ask("\n[bold]Do you want to track status?[/bold]", choices=["yes", "no"], default="yes") == "no":
        # console.print(f"[cyan]ℹ️ To track status with Task ID run:[/cyan] [green]'agentcore instance view'[/green]\n")
        # console.print(f"[cyan]🧾 Use this Task ID:[/cyan] {response.get('task_id', 'N/A')}\n")
        return None
    
    fetch_status(response['task_id'], instance_id=instance_id)

if __name__ == "__main__":
    instances()