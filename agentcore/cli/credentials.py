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

import os
import click
from rich.console import Console
from rich.table import Table
from rich.traceback import install
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
from datetime import datetime, timezone, timedelta
from agentcore.utils.config import CREDENTIALS_TYPES
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.config import ConfigManager
from agentcore.managers.users_manager import UserManager

from agentcore.managers.credentials_manager import CredentialManager
from agentcore.managers.base import BaseManager
from agentcore.managers.config_manager import ConfigManager2
from agentcore.cli.experiments.helpers import get_user_credentials_search_list

install()

console = Console()

#helper functions

@BaseManager.handle_api_error
def beautify_datetime(dt_str, date_only=False):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Convert Zulu to UTC offset
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d") if date_only else dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None
    
@BaseManager.handle_api_error
def get_credential_type_list():
    """Get credential type list with tab completion using Credential type name(id) format and return full Credential type dict."""

    credential_manager = CredentialManager()
    base_manager = BaseManager()
    
    response = credential_manager.get_credential_types()
    if not response:
        console.print("[red]No Credentials types found. Aborting operation.[/red]")
        return None
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{credential_type['name']}({credential_type['id']})": credential_type
        for credential_type in response if "name" in credential_type and "id" in credential_type
    }
    formatted_credential_types = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter Credential Type/ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        selected_credential_type = base_manager.get_input_with_tab_completion("Credential Types", formatted_credential_types)
        if selected_credential_type in formatted_map:
            credential_type = formatted_map[selected_credential_type]

            console.print(f"\n[green]✅ Selected Credential Type:\n Name: [blue]{credential_type['name']}[/blue]\n Description: [blue]{credential_type['description']}[/blue][/green]\n")

            return credential_type
        else:
            console.print(f"\n[yellow]⚠️ '{selected_credential_type}' is not a valid credential type entry.[/yellow]")
            suggestions = [p for p in formatted_credential_types if selected_credential_type.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

#CLI
@click.group()
def credentials():
    """Credentials management commands."""
    pass

# @credentials.command(name='create')
@BaseManager.handle_api_error
def x1():
    """Create a user credential for one of the available credential types."""

    console.print("\n[bold blue]Create User Credential[/bold blue]")

    credential_manager = CredentialManager()
    # Fetch available credential types
    credential_types = credential_manager.get_credential_types()
    print(credential_types)
    if not credential_types:
        console.print("[red]No credential types available.[/red]")
        return None


    # Display credential types for user selection
    console.print("\n[bold]Available Credential Types:[/bold]")
    for i, cred_type in enumerate(credential_types, start=1):
        console.print(f"{i}. {cred_type['name']} - {cred_type['description']}")

    selected_index = int(Prompt.ask("\nSelect a credential type", choices=[str(i) for i in range(1, len(credential_types)+1)])) - 1
    selected_cred_type = credential_types[selected_index]

    name = Prompt.ask("[bold]Credential Name[/bold]", default=f"My {selected_cred_type['name']} Credential")
    credential_data = {}

    for field in selected_cred_type.get("required_fields", []):
        credential_data[field] = Prompt.ask(f"[bold]{field.replace('_', ' ').title()}[/bold]", password=("key" in field or "token" in field))

    # Optional URL for repository use-case
    if selected_cred_type['name'].lower() == "github token":
        credential_data['url'] = Prompt.ask("[bold]Repository URL (optional)[/bold]", default="https://github.com/your-username/your-repo.git")

    # Ask user ID or fetch from config/session
    config = ConfigManager()
    user_id = config.get_user_id()
    if not user_id:
        console.print("[red]User ID is required to add credentials.[/red]")
        return None
    print("user id ", user_id)
    
    payload = {
        "name": name,
        "credential_type_id": selected_cred_type['id'],
        "credential_data": credential_data
    }

    manager = CredentialManager()
    response = manager.create_user_credential(user_id, payload)

    if response:
        # Debug: Print the actual response structure
        console.print(f"[dim]Debug - Response structure: {response}[/dim]")
        
        # Process the credential type field properly
        response_copy = response.copy()  # Work with a copy to avoid modifying original
        
        # Handle credential_type field - try multiple approaches
        if "credential_type" in response_copy:
            cred_type_value = response_copy["credential_type"]
            
            # If it's a dictionary, extract the name
            if isinstance(cred_type_value, dict):
                response_copy["credential_type"] = cred_type_value.get("name", selected_cred_type['name'])
            # If it's None or empty, use the selected credential type name
            elif not cred_type_value:
                response_copy["credential_type"] = selected_cred_type['name']
            # If it's already a string, keep it as is
            elif isinstance(cred_type_value, str):
                response_copy["credential_type"] = cred_type_value
        else:
            # If credential_type field doesn't exist, add it from selected type
            response_copy["credential_type"] = selected_cred_type['name']
        
        # Format the created_at date to be more readable
        if "created_at" in response_copy and response_copy["created_at"]:
            response_copy["created_at"] = format_datetime(response_copy["created_at"])

        console.print("[green]\nCredential created successfully![/green]")
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [response_copy], 'count': 1},
            columns=manager.columns,
            title_prefix="User Credential",
        )
        
    else:
        console.print("[red]Failed to create credential.[/red]")

