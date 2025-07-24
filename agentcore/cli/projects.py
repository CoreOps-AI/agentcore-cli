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
from datetime import datetime,timedelta
from typing import Tuple

from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.users_manager import UserManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list
from agentcore.cli.config import ConfigManager
from agentcore.managers.users_manager import demo_user_check

install()

console = Console()

#Helper functions
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
def get_project_type(default_project_type_id=None):
    """Get project type list with tab completion (name only) and return full type dict."""
    
    project_manager = ProjectManager()
    base_manager = BaseManager()
    project_types = project_manager.project_types()

    if not project_types:
        console.print("[red]No project types found.[/red]")
        return None

    # Create mapping: type_name => full project_type dict
    formatted_map = {
        project_type["type_name"]: project_type
        for project_type in project_types
        if "type_name" in project_type
    }
    formatted_names = sorted(formatted_map.keys())

    # Find default project type name if default_project_type_id is provided
    default_project_type_name = None
    if default_project_type_id:
        for project_type in project_types:
            if str(project_type.get("id")) == str(default_project_type_id):
                default_project_type_name = project_type.get("type_name")
                break

    while True:
        # Show current default if exists
        if default_project_type_name:
            console.print(f"\n[dim]Current: {default_project_type_name}[/dim]")
        
        console.print("\n[bold]Enter Project Type (press Tab for suggestions, Enter for selection, or just Enter to keep current):[/bold]")
        selected_project_type = base_manager.get_input_with_tab_completion("Project Types", formatted_names)

        # If user just pressed Enter and we have a default, use it
        if not selected_project_type.strip() and default_project_type_name:
            selected_project_type = default_project_type_name

        if selected_project_type in formatted_map:
            project_type = formatted_map[selected_project_type]
            console.print(f"\n[green]✅ Selected Project Type:[/green] {selected_project_type}")

            console.print("[bold]Selected Project Type Details:[/bold]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [project_type]},
                columns=project_manager.project_types_columns,
                title_prefix="Selected Project Type",
                row_formatter=table_display.format_project_row
            )
            return project_type
        else:
            console.print(f"\n[yellow]⚠️ '{selected_project_type}' is not a valid project type.[/yellow]")
            suggestions = [p for p in formatted_names if selected_project_type.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

@BaseManager.handle_api_error
def get_multiple_users():
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
        
        console.print("\n[bold]Enter a username or email to assign to the project (press Tab for suggestions, Enter to confirm):[/bold]")
        console.print("[bold]Leave empty if you don't want to assign any user.[/bold]")
        selected_user = base_manager.get_input_with_tab_completion("Usernames", formatted_names)
        
        if not selected_user:
            return None
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

def is_length_valid(value: str, field: str) -> Tuple[bool, str]:
    val = value.strip()
    field_title = field.title()

    if field == "name":
        if not (3 <= len(val) <= 20):
            return False, f"{field_title} must be between 3 and 20 characters."
    elif field == "description":
        if len(val) < 5:
            return False, f"{field_title} must be at least 5 characters long."
    
    return True, ""


#CLI functions
@click.group()
def projects():
    """Project management commands."""
    pass


@projects.command(name='view')
@BaseManager.handle_api_error
def view_projects():
    """View all projects with pagination and table display."""
    project_manager = ProjectManager()
    table_display = TableDisplay()
    base_manager = BaseManager()
    
    response = project_manager.view_projects()
    
    if not response:
            console.print("[yellow]No projects assigned.[/yellow]\n")
            return
    active =[]
    archived =[]
    for project in response:
        if 'project_type' in project and isinstance(project['project_type'], dict):
            project['project_type'] = project['project_type'].get('type_name', 'N/A')
            project['start'] = beautify_datetime(project['start'],date_only = True)
            project['finish'] = beautify_datetime(project['finish'], date_only = True)
            if project['is_archived'] :
                archived.append(project)
            else:
                active.append(project)
    status_mapping = {
        "1": ("All Projects", response),
        "2": ("Active Projects", active),
        "3": ("Archived Projects", archived)
    }

    status_choice = Prompt.ask(
        "\n[bold]Choose an option to view projects:[/bold]\n"
        + "\n".join([f"{key}. {label}" for key, (label, _) in status_mapping.items()]),
        choices=status_mapping.keys(),
        default="1"
    )

    title_prefix, selected_data = status_mapping[status_choice]

    selected_project = base_manager.paginate_data(
        data=selected_data,
        columns=project_manager.columns,
        title_prefix=title_prefix,
        row_formatter=table_display.format_project_row,  # Method that needs columns
        search_fields=['id', 'name'],
        allow_selection=True,
        selection_field='id',
        page_size=10
    )
    if selected_project:
        console.print(f"Selected project: [green]{selected_project['name']}[/green]")
        # Use selected_project for further operations
        

@projects.command(name='create')
@BaseManager.handle_api_error(show_details=True)
def create_project():
    """Create a new project through an interactive prompt."""

    project_manager = ProjectManager()
    user_manager = UserManager()
    base_manager = BaseManager()
    
    is_demo_user = user_manager.is_demo_user()

    console.print("\n[bold blue]Create New Project[/bold blue]\n")
    
    # Assuming inside a method where `self.is_length_valid()` is accessible

    while True:
        name = Prompt.ask("[bold]Project Name[/bold]").strip()
        valid, msg = is_length_valid(name, "name")
        if valid:
            break
        console.print(f"[red]{msg}[/red]")

    while True:
        description = Prompt.ask("[bold]Project Description[/bold]").strip()
        valid, msg = is_length_valid(description, "description")
        if valid:
            break
        console.print(f"[red]{msg}[/red]")


    # status_mapping = {"1": "planned", "2": "in_progress", "3": "completed", "4": "on_hold"}
    # status_choice = Prompt.ask(
    #     "\n[bold]Choose a project status:[/bold]\n1. Planned\n2. In Progress\n3. Completed\n4. On Hold\n",
    #     choices=status_mapping.keys(),
    #     default="1"
    # )
    # status = status_mapping[status_choice]

    today = datetime.today().strftime("%Y-%m-%d")

    # Prompt for valid start date
    while True:
        start = Prompt.ask("[bold]Start Date[/bold] (YYYY-MM-DD)", default=today) or None
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            break
        except ValueError:
            console.print("[red]❌ Invalid start date format. Please use YYYY-MM-DD format.[/red]")

    # Compute default finish date as one day after start
    default_finish = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d")

    # Prompt for valid finish date that is not before start date
    while True:
        finish = Prompt.ask("[bold]Finish Date[/bold] (YYYY-MM-DD)", default=default_finish) or None
        try:
            finish_dt = datetime.strptime(finish, "%Y-%m-%d")
            if finish_dt <= start_dt:
                console.print("[red]❌ Finish date cannot be before the start date. Please enter again.[/red]")
            else:
                break
        except ValueError:
            console.print("[red]❌ Invalid finish date format. Please use YYYY-MM-DD.[/red]")

    # deployed = Prompt.ask("[bold]Is the project deployed?[/bold] (yes/no)", choices=['yes', 'no'], default="no") == "yes"
    if is_demo_user:
        console.print("\n[yellow]For trial version, you can choose only: Classification, Timeseries, or Regression.[/yellow]")

        while True:
            project_type = get_project_type()
            if project_type['type_name'] in ["Classification", "Timeseries", "Regression"]:
                break
            else:
                console.print("[red]❌ Invalid selection. Please select from the allowed options only.[/red]")
    else:
        project_type = get_project_type()

    if not project_type:
            # console.print("[red]No project types found.[/red]")
            return None
        
    project_type_id = project_type['id']
    # Use selected project_type_id in payload
    console.print(f"[green]You selected project type:[/green] {project_type['type_name']} (ID: {project_type_id})\n")

    add_users_str = []
    add_users_names =[]
    
    if not is_demo_user:
        # Assign User
        console.print("\n[bold blue]Assign Users:[/bold blue]")
        while True:
            user = get_multiple_users()
            if user:
                user_id = user['id']
                user_name = user['username']
                add_users_str.append(str(user_id))
                add_users_names.append(user_name)
            else :
                break

    project_data = {
        'name': name,
        'description': description,
        'status': "planned",
        'start': start,
        'finish': finish,
        'project_type_id': project_type_id
    }

    missing_fields = [key for key, value in project_data.items() if not value]

    if missing_fields:
        console.print("")
        for key in missing_fields:
            console.print(f"[red]Error: {key} is required. Aborting operation.[/red]")
        console.print("")   
        exit(1)  # Exit with an error code

    # project_data['deployed'] = deployed
    console.print("\n[bold green]Project Summary:[/bold green]")
    for key, value in project_data.items():
        console.print(f"{key.title()}: {value}")

    if not is_demo_user and add_users_str:
        add_users = list(dict.fromkeys(user_id.strip() for user_id in add_users_str))
        add_users_names = list(dict.fromkeys(add_users_names))
        console.print(f"Assigning_users: {add_users_names}")
    elif not is_demo_user:
        console.print("[yellow]No user was selected for assignment to the project.[/yellow]")

    if Prompt.ask("\n[bold]Create project?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Project creation cancelled.[/yellow]\n")
        return None

    created_project = project_manager.create_project(project_data)
    if not created_project:
        console.print("[red]Project creation Failed[/red]\n")
        return None
    
    console.print("[bold green]Project created successfully[/bold green]\n")
    project_id = created_project['id']

    if not is_demo_user and add_users_str:

        payload_data = {
            "project_id": project_id,
            "add_users": add_users,
            "remove_users": []
        }

        response = project_manager.users_assign(project_id, payload_data)

        if not response:
            console.print("[red]User assign operation failed[/red]")

        if "message" in response:
            console.print(f"[bold green]{response['message']}[/bold green]")

        added = response.get("added_users", [])
        if added:
            console.print(f"[bold cyan]➕ Added Users:[/bold cyan] {', '.join(added)}")
        else:
            console.print(f"[bold cyan]➕ Added Users:[/bold cyan] None")

        # Inactive Users
        inactive = response.get("inactive_users", [])
        if inactive:
            console.print(f"[bold yellow]⚠️ Inactive Users Skipped:[/bold yellow] {', '.join(inactive)}")
        else:
            console.print(f"[bold yellow]⚠️ Inactive Users Skipped:[/bold yellow] None")

        # Warnings
        warnings = response.get("warnings", [])
        if warnings:
            console.print("[bold magenta]⚠️ Warnings:[/bold magenta]")
            for warning in warnings:
                console.print(f"  - {warning}")
            console.print("\n")

    project_details = project_manager.fetch_project(project_id)

    if project_details == -1 or not project_details:
        console.print(f"[red]No project found with ID {project_id} Exiting.[/red]")
        return None

    if 'project_type' in project_details and isinstance(project_details['project_type'], dict):
        project_details['project_type'] = project_details['project_type'].get('type_name', 'N/A')

    # Format date-time fields
    if project_details.get("start"):
        project_details["start"] = beautify_datetime(project_details["start"])

    if project_details.get("finish"):
        project_details["finish"] = beautify_datetime(project_details["finish"])

    if project_details:
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [project_details], 'count': 1},
            columns=project_manager.columns,
            title_prefix="Created Project",
            row_formatter=table_display.format_project_row
        )

