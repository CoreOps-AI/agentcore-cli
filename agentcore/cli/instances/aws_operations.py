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
from agentcore.managers.users_manager import UserManager
from agentcore.cli.experiments.helpers import get_project_list

from agentcore.cli.instances.display_utils import displayItemsForSelection
from agentcore.cli.instances.status_tracker import fetch_status, fetch_instance_details

console = Console()

@BaseManager.handle_api_error
def create_aws_instance(project):
    """create aws instance."""
    
    instance_manager = InstanceManager()
    user_manager =UserManager()

    is_demo_user = user_manager.is_demo_user()
    provider_type = "AWS"

    # project = get_project_list()
    # if not project:
    #     return None
    project_id = project['id']
    name = Prompt.ask("\n[bold]Enter unique Instance Name[/bold]")

    stage = Prompt.ask(
        "\n[bold]Choose a stage:[/bold]\n1. DEV\n2. STAGING\n3. PROD\n",
        choices=["1", "2", "3"]
    )

    stage_mapping = {"1": "DEV", "2": "STAGING", "3": "PROD"}
    stage = stage_mapping[stage]

    console.print(f"\nYou selected [blue]{stage}[/blue] stage.")

    # NEW: AWS Credentials Selection
    aws_credential = get_aws_credentials_selection(project_id)
    if not aws_credential:
        console.print("[red]AWS credential selection is required. Aborting the operation[/red]")
        return
    
    is_global = aws_credential.get('credential_type') == "GLOBAL"
    if is_global and is_demo_user :
        console.print(
            "\n[yellow]⚠️ Note: You are using [bold]GLOBAL[/bold] credentials.[/yellow]\n"
            "[bold cyan]Only the following configurations are allowed:[/bold cyan]\n"
            "• Region: [bold green]ap-south-1[/bold green]\n"
            "• Instance Type: [bold green]t2.micro[/bold green]\n"
            "[blue]To unlock more regions and instance types, please use your own AWS keys.[blue]\n"
            "[blue]To save your keys you can use [bold green]'agentcore credentials aws'[/bold green] command.[/blue]\n"
        )

    region = get_aws_region_list() 
    if(region == "/?"):
        region = displayMessageregion()
        
    if is_demo_user and is_global and region != "ap-south-1":
        console.print("[yellow]For Demo user using GLOBAL credentials, only region 'ap-south-1' is allowed.[/yellow]")
        region = "ap-south-1"
    console.print("Region selected is:", region)

    if not region:
        console.print("[red]Region is required. Aborting the operation[/red]")
        return

    # Updated OS type selection using API
    os_type = get_os_type_selection()  # or use instance_manager.get_os_type_with_tab_completion()

    instance_type = get_aws_instance_types(region)
    if(instance_type == "/?"):
        instance_type = getselectedinstancetype(region)
        
    if is_demo_user and is_global and instance_type != "t2.micro":
        console.print("[yellow]For Demo user using GLOBAL credentials, only instance type 't2.micro' is allowed.[/yellow]")
        instance_type = "t2.micro"
    console.print("instance type selected is:", instance_type)

    if not instance_type:
        console.print("[red]Instance type is required. Aborting the operation[/red]")
        return

    pricing = instance_manager.pricing(provider_type, instance_type, region)
    if not pricing:
        return

    instance_data ={
        'provider_type' : provider_type,
        'project_id' : project_id,
        'name' : name,
        'stage' : stage,
        "region" : region,
        "os_type": os_type,
        "instance_type": instance_type,
        "aws_credential_id": aws_credential['id']  # NEW: Add credential ID
    }

    missing_fields = [key for key, value in instance_data.items() if not value]

    if missing_fields:
        for key in missing_fields:
            console.print(f"[red]Error: {key} is required. Aborting operation.[/red]")
        exit(1)  # Exit with an error code

    console.print("\n[bold]Instance Summary:[/bold]")
    for key, value in instance_data.items():
        if key == "aws_credential_id":
            console.print(f"AWS Credential: {aws_credential['name']} ({aws_credential['credential_type']})")
        else:
            console.print(f"{key.title()}: {value}")

    console.print(f"Pricing for chosen region [green]'{region}'[/green] and instance type [green]'{instance_type}'[/green] is [green]{pricing['price_per_hour']} {pricing['currency']}[/green] per hour")
    if Prompt.ask("\n[bold]Create Instance?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Instance creation cancelled.[/yellow]\n")
        return None

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
        # console.print(f"[cyan]ℹ️ To track status with Task ID run:[/cyan] [green]'agentcore instance view'[/green]\n")
        # console.print(f"[cyan]🧾 Use this Task ID :[/cyan] {response.get('task_id', 'N/A')}\n")
        return None
    
    fetch_status(task_id=response['task_id'],instance_id=instance['id'])
    fetch_instance_details(instance['id'])

