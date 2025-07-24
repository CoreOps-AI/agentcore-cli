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
import json
import sys
from agentcore.managers.users_manager import UserManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager

install()

console = Console()

#helpers functions

@BaseManager.handle_api_error
def get_single_user():
    """Get Users list with tab completion (name only) and return full type dict."""
    
    user_manager = UserManager()
    base_manager = BaseManager()
    users_response = user_manager.view_users()

    if not users_response:
        console.print("[red]No Users found.[/red]")
        return

    formatted_map = {
        f"{user['username']}({user['email']})": user
        for user in users_response if "username" in user and "email" in user
    }
    formatted_names = sorted(formatted_map.keys())

    while True:
        
        console.print("\n[bold]Enter a username or email to select user (press Tab for suggestions, Enter to confirm):[/bold]")
        selected_user = base_manager.get_input_with_tab_completion("Usernames", formatted_names)
        
        if selected_user in formatted_map:
            user = formatted_map[selected_user]
            console.print(f"\n[green]✅ Selected User:[/green] {selected_user}")

            console.print("[bold]Selected User Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [user]},
                columns=user_manager.columns,
                title_prefix="Selected User",
                row_formatter=table_display.format_user_row
            )
            return user
        else:
            console.print(f"\n[yellow]⚠️ '{selected_user}' is not a valid User.[/yellow]")
            suggestions = [p for p in formatted_names if selected_user.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_multiple_roles():
    """Get Roles list with tab completion (name only) and return full type dict."""
    
    user_manager = UserManager()
    base_manager = BaseManager()
    roles_response = user_manager.view_roles()

    if not roles_response:
        console.print("[red]No Roles found.[/red]")
        return

    formatted_map = {
        f"{role['name']}({role['id']})": role
        for role in roles_response if "name" in role and "id" in role
    }
    formatted_roles = sorted(formatted_map.keys())

    while True:
        
        console.print("\n[bold]Enter a Role to assign to the User (press Tab for suggestions, Enter to confirm):[/bold]")
        console.print("[bold]Leave empty if you don't want to assign any role.[/bold]")
        selected_role = base_manager.get_input_with_tab_completion("Roles", formatted_roles)
        
        if not selected_role:
            return None
        if selected_role in formatted_map:
            role = formatted_map[selected_role]
            console.print(f"\n[green]✅ Selected Role:[/green] {selected_role}")

            return role
        else:
            console.print(f"\n[yellow]⚠️ '{selected_role}' is not a valid Role.[/yellow]")
            suggestions = [p for p in formatted_roles if selected_role.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

#cli functions
@click.group()
def users():
    """User management commands."""
    pass

@users.command(name='view')
@click.option('--format', '-f', 
              type=click.Choice(['table', 'json']), 
              default='table',
              help='Output format')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def view_users(format):
    """View all users with formatting and pagination."""
    user_manager = UserManager()
    base_manager = BaseManager()
    response_users = user_manager.view_users()
    response_roles = user_manager.view_roles()

    if response_users == -1:
        return None
    if not response_users:
        console.print("[yellow]No users found.[/yellow]")
        return None

    role_mapping = {role["id"]: role["name"] for role in response_roles or []}

    response_dict_list = [
        {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "is_active": user["is_active"],
            "roles": ", ".join(role_mapping.get(role_id, "Unknown") for role_id in user.get("roles", []))
        }
        for user in response_users
    ]

    if format == 'json':
        return response_users

    base_manager.paginate_data(
        data=response_dict_list,
        columns=user_manager.columns,
        title_prefix='Users List',
        row_formatter=TableDisplay().format_user_row,
        page_size=10
    )


@users.command(name='create')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def create_user():
    """Create a new user. Starts an interactive prompt."""
    user_manager = UserManager()
    base_manager = BaseManager()
    console.print("\n[bold blue]Creating new user (interactive mode)[/bold blue]\n")
    
    username = Prompt.ask("[bold]Username[/bold]")
    email = Prompt.ask("[bold]Email[/bold]")
    first_name = Prompt.ask("[bold]First Name[/bold]", default="")
    last_name = Prompt.ask("[bold]Last Name[/bold]", default="")
    password = base_manager.masked_input("\n[bold]Password:[/bold] ")
    active_status = Prompt.ask("[bold]Active Status (true/false)[/bold]", choices=["true", "false"], default="true")

    # Fetch and display roles
    roles_response = user_manager.get_roles()
    # Create a styled table
    table = Table(
        title="Available Roles",
        title_style="bold magenta",
        border_style="blue",
        header_style="bold cyan"
    )
    
    table.add_column("Role ID", justify="center", style="yellow")
    table.add_column("Role Name", justify="left", style="green")

    # Assuming roles_response is a list of dicts with keys 'id' and 'name'
    for role in sorted(roles_response, key=lambda x: x["id"]):
        table.add_row(str(role["id"]), role["name"])

    console.print(table)
    
    console.print("\n[bold blue]Assign Roles to the User[/bold blue]\n")

    add_roles = []
    add_roles_str = []
    add_role_names = []
    while True:
        role = get_multiple_roles()
        if role:
            role_id = role['id']
            role_name = role['name']
            add_roles_str.append(str(role_id))
            add_role_names.append(role_name)
        else :
            break

    if not add_roles_str:
            console.print("[yellow]No role was selected for assignment to user[/yellow]")

    user_data = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "is_active": active_status.lower() == "true",
    }
    
    console.print("\n[bold green]User Summary:[/bold green]")
    for key, value in user_data.items():
        console.print(f"{key.title()}: {value}")
    if not add_roles_str:
            console.print("[yellow]No role was selected for assignment to user[/yellow]")
    else:
        add_roles = list(dict.fromkeys(role_id.strip() for role_id in add_roles_str))
        console.print(f"Assigning_roles: {add_role_names}")
    
    if Prompt.ask("\n[bold]Create user?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]User creation cancelled.[/yellow]\n")
        return
    
    user = user_manager.user_create(user_data)
    if not user:
        console.print("[red]Failed to create user.[/red]")
        return 
    console.print("\n[bold green]User Created Successfully.[/bold green]")

    user_id = user['id']

    if not user_id:
        console.print("[red]User ID is required. Aborting operation.[/red]")
        return
       
    if add_roles_str:

        payload_data = {
            "user_id": user_id,
            "add_roles": add_roles,
            "remove_roles": [] 
        }

        user_manager = UserManager()
        response = user_manager.assign_role(payload_data=payload_data)

        # Display response in a structured format
        # console.print(Panel.fit(f"[bold green]{response['message']}[/bold green]", title="✅ Status", border_style="green"))
        if response:
            console.print(f"[bold green]{response['message']}[/bold green]")

        if response["added_roles"]:
            console.print(f"[bold cyan]➕ Added Roles:[/bold cyan] {', '.join(response['added_roles'])}")
        else:
            console.print(f"[bold cyan]➕ Added Roles:[/bold cyan] None")
        
        if not response:
            console.print("\n[red]Role assignment operation failed.[/red]")
    
    
    current_user = user_manager.fetch_user(user_id)
    if current_user == -1 or not current_user:
        console.print(f"[red]No user found with ID {user_id} Exiting.[/red]")
        return None
    
    role_id_to_name = {role['id']: role['name'] for role in roles_response}
    user_role_names = [role_id_to_name.get(role_id) for role_id in current_user['roles'] if role_id in role_id_to_name]
    current_user['roles'] = user_role_names

    console.print("\n[bold]Created User Details:[/bold]")
    if current_user:
        table_display = TableDisplay()
        table_display.display_table(
            response_data={'results': [current_user], 'count': 1},
            columns=user_manager.columns,
            title_prefix='Created user',
            row_formatter=table_display.format_user_row
        )

@users.command(name='assign-role')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def role_assign():
    """Assign role to an user by their ID."""

    user_manager = UserManager()

    # Fetch and display roles
    roles_response = user_manager.get_roles()
    # Create a styled table
    table = Table(
        title="Available Roles",
        title_style="bold magenta",
        border_style="blue",
        header_style="bold cyan"
    )
    
    table.add_column("Role ID", justify="center", style="yellow")
    table.add_column("Role Name", justify="left", style="green")

    # Assuming roles_response is a list of dicts with keys 'id' and 'name'
    for role in sorted(roles_response, key=lambda x: x["id"]):
        table.add_row(str(role["id"]), role["name"])

    console.print(table)

    console.print("\n[bold blue]Assign or Remove Roles to a User (Interactive Mode)[/bold blue]\n")

    current_user = get_single_user()
    user_id = current_user['id']
   
    if not user_id:
        console.print("[red]User ID is required. Aborting operation.[/red]")
        return
    
    console.print("\n[bold blue]Assign Roles to the User[/bold blue]\n")
    add_roles = []
    add_roles_str = []
    add_role_names = []
    while True:
        role = get_multiple_roles()
        if role:
            role_id = role['id']
            role_name = role['name']
            add_roles_str.append(str(role_id))
            add_role_names.append(role_name)
        else :
            break

    console.print("\n[bold cyan]Unassign Roles to the User[/bold cyan]\n")
    remove_roles = []
    remove_roles_str = []
    remove_role_names = []
    while True:
        role = get_multiple_roles()
        if role:
            role_id = role['id']
            role_name = role['name']
            remove_roles_str.append(str(role_id))
            remove_role_names.append(role_name)
        else :
            break
    
    if not add_roles_str:
            console.print("\n[yellow]No role was selected for assignment to user[/yellow]")
    else:
        add_roles = list(dict.fromkeys(role_id.strip() for role_id in add_roles_str))
        console.print(f"\n[bold cyan]Assigning_roles: [/bold cyan]{add_role_names}")

    if not remove_roles_str:
            console.print("[yellow]No role was selected for unassignment to user[/yellow]\n")
    else:
        remove_roles = list(dict.fromkeys(role_id.strip() for role_id in remove_roles_str))
        console.print(f"[bold red]Unassigning_roles: [/bold red]{remove_role_names}\n")

    if not add_roles_str and not remove_roles_str:
            console.print("[red]Error: At least one of 'Adding Roles' or 'Removing Roles' is required. Aborting operation.[/red]")
            return None

    payload_data = {
        "user_id": user_id,
        "add_roles": add_roles,
        "remove_roles": remove_roles 
    }

    user_manager = UserManager()
    response = user_manager.assign_role(payload_data=payload_data)

    # Display response in a structured format
    # console.print(Panel.fit(f"[bold green]{response['message']}[/bold green]", title="✅ Status", border_style="green"))
    console.print(f"[bold green]{response['message']}[/bold green]")

    if response["added_roles"]:
        console.print(f"[bold cyan]➕ Added Roles:[/bold cyan] {', '.join(response['added_roles'])}")
    else:
        console.print(f"[bold cyan]➕ Added Roles:[/bold cyan] None")

    if response["removed_roles"]:
        console.print(f"[bold red]❌ Removed Roles:[/bold red] {', '.join(response['removed_roles'])}\n")
    else:
        console.print(f"[bold red]❌ Removed Roles:[/bold red] None\n")

@users.command(name='update')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def update_user():
    """Update an existing user by their ID."""
    user_manager = UserManager()
    table_display = TableDisplay()
       
    console.print("\n[bold blue]Update user (interactive mode)[/bold blue]")

    current_user = get_single_user()
    user_id = current_user['id']
   
    if not user_id:
        console.print("[red]User ID is required. Aborting operation.[/red]")
        return
           
    # Show current values and ask for updates
    console.print(f"\n[bold]Updating User ID: {user_id}[/bold]")
    console.print("[italic]Press Enter to keep current values or type new values.[/italic]\n")
   
    username = Prompt.ask("[bold]Username[/bold]", default=current_user.get('username', ''))
    email = Prompt.ask("[bold]Email[/bold]", default=current_user.get('email', ''))
    first_name = Prompt.ask("[bold]First Name[/bold]", default=current_user.get('first_name', ''))
    last_name = Prompt.ask("[bold]Last Name[/bold]", default=current_user.get('last_name', ''))
   
    # Convert boolean to string for the prompt
    current_active = "true" if current_user.get('is_active') else "false"
    active_status = Prompt.ask(
        "[bold]Active Status (true/false)[/bold]",
        choices=["true", "false"],
        default=current_active
    )
   
    # Prepare user data for update
    user_data = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "is_active": active_status.lower() == "true"
    }
   
    # Show summary before confirming
    console.print("\n[bold]Update Summary:[/bold]")
    for key, value in user_data.items():
        console.print(f"{key.title()}: {value}")
   
    if Prompt.ask("\n[bold]Update user?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]User update cancelled.[/yellow]")
        return
   
    # Call the user manager to perform the update
    updated_response = user_manager.update_user(user_data,user_id)
   
    if updated_response:
        console.print("[green]User updated successfully![/green]")
        table_display.display_table(
            response_data={'results': [updated_response], 'count': 1},
            columns=user_manager.columns,
            title_prefix="Updated User",
            row_formatter=table_display.format_user_row
        )
    else:
        console.print("[red]Failed to update the user.[/red]")
 
 
@users.command(name='delete')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def delete_user():
    """Delete an existing user by their ID."""
    user_manager = UserManager()
       
    console.print("\n[bold blue]Delete user (interactive mode)[/bold blue]")

    current_user = get_single_user()
    user_id = current_user['id']
   
    if not user_id:
        console.print("[red]User ID is required. Aborting operation.[/red]")
        return
 
    if Prompt.ask("\n[bold]Are you sure you want to delete this user?[/bold]", choices=["yes", "no"], default="no") == "no":
        console.print("[yellow]User deletion cancelled.[/yellow]")
        return None  
   
    # Call the user manager to perform the deletion
    user_manager.delete_user(user_id)
    console.print("[green]User deleted successfully![/green]")


if __name__ == "__main__":
    users()