@projects.command(name='github')
@BaseManager.handle_api_error
def set_project_details():
    """Set or update GitHub repository URL for a project."""
    console = Console()
    project_manager = ProjectManager()

    # --- Required Fields ---
    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    github_repo = Prompt.ask("[bold]GitHub repository URL[/bold]").strip()
    if not github_repo:
        console.print("[red]Error: GitHub repository URL is required. Aborting operation.[/red]")
        return

    # First, check if the project already has a GitHub URL
    console.print("[yellow]Checking if project already has a GitHub URL...[/yellow]")
    existing_url = project_manager.get_project_github_url(project_id)
    
    if existing_url:
        console.print(f"[yellow]Project already has GitHub URL: {existing_url}[/yellow]")
        update_choice = Prompt.ask(
            "[bold]Do you want to update the existing GitHub URL?[/bold]",
            choices=["yes", "no"],
            default="no"
        )
        
        if update_choice.lower() != "yes":
            console.print("[yellow]Operation cancelled.[/yellow]")
            return
        
        operation = "update"
    else:
        console.print("[green]No existing GitHub URL found. Creating new one...[/green]")
        operation = "create"

    # Call the manager
    result = project_manager.set_project_details(
        project_id=project_id,
        github_repo=github_repo,
        operation=operation
    )

    # Display output
    if result:
        table = Table(
            title=f"Project GitHub URL {'Updated' if operation == 'update' else 'Created'} Successfully",
            title_style="bold magenta",
            border_style="blue",
            header_style="bold cyan"
        )

        table.add_column("Field")
        table.add_column("Value")

        table.add_row("Project ID", str(project_id))
        table.add_row("GitHub Repository URL", github_repo)
        table.add_row("Operation", operation.title())
        
        if operation == "update" and existing_url:
            table.add_row("Previous URL", existing_url)

        console.print(table)
    else:
        console.print("[red]Failed to set project details. Please check the logs above.[/red]")

        
