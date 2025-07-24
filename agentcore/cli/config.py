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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.prompt import Prompt
from rich.traceback import install
from rich import print as rprint
from typing import Optional
import re
from functools import wraps
import json
import logging
from agentcore.managers.users_manager import UserManager
from agentcore.managers.client import APIClient, APIError, HTTPMethod
from agentcore.managers.config import ConfigManager
from agentcore.utils.config import CONFIG_FILE, CONFIG_DIR
from agentcore.managers.base import BaseManager
from agentcore.managers.config_manager import ConfigManager2


install()

console = Console()



@click.group()
def config():
    """Configuration management commands."""
    pass


@config.command(name='set-url')
def set_url():
    """Set the API base URL."""
    config = ConfigManager()
    config.initialize()
    url = Prompt.ask("[bold] Enter service URL[/bold]")
    
    if config.validate_url(url):
        console.print(f"[green]Base URL set to: {url}[/green]")
        config.set_url(url)
    else:
        console.print(f"[red]Provided URL:'{url}' is not a running Agentcore URL. Please set the running Agentcore URL[/red]")

@config.command(name='view')
@BaseManager.handle_api_error
def view_config():
    """View current configuration including logged-in user details with role names."""
    config = ConfigManager()
    
    table = Table(
        title="Current Configuration",
        title_style="bold magenta",
        border_style="blue",
        header_style="bold cyan"
    )
    table.add_column("Setting")
    table.add_column("Value")
    
    # Existing configuration rows
    table.add_row("API URL", config.url() or "[red]Not Set[/red]")
    table.add_row(
        "Token", 
        "[green]Set[/green]" if config.token() else "[red]Not Set[/red]"
    )
    table.add_row("Logged In Time", config.login_time() or "[red]Not Set[/red]")
    
    # Add user information if logged in
    if config.token():
        try:
            user_manager = UserManager()
            user_data = user_manager.get_user_with_role_names()  # Use the new method
            
            if user_data:
                # Add a separator row
                table.add_row("", "")  # Empty row for spacing
                table.add_row("[bold blue]--- Logged-In User Information ---[/bold blue]", "")
                
                # Add user details (excluding tokens)
                # table.add_row("User ID", str(user_data.get("id", "N/A")))
                # table.add_row("Username", str(user_data.get("username", "N/A")))
                table.add_row("Email", str(user_data.get("email", "N/A")))
                table.add_row("Full Name", f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or "N/A")
                table.add_row("Status", "[green]Active[/green]" if user_data.get("is_active") else "[red]Inactive[/red]")
                
                # Format roles with names (fallback to IDs if role names not available)
                if 'role_names' in user_data and user_data['role_names']:
                    roles_str = ", ".join(user_data['role_names'])
                    table.add_row("Roles", f"[green]{roles_str}[/green]")
                    
                else:
                    # Fallback to showing just IDs if role names couldn't be fetched
                    roles = user_data.get("roles", [])
                    roles_str = ", ".join(map(str, roles)) if roles else "None"
                    table.add_row("Roles", f"[yellow]{roles_str} (IDs only)[/yellow]")
            else:
                table.add_row("", "")  # Empty row for spacing
                table.add_row("[yellow]Current Configuration & Logged-in User Info[/yellow]", "[yellow]Unable to fetch user details[/yellow]")
                
        except Exception as e:
            # If there's any error fetching user data, just show that user info is unavailable
            table.add_row("", "")  # Empty row for spacing
            table.add_row("[yellow]Current Logged-in User Configuration & Info[/yellow]", f"[yellow]Error fetching user details: {str(e)}[/yellow]")
    else:
        table.add_row("", "")  # Empty row for spacing
        table.add_row("[yellow]User Info[/yellow]", "[yellow]Not logged in[/yellow]")
    
    console.print(table)


# @config.group()
# def aws():
#     """Manage AWS credentials."""
#     pass