def format_datetime(datetime_string):
    """
    Format ISO datetime string to IST timezone and readable format.
    
    Args:
        datetime_string (str): ISO format datetime string (UTC)
        
    Returns:
        str: Formatted datetime string in IST
    """
    try:
        # Parse the UTC datetime string
        if datetime_string.endswith('Z'):
            # Remove Z and create UTC datetime
            dt_utc = datetime.fromisoformat(datetime_string[:-1]).replace(tzinfo=timezone.utc)
        else:
            dt_utc = datetime.fromisoformat(datetime_string).replace(tzinfo=timezone.utc)
        
        # Convert to IST (UTC + 5:30)
        ist_timezone = timezone(timedelta(hours=5, minutes=30))
        dt_ist = dt_utc.astimezone(ist_timezone)
        
        # Format to a more readable format in IST
        return dt_ist.strftime("%b %d, %Y at %I:%M %p IST")
    except Exception as e:
        # If formatting fails, return original string
        print(f"Date formatting error: {e}")
        return datetime_string


def get_current_user_id():
    """Stub to fetch current user ID - implement as per session/config."""
    return os.getenv("CURRENT_USER_ID") or "1"

@credentials.command(name='github')
@BaseManager.handle_api_error
def create_credential():
    """Create a user credential for one of the available credential types."""

    console.print("\n[bold blue]Create User Credential[/bold blue]")

    user_manager = UserManager()
    credential_manager = CredentialManager()

    current_user = user_manager.get_current_user()
    if not current_user:
        return None
    
    user_id = current_user.get('id')
    if not user_id:
        console.print("[red]❌ Could not fetch current user info. Aborting.[/red]\n")
        return

    credential_type = get_credential_type_list()
    if not credential_type:
        return None

    credential_type_id = credential_type['id']
    required_fields = credential_type.get('required_fields', [])

    name = Prompt.ask("[bold]Enter Credential Name[/bold]")

    # Prompt for each required field
    field_values = {}
    for field in required_fields:
        label = field.replace('_', ' ').title()
        field_values[field] = Prompt.ask(f"[bold]Enter {label}[/bold]")

    payload = {
        "name": name,
        "credential_type_id": credential_type_id,
        "credential_data": field_values
    }

    response = credential_manager.create_user_credential(user_id, payload)
    if not response:
        console.print("[red]Credential creation failed![/red]")
        return

    # Prepare columns for display
    columns = ['ID', 'Name']
    columns += [field.replace('_', ' ').title() for field in required_fields]

    # Flatten the response for display
    for field in required_fields:
        response[field] = response.get('credential_data', {}).get(field)

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': [response]},  # wrap in list
        columns=columns,
        title_prefix="Credentials",
        row_formatter=table_display.format_project_row
    )


@credentials.command(name='view')
@BaseManager.handle_api_error
def view_credentials():
    """View credentials created by user."""

    user_manager = UserManager()
    credential_manager = CredentialManager()

    current_user = user_manager.get_current_user()
    user_id = current_user.get('id')
    if not user_id:
        console.print("[red]❌ Could not fetch current user info. Aborting.[/red]\n")
        return
    
    response = credential_manager.get_user_credentials(user_id)
    if not response:
        console.print("[yellow]No credentials found for this user.[/yellow]\n")
        return

    credential_type = get_credential_type_list()
    if not credential_type:
        # console.print("[red]No credential type selected. Aborting operation.[/red]")
        return None
    
    filter_name = credential_type['name']
    columns = ['ID', 'Name']
    columns += [field.replace('_', ' ').title() for field in credential_type['required_fields']]

    required_credentials = []

    for credential in response:
        if credential['credential_type_name'] == filter_name:
            required_credentials.append(credential)

    if not required_credentials:
        console.print("[yellow]No credentials found with selected credential type.[/yellow]\n")
        return None

    for credential in required_credentials:
        for item in credential_type['required_fields']:
            credential[item] = credential['credential_data'].get(item)

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': required_credentials},
        columns=columns,
        title_prefix="Credentials",
        row_formatter=table_display.format_project_row
    )

@credentials.command(name='aws')
@BaseManager.handle_api_error
def aws():
    """
    Manage AWS credentials: view (get) or add (post).
    """
    console.print("[bold cyan]What do you want to do?[/bold cyan]")
    console.print("1. View saved AWS credentials (fetch)")
    console.print("2. Add new AWS credentials (post)")
    choice = Prompt.ask("Enter your choice (1 or 2)", choices=["1", "2"])

    config_manager = ConfigManager2()

    if choice == "1":
        credentials = config_manager.get_aws_config_credentials()

        if credentials and isinstance(credentials, list) and len(credentials) > 0:
            table = Table(title="Saved AWS Credentials", show_header=True, header_style="bold magenta", border_style="blue")

            # table.add_column("ID", style="cyan")
            table.add_column("Name", style="yellow")
            table.add_column("Type", style="magenta")
            table.add_column("Access Key", style="green")
            table.add_column("Secret Key", style="green")
            table.add_column("Created At", style="white")
            
            for cred in credentials:
                table.add_row(
                    # str(cred.get("id", "N/A")),
                    cred.get("server_name", "N/A"),
                    cred.get("credential_type", "N/A"),
                    cred.get("access_key", "N/A"),
                    cred.get("secret_key", "N/A"),
                    beautify_datetime(cred.get("created_at", "N/A")),
                    
                )

            console.print(table)
        else:
            console.print("[yellow]No AWS credentials found.[/yellow]")
    elif choice == "2":
        access_key = Prompt.ask("[bold green]Enter your AWS Access Key[/bold green]")
        secret_key = Prompt.ask("[bold green]Enter your AWS Secret Key[/bold green]")
        payload = {
            "access_key": access_key,
            "secret_key": secret_key
        }
        response = config_manager.post_aws_config_credentials(payload)
        console.print("[green]AWS credentials saved successfully![/green]" if response else "[red]Failed to save credentials.[/red]")

 
if __name__ == "__main__":
    credentials()