@projects.command(name='update')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def update_project():
    """Update an existing project by its ID."""

    console.print("\n[bold blue]Update Project[/bold blue]")
    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    project_manager = ProjectManager()
    
    # Collect updated details
    # Ask all questions first
    name = Prompt.ask("[bold]New Name[/bold]", default=project_details.get('name', ''))
    description = Prompt.ask("[bold]New Description[/bold]", default=project_details.get('description', ''))

    status_mapping = {"1": "planned", "2": "in_progress", "3": "completed", "4": "on_hold"}
    status_choice = Prompt.ask(
        f"\n[bold]Choose a project status:[/bold]\n1. Planned\n2. In Progress\n3. Completed\n4. On Hold\n",
        choices=status_mapping.keys(),
        default=str(list(status_mapping.keys())[list(status_mapping.values()).index(project_details.get('status', 'planned'))])
    )
    status = status_mapping[status_choice]

    # Prepare defaults with beautified existing values or today's date
    default_start = beautify_datetime(project_details['start'],date_only=True) if project_details.get('start') else datetime.today().strftime("%Y-%m-%d")
    default_finish = beautify_datetime(project_details['finish'],date_only=True) if project_details.get('finish') else datetime.today().strftime("%Y-%m-%d")

    # Prompt for start date
    while True:
        start = Prompt.ask("[bold]New Start Date[/bold] (YYYY-MM-DD)", default=default_start)
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            break
        except ValueError:
            console.print("[red]❌ Invalid start date format. Please use YYYY-MM-DD.[/red]")

    # Prompt for finish date
    while True:
        finish = Prompt.ask("[bold]New Finish Date[/bold] (YYYY-MM-DD)", default=default_finish)
        try:
            finish_dt = datetime.strptime(finish, "%Y-%m-%d")
            if finish_dt <= start_dt:
                console.print("[red]❌ Finish date cannot be before the start date. Please enter again.[/red]")
            else:
                break
        except ValueError:
            console.print("[red]❌ Invalid finish date format. Please use YYYY-MM-DD.[/red]")

    # default_deployed = "yes" if project_details.get('deployed', False) else "no"
    # deployed = Prompt.ask("[bold]Is the project deployed?[/bold]", choices=['yes', 'no'], default=default_deployed) == "yes"

    # Get current project type ID for default
    current_project_type_id = project_details.get('project_type_id')

    # Get project type with default
    project_type = get_project_type(default_project_type_id=current_project_type_id)
    if not project_type:
        console.print("[red]Project type selection failed.[/red]")
        return None

    project_type_id = project_type['id']
    console.print(f"[green]You selected project type:[/green] {project_type['type_name']} (ID: {project_type_id})\n")

    # Create the updated_data dictionary
    updated_data = {
        'name': name,
        'description': description or "",
        'status': status or "planned",
        'start': start,
        'finish': finish,
        'project_type_id': project_type_id
    }


    console.print("\n[bold]Updated Project Data:[/bold]")
    for key, value in updated_data.items():
        console.print(f"{key.title()}: {value}")

    if Prompt.ask("\n[bold]Confirm Update?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Project update cancelled.[/yellow]\n")
        return None

    updated_response = project_manager.update_project(project_id, updated_data)
    if 'project_type' in updated_response and isinstance(updated_response['project_type'], dict):
        updated_response['project_type'] = updated_response['project_type'].get('type_name', 'N/A')
    if updated_response.get("start"):
        updated_response["start"] = beautify_datetime(updated_response["start"],date_only=True)
    if updated_response.get("finish"):
        updated_response["finish"] = beautify_datetime(updated_response["finish"],date_only=True)

    if updated_response:
        console.print("[green]Project updated successfully![/green]")
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [updated_response], 'count': 1},
            columns=project_manager.columns,
            title_prefix="Updated Project",
            row_formatter=table_display.format_project_row
        )
    else:
        console.print("[red]Failed to update the project.[/red]")