# @aws.command("post")
# @BaseManager.handle_api_error
# def post_aws_credentials():
#     """
#     Save AWS credentials (access_key and secret_key) to the server.
#     """
#     access_key = Prompt.ask("[bold green]Enter your AWS Access Key[/bold green]")
#     secret_key = Prompt.ask("[bold green]Enter your AWS Secret Key[/bold green]")

#     payload = {
#         "access_key": access_key,
#         "secret_key": secret_key
#     }

#     config_manager = ConfigManager2()
#     response = config_manager.post_aws_config_credentials(payload)
#     console.print("[green]AWS credentials saved successfully![/green]" if response else "[red]Failed to save credentials.[/red]")

# @aws.command("get")
# @BaseManager.handle_api_error
# def get_aws_credentials():
#     """
#     Retrieve and display AWS credentials from the server.
#     """
#     config_manager = ConfigManager2()
#     credentials = config_manager.get_aws_config_credentials()

#     if credentials and isinstance(credentials, list) and len(credentials) > 0:
#         table = Table(title="Saved AWS Credentials", show_header=True, header_style="bold magenta")
#         table.add_column("Access Key")
#         table.add_column("Secret Key")
#         for cred in credentials:
#             table.add_row(cred.get("access_key", "N/A"), cred.get("secret_key", "N/A"))
#         console.print(table)
#     else:
#         console.print("[yellow]No AWS credentials found.[/yellow]")



# @config.command()
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
            table = Table(title="Saved AWS Credentials", show_header=True, header_style="bold magenta")
            table.add_column("Access Key")
            table.add_column("Secret Key")
            for cred in credentials:
                table.add_row(cred.get("access_key", "N/A"), cred.get("secret_key", "N/A"))
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


# @config.command(name="aws")
# @BaseManager.handle_api_error
# def post_aws_credentials():
#     """
#     Post AWS credentials (access_key and secret_key) to the server.
#     """
#     access_key = Prompt.ask("[bold green]Enter your AWS Access Key[/bold green]")
#     secret_key = Prompt.ask("[bold green]Enter your AWS Secret Key[/bold green]")

#     payload = {
#         "access_key": access_key,
#         "secret_key": secret_key
#     }

#     config_manager = ConfigManager2()
#     response = config_manager.post_aws_config_credentials(payload)

#     console.print(response)


# @config.group()
# def onprem():
#     """Manage on-premises configurations."""
#     pass

# @onprem.command("post")
# @BaseManager.handle_api_error
# def post_onprem_credentials():
#     """
#     Save on-premises credentials (access_key and secret_key) to the server.
#     """
#     access_key = Prompt.ask("[bold green]Enter your On-Prem Access Key[/bold green]")
#     secret_key = Prompt.ask("[bold green]Enter your On-Prem Secret Key[/bold green]")

#     payload = {
#         "access_key": access_key,
#         "secret_key": secret_key
#     }

#     config_manager = ConfigManager2()
#     response = config_manager.post_aws_config_credentials(payload)
#     console.print("[green]Onprem credentials saved successfully![/green]" if response else "[red]Failed to save credentials.[/red]")

# @onprem.command("get")
# @BaseManager.handle_api_error
# def get_onprem_credentials():
#     """
#     Retrieve and display on-premises credentials from the server.
#     """
#     config_manager = ConfigManager2()
#     credentials = config_manager.get_aws_config_credentials()

#     if credentials and isinstance(credentials, list) and len(credentials) > 0:
#         table = Table(title="Saved On-Prem Credentials", show_header=True, header_style="bold magenta")
#         table.add_column("Access Key")
#         table.add_column("Secret Key")
#         for cred in credentials:
#             table.add_row(cred.get("access_key", "N/A"), cred.get("secret_key", "N/A"))
#         console.print(table)
#     else:
#         console.print("[yellow]No On-Prem credentials found.[/yellow]")
                

if __name__ == "__main__":
    config()