@BaseManager.handle_api_error
def get_aws_credentials_selection(project_id):
    """
    Display available AWS credentials for the project and let the user select one using tab completion.
    Returns the selected credential object or None if selection failed.
    """
    try:
        instance_manager = InstanceManager()
        base_manager = BaseManager()
        response = instance_manager.get_aws_credentials_by_project(project_id)
        
        if not response:
            console.print("[bold red]No AWS credentials found for this project[/bold red]")
            return None

        if len(response) == 1:
            # If only one credential is available, auto-select it
            credential = response[0]
            console.print(f"\n[green]Auto-selected AWS credential: {credential['name']} ({credential['credential_type']})[/green]")
            return credential

        # Multiple credentials available, let user choose with tab completion
        # Create a mapping of display names to credential objects
        credential_display_names = []
        credential_mapping = {}
        
        for cred in response:
            display_name = f"{cred['name']} ({cred['credential_type']})"
            credential_display_names.append(display_name)
            credential_mapping[display_name] = cred
        
        credential_display_names = sorted(credential_display_names)

        while True:
            console.print("\n[bold]Enter AWS Credential (press Tab for suggestions):[/bold]")
            selected_credential_display = base_manager.get_input_with_tab_completion(
                "AWS Credentials", credential_display_names
            )

            if selected_credential_display in credential_display_names:
                selected_credential = credential_mapping[selected_credential_display]
                console.print(f"\n[green]Selected AWS credential: {selected_credential['name']} ({selected_credential['credential_type']})[/green]")
                return selected_credential
            else:
                console.print(f"\n[yellow]Warning: '{selected_credential_display}' is not a valid AWS credential.[/yellow]")
                suggestions = [cred for cred in credential_display_names if selected_credential_display.lower() in cred.lower()]
                if suggestions:
                    console.print("[blue]Did you mean one of these?[/blue]")
                    for suggestion in suggestions[:5]:
                        console.print(f"  - {suggestion}")
        
    except Exception as e:
        console.print(f"[bold red]Error fetching AWS credentials: {e}[/bold red]")
        return None

@BaseManager.handle_api_error
def displayMessageregion():
    """
    Display available AWS regions in a window and let the user select one by index.
    Returns the selected region name or None if selection failed.
    """
    try:
        instance_manager = InstanceManager()
        response = instance_manager.regions_aws()
        regionList = [region['name'] for region in response]
        
        if not regionList:
            console.print("[bold red]No regions found in the response[/bold red]")
            return None

        messageType="region"  
        # Use the dynamic display function
        title = f"AWS {messageType.title()} Selection"
        region= displayItemsForSelection(regionList, title, messageType)

        while not region:
            console.print("region is not selected. Please try again!")
            region = displayItemsForSelection(regionList, title, messageType)

        return region
        
    except Exception as e:
        console.print(f"[bold red]Error displaying region selection: {e}[/bold red]")
        return None

@BaseManager.handle_api_error
def getselectedinstancetype(region):
    """Show AWS instance types of a region."""

    if not region:
        console.print("[red]Error: Region name cannot be empty.[/red]")
        return None

    try:
        instance_manager = InstanceManager()
        response = instance_manager.instance_type_aws(region)

        if not response or "instance_types" not in response:
            console.print(f"[red]Error:  Region '{region}' not available or No instance types found for region '{region}'.[/red]")
            return
        
        instance_list = response["instance_types"]
        messageType = "Instance Types"
        
        # Use the dynamic display function
        title = f"AWS {messageType.title()} Selection"
        instance_type = displayItemsForSelection(instance_list, title, messageType)

        while not instance_type:
            console.print("Instance type is not selected. Please try again!")
            instance_type = displayItemsForSelection(instance_list, title, messageType)

        return instance_type
        
    except Exception as e:
        console.print(f"[bold red]Error displaying instance types selection: {e}[/bold red]")
        return None       

@BaseManager.handle_api_error
def get_aws_region_list():
    "get regions list"

    instance_manager = InstanceManager()
    base_manager = BaseManager()
    response = instance_manager.regions_aws()
    if not response:
        console.print("[red]No regions found.[/red]")
        return None

    # Extract the region names for tab completion
    region_names = [region["name"] for region in response if "name" in region]
    region_names = sorted(region_names)

    while True:
        console.print("\n[bold]Enter region (press Tab for suggestions):[/bold]")
        selected_region = base_manager.get_input_with_tab_completion("AWS Regions", region_names)

        if selected_region in region_names:
            console.print(f"\n[green]Selected region: {selected_region}[/green]")
            return selected_region
        else:
            console.print(f"\n[yellow]Warning: '{selected_region}' is not a valid region.[/yellow]")
            suggestions = [inst for inst in region_names if selected_region in inst]
            if suggestions:
                console.print("[blue]Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_aws_instance_types(region):
    "get instance types"

    instance_manager = InstanceManager()
    base_manager = BaseManager()
    response = instance_manager.instance_type_aws(region)

    if not response or "instance_types" not in response:
        console.print(f"[red]Error: Region '{region}' not available or no instance types found.[/red]")
        return

    all_instances = sorted(response["instance_types"])
    while True:
        console.print("\n[bold]Enter Instance type (press Tab for suggestions):[/bold]")
        selected_instance = base_manager.get_input_with_tab_completion("AWS Instance types", all_instances)

        if selected_instance in all_instances:
            console.print(f"\n[green]Selected instance type: {selected_instance}[/green]")
            return selected_instance
        else:
            console.print(f"\n[yellow]Warning: '{selected_instance}' is not a valid instance type in given region.[/yellow]")
            suggestions = [inst for inst in all_instances if selected_instance in inst]
            if suggestions:
                console.print("[blue]Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_os_type_selection():
    "get regions list"

    instance_manager = InstanceManager()
    base_manager = BaseManager()
    response = instance_manager.get_os_types()
    if not response:
        console.print("[red]No OS Types found.[/red]")
        return None

    # Extract the os_type names for tab completion
    os_types = [os_type["name"] for os_type in response if "name" in os_type]
    os_types = sorted(os_types)

    while True:
        console.print("\n[bold]Enter OS Type (press Tab for suggestions):[/bold]")
        selected_os_type = base_manager.get_input_with_tab_completion("OS Types", os_types)

        if selected_os_type in os_types:
            console.print(f"\n[green]Selected OS Type: {selected_os_type}[/green]")
            return selected_os_type
        else:
            console.print(f"\n[yellow]Warning: '{selected_os_type}' is not a valid OS Type.[/yellow]")
            suggestions = [inst for inst in os_types if selected_os_type in inst]
            if suggestions:
                console.print("[blue]Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")