@projects.command(name='assign-user')
@BaseManager.demo_user_check
@BaseManager.handle_api_error
def assign_users():
    "Assigns users to the project"

    project_manager = ProjectManager()

    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    # Assinging Users
    console.print("\n[bold blue]Assign Users:[/bold blue]")
    add_users_str = []
    add_users_names =[]
    while True:
        user = get_multiple_users()
        if user:
            user_id = user['id']
            user_name = user['username']
            add_users_str.append(str(user_id))
            add_users_names.append(user_name)
        else :
            break
    if not add_users_str:
        console.print("\n[yellow]No user was selected for assignment to the project.[/yellow]")
        add_users = []

    else :
        # Final cleaned list of user IDs
        add_users = list(dict.fromkeys(user_id.strip() for user_id in add_users_str))
        console.print(f"\n[bold cyan]Assigning_users: [/bold cyan]{add_users_names}")

    # Unassigning Users
    console.print("\n[bold blue]Unassign Users:[/bold blue]")
    remove_users_str = []
    remove_users_names = []
    while True:
        user = get_multiple_users()
        if user:
            user_id = user['id']
            user_name = user['username']
            remove_users_str.append(str(user_id))
            remove_users_names.append(user_name)
        else :
            break
    if not remove_users_str:
        console.print("\n[yellow]No user was selected for unassignment to the project.[/yellow]")
        remove_users = []

    else :
        # Final cleaned list of user IDs
        remove_users = list(dict.fromkeys(user_id.strip() for user_id in remove_users_str))
        console.print(f"\n[bold red]Unassigning_users: [/bold red]{remove_users_names}")

    if not add_users_str and not remove_users_str:
        console.print("[red]Error: At least one of 'Adding Users' or 'Removing Users' is required. Aborting operation.[/red]")
        return None

    payload_data = {
        "project_id": project_id,
        "add_users": add_users,
        "remove_users": remove_users
    }

    response = project_manager.users_assign(project_id, payload_data)

    if not response:
        return
    if "message" in response:
        console.print(f"\n[bold green]{response['message']}[/bold green]\n")

    added = response.get("added_users", [])
    if added:
        console.print(f"[bold cyan]➕ Added Users:[/bold cyan] {', '.join(added)}")
    else:
        console.print(f"[bold cyan]➕ Added Users:[/bold cyan] None")

    # Removed Users
    removed = response.get("removed_users", [])
    if removed:
        console.print(f"[bold red]❌ Removed Users:[/bold red] {', '.join(removed)}")
    else:
        console.print(f"[bold red]❌ Removed Users:[/bold red] None")

    # Inactive Users
    inactive = response.get("inactive_users", [])
    if inactive:
        console.print(f"[bold yellow]⚠️ Inactive Users Skipped:[/bold yellow] {', '.join(inactive)}")
    else:
        console.print(f"[bold yellow]⚠️ Inactive Users Skipped:[/bold yellow] None")

    # Warnings
    warnings = response.get("warnings", [])
    if warnings:
        console.print("[bold magenta]⚠️ Warnings:[/bold magenta]")
        for warning in warnings:
            console.print(f"  - {warning}")
        console.print("\n")


@projects.command(name="archive")
# @BaseManager.demo_user_check
@BaseManager.handle_api_error
def archive_project():
    """Archive or Unarchive a project."""

    project_manager = ProjectManager()

    project_details = get_project_list()
    project_id = project_details['id']
    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    payload = {
        "is_archived": None
    }

    if project_details['is_archived']:
        payload["is_archived"] = False
        message = "Unarchive"
    else:
        payload["is_archived"] = True
        message = "Archive"
    
    if Prompt.ask(f"\n[bold]Are you sure you want to {message} this project?[/bold]", choices=["yes", "no"], default="no") == "no":
        console.print("[yellow]Operation cancelled.[/yellow]\n")
        return None
    
    response = project_manager.project_archive(project_id, payload)
    if response:
        console.print(f"\n[green]{response['message']}[/green]\n")

@projects.command(name='metrics')
@BaseManager.handle_api_error
# @BaseManager.demo_user_check
def project_metrics():
    """View project metrics."""
    project_manager = ProjectManager()
    base_manager = BaseManager()
    
    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None
    
    response = project_manager.project_metrics(project_id)
    if not response:
        console.print("[yellow]No metrics found for this project.[/yellow]")
        query = "\n[bold]Choose an action[/bold] (1: Add Metrics, q: Quit)"
        choices = ["1", "q"]  # Add, Quit only
    else:
        for metric in response:
            metric['created_at'] = beautify_datetime(metric.get("created_at", ""))
            metric['updated_at'] = beautify_datetime(metric.get("updated_at", ""))

        response.sort(key=lambda x: x['id'])

        console.print("[green]Project Metrics[/green]")
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': response},
            columns=project_manager.metrics_columns,
            title_prefix="Project Metrics",
            row_formatter=table_display.format_project_row
        )
        choices = ["1", "2", "3", "q"]  # Add, Update, Delete, Quit
        query = "\n[bold]Choose an action[/bold] (1: Add Metrics, 2: Update Metrics, 3: Delete Metrics, q: Quit)"

    mode = Prompt.ask(
        query,
        choices=choices,
        default="q"
    )

    if mode == "q":
        return

    if mode == "1":
        add_project_metric(project_manager, base_manager, project_id)
    elif mode == "2":
        update_project_metric(project_manager, response, project_id)
    elif mode == "3":
        delete_project_metric(project_manager, response, project_id)

@BaseManager.handle_api_error
def add_project_metric(project_manager, base_manager, project_id):

    project_manager = ProjectManager()
    base_manager = BaseManager()

    response = project_manager.fetch_metric_definitions()
    metric_names = [metric['name'] for metric in response]

    selected_metric = base_manager.get_input_with_tab_completion("Metrics", metric_names)
    selected_metric = [item for item in response if item['name'] == selected_metric]

    if not selected_metric:
        console.print("[red]No metrics found with the given name or no metrics selected.[/red]\n")
        return

    threshold_value = Prompt.ask("\n[bold]Enter the threshold value for the metrics[/bold]").strip()
    description = Prompt.ask("[bold]Enter a description for the metrics (optional)[/bold]").strip() or None

    if not threshold_value:
        console.print("[red]Error: Threshold value is required.[/red]\n")
        return

    payload = {
        "metric": selected_metric[0]['id'],
        "threshold_value": threshold_value,
        "description": description,
        "project": project_id,
    }

    response = project_manager.post_project_metrics(payload=payload)
    
    if response:
        response['created_at'] = beautify_datetime(response.get("created_at", ""))
        response['updated_at'] = beautify_datetime(response.get("updated_at", ""))
        console.print("\n[green]Created Metrics[/green]")
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [response]},
            columns=project_manager.metrics_columns,
            title_prefix="Created Metrics",
            row_formatter=table_display.format_project_row
        )
    else:
        console.print("[red]Addition of metrics failed[red]\n")

@BaseManager.handle_api_error
def update_project_metric(project_manager, metrics, project_id):

    project_manager = ProjectManager()
    base_manager = BaseManager()

    metric_ids = [str(metric['id']) for metric in metrics]
    selected_id = None
    while selected_id not in metric_ids:
        selected_id = Prompt.ask("\nEnter the Metrics ID to update")
        if selected_id not in metric_ids:
            console.print("[red]❌ Invalid Metrics ID. Please choose a valid one from the table.[/red]")
        else:
            selected_metric = next((m for m in metrics if str(m['id']) == selected_id), None)

    selected_metric['created_at'] = beautify_datetime(selected_metric.get("created_at", ""))
    selected_metric['updated_at'] = beautify_datetime(selected_metric.get("updated_at", ""))

    console.print("[green]Selected Metrics[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': [selected_metric]},
        columns=project_manager.metrics_columns,
        title_prefix="Selected Metrics",
        row_formatter=table_display.format_project_row
    )
    # selected_id = Prompt.ask("Enter the Metric ID to update", choices=metric_ids)
    console.print("[italic]Press Enter to keep current values or type new values.[/italic]\n")

    threshold_value = Prompt.ask("New Threshold Value", default=str(selected_metric.get('threshold_value', '')))
    description = Prompt.ask("New Description", default=selected_metric.get('description', ''))

    payload = {
        "project_id": project_id,
        "id": selected_id,
        "threshold_value": threshold_value,
        "description": description
    }

    console.print("\n[bold]Updated Metrics Data:[/bold]")
    for key, value in payload.items():
        console.print(f"{key.title()}: {value}")

    if Prompt.ask("\n[bold]Confirm Update?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Merics update cancelled.[/yellow]\n")
        return None

    response = project_manager.update_project_metrics(payload=payload)

    if response:
        console.print("[green]✅ Metrics updated successfully.[/green]")
        response['created_at'] = beautify_datetime(response.get("created_at", ""))
        response['updated_at'] = beautify_datetime(response.get("updated_at", ""))

        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': [response]},
            columns=project_manager.metrics_columns,
            title_prefix="Updated Metrics",
            row_formatter=table_display.format_project_row
        )

@BaseManager.handle_api_error
def delete_project_metric(project_manager, metrics, project_id):

    project_manager = ProjectManager()
    base_manager = BaseManager()

    metric_ids = [str(metric['id']) for metric in metrics]
    selected_id = None
    while selected_id not in metric_ids:
        selected_id = Prompt.ask("\nEnter the Metrics ID to update")
        if selected_id not in metric_ids:
            console.print("[red]❌ Invalid Metrics ID. Please choose a valid one from the table.[/red]")
        else:
            selected_metric = next((m for m in metrics if str(m['id']) == selected_id), None)

    selected_metric['created_at'] = beautify_datetime(selected_metric.get("created_at", ""))
    selected_metric['updated_at'] = beautify_datetime(selected_metric.get("updated_at", ""))

    console.print("[green]Selected Metrics[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': [selected_metric]},
        columns=project_manager.metrics_columns,
        title_prefix="Selected Metrics",
        row_formatter=table_display.format_project_row
    )

    # selected_id = Prompt.ask("Enter the Metric ID to delete", choices=metric_ids)
    confirm = Prompt.ask("Are you sure you want to delete this metrics?", choices=["yes", "no"], default="no")
    if confirm == "yes":
        project_manager.delete_project_metrics(project_id=project_id, id=selected_id)
        console.print("[red]🗑️ Metrics deleted successfully.[/red]\n")
    else:
        console.print("[yellow]Deletion cancelled.[/yellow]\n")



if __name__ == "__main__":
    projects()