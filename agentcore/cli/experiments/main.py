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
from rich.prompt import Prompt, Confirm
from rich.traceback import install
from rich.table import Table
from typing import List, Dict, Tuple, Optional, Any
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from datetime import datetime
from rich.box import MINIMAL_HEAVY_HEAD
from rich.panel import Panel
import os
import csv
from datetime import datetime
import os
import csv
from rich.panel import Panel
from rich.table import Table
from rich import box

from agentcore.managers.experiment_manager import ExperimentManager
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.experiments_manager import ExperimentsManager


install()
console = Console()


def beautify_datetime(dt_str):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Zulu time to UTC offset
        dt = datetime.fromisoformat(dt_str)  # Handles ISO format with T and timezone
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return 


def select_data_version(data_versions: List[Dict], table_display: TableDisplay) -> int:
    """Select a data version from the list. Automatically selects if only one version exists."""
    if not data_versions:
        console.print("[yellow]No data versions available.[/yellow]")
        return None
        
    # If there's only one data version, select it automatically
    if len(data_versions) == 1:
        version_id = data_versions[0]['id']
        console.print(f"[green]Automatically selected the only available data version:[/green] "
                     f"ID: {version_id}, Datasource: {data_versions[0].get('data_source', 'N/A').get('description', 'N/A')}")
        return version_id
    
    # If multiple data versions, let user choose one
    console.print("\n[bold]Select a data version by ID:[/bold]")
    
    try:
        version_id_input = Prompt.ask("[bold]Enter Data Version ID[/bold]")
        version_id = int(version_id_input)
        
        # Verify the data version ID exists
        if any(version['id'] == version_id for version in data_versions):
            selected_version = next(version for version in data_versions if version['id'] == version_id)
            console.print(f"[green]Selected data version:[/green] "
                         f"ID: {version_id} , Datasource: {data_versions[0].get('data_source', 'N/A').get('description', 'N/A')}")
            return version_id
        else:
            console.print("[red]Invalid data version ID. Please try again.[/red]")
            return select_data_version(data_versions, table_display)
    except ValueError:
        console.print("[red]Please enter a valid numeric ID.[/red]")
        return select_data_version(data_versions, table_display)

def display_columns(columns_data: Dict[str, Any], table_display: TableDisplay):
    """Display available columns using Rich Table directly."""
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns found for this data version.[/yellow]")
        return
    
    # Get column names
    column_names = columns_data.get('columns', [])
    
    # Create a table using Rich directly
    table = Table(title=f"Available Columns (Table: {columns_data.get('table_name', 'N/A')})")
    
    # Add columns to the table
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Column Name", style="green")
    
    # Add rows to the table
    for idx, column_name in enumerate(column_names, 1):
        table.add_row(str(idx), column_name)
    
    # Display the table directly
    console.print(table)

def select_column(columns_data: Dict[str, Any], table_display: TableDisplay) -> str:
    """Allow user to select a column from the available columns."""
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns available to select.[/yellow]")
        return None
    
    # Display available columns
    display_columns(columns_data, table_display)
    
    # Create a list of column names for autocompletion - handle list of strings
    column_names = columns_data.get('columns', [])
    column_completer = FuzzyWordCompleter(column_names)
    
    console.print("\n[bold]Select a column:[/bold]")
    console.print("[dim]You can type part of the column name and press Tab for suggestions[/dim]")
    console.print("[dim]Tip: For target column selection, consider categorical columns like 'seller', 'buyer_name', etc.[/dim]")
    
    # Get user input with autocompletion
    selected_column = prompt(
        "Column name: ",
        completer=column_completer,
        complete_while_typing=True
    )
    
    # Verify the column exists
    if selected_column in column_names:
        console.print(f"[green]Selected column:[/green] {selected_column}")
        return selected_column
    else:
        console.print("[yellow]Column not found. Please try again.[/yellow]")
        return select_column(columns_data, table_display)
    
def create_project_completer(projects: List[Dict]) -> FuzzyWordCompleter:
    """Create a fuzzy completer for project names."""
    project_names = [
        f"{p['name']} (ID: {p['id']})" for p in projects
    ]
    return FuzzyWordCompleter(project_names)

def search_projects(projects: List[Dict], search_term: str) -> Tuple[List[Dict], Optional[Dict]]:
    """
    Search projects based on name using case-insensitive matching.
    
    Returns:
        Tuple containing:
        - List of matching projects
        - Exact match project (if found) or None
    """
    if not search_term:
        return projects, None

    # Check for exact matches first (case insensitive)
    exact_matches = [
        project for project in projects
        if search_term.lower() == project['name'].lower()
    ]
    
    if exact_matches:
        return exact_matches, exact_matches[0]
    
    # Check if search term contains a project ID
    project_id = get_project_id_from_selection(search_term)
    if project_id:
        id_matches = [p for p in projects if p['id'] == project_id]
        if id_matches:
            return id_matches, id_matches[0]
    
    # Return partial matches
    filtered_projects = [
        project for project in projects
        if search_term.lower() in project['name'].lower()
    ]
    
    return filtered_projects, None

def display_filtered_projects(projects: List[Dict], table_display: TableDisplay):
    """Display filtered projects in a table."""
    if not projects:
        console.print("[yellow]No matching projects found.[/yellow]")
        return

    response_data = {'results': projects}
    BaseManager.paginate_data(
        data=projects,
        columns=ProjectManager().columns,
        title_prefix="Matching Projects",
        row_formatter=table_display.format_project_row,
        search_fields=["id", "name", "description"],  # adjust as per your project fields
        allow_selection=True,  # set to True if you want the user to select a project
        page_size=10
    )

def get_project_id_from_selection(selection: str) -> Optional[int]:
    """Extract project ID from the selection string."""
    try:
        if "ID: " in selection:
            return int(selection.split("ID: ")[-1].rstrip(")"))
        return None
    except (ValueError, IndexError):
        return None

def select_project(projects: List[Dict], table_display: TableDisplay) -> Tuple[int, Dict]:
    """Streamlined project selection with automatic selection for good matches."""
    # Display all projects initially
    console.print("\n[bold]Available Projects:[/bold]")
    display_filtered_projects(projects, table_display)

    while True:
        # Create completer for project names
        project_completer = create_project_completer(projects)
        
        # Get user input with autocompletion
        console.print("\n[bold]Search for a project (type to search, use tab for suggestions, or press enter to see all):[/bold]")
        console.print("[dim]Tip: You can type part of the project name or ID and press Tab for suggestions[/dim]")
        
        user_input = prompt(
            "Project search: ",
            completer=project_completer,
            complete_while_typing=True
        )

        # Search for matches
        filtered_projects, exact_match = search_projects(projects, user_input)
        
        # Auto-select if we have an exact match
        if exact_match:
            project_id = exact_match['id']
            console.print(f"[green]Found exact match:[/green] {exact_match['name']} (ID: {project_id})")
            return project_id, exact_match
            
        # Auto-select if we have exactly one match from partial search
        elif len(filtered_projects) == 1:
            project_id = filtered_projects[0]['id']
            console.print(f"[green]Found single match:[/green] {filtered_projects[0]['name']} (ID: {project_id})")
            return project_id, filtered_projects[0]
            
        # Display filtered results and continue with manual selection
        elif filtered_projects:
            display_filtered_projects(filtered_projects, table_display)
            
            # Allow direct ID entry
            try:
                project_id_input = Prompt.ask(
                    "\n[bold]Enter Project ID[/bold] or press Enter to continue searching",
                    default=""
                )
                
                if project_id_input:
                    project_id = int(project_id_input)
                    selected_project = next((p for p in projects if p['id'] == project_id), None)
                    if selected_project:
                        return project_id, selected_project
                    else:
                        console.print("[red]Invalid project ID. Please try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid numeric ID.[/red]")
        else:
            # No matches found
            console.print("[yellow]No matching projects found. Try a different search term.[/yellow]")
            display_filtered_projects(projects, table_display)

def select_instance(instances: List[Dict]) -> int:
    """Select an instance from the list. Automatically selects if only one instance exists."""
    if not instances:
        console.print("[yellow]No instances available.[/yellow]")
        return None
        
    # If there's only one instance, select it automatically
    if len(instances) == 1:
        instance_id = instances[0]['id']
        console.print(f"[green]Automatically selected the only available instance:[/green] {instances[0]['name']} (ID: {instance_id})")
        return instance_id
    
    # If multiple instances, let user choose one
    console.print("\n[bold]Select an instance by ID:[/bold]")
    
    try:
        instance_id_input = Prompt.ask("[bold]Enter Instance ID[/bold]")
        instance_id = int(instance_id_input)
        
        # Verify the instance ID exists
        if any(instance['id'] == instance_id for instance in instances):
            return instance_id
        else:
            console.print("[red]Invalid instance ID. Please try again.[/red]")
            return select_instance(instances)  # Recursively try again
    except ValueError:
        console.print("[red]Please enter a valid numeric ID.[/red]")
        return select_instance(instances)  # Recursively try again

def display_data_versions(data_versions: List[Dict[str, Any]], table_display: TableDisplay):
    """Display data versions in a table."""
    if not data_versions:
        console.print("[yellow]No data versions found for this project.[/yellow]")
        return

    # Assuming data versions are in a 'results' field, adjust if needed
    response_data = {'results': data_versions}
    
    # Define columns for data versions - adjust these based on your actual data structure
    columns = [
        {"key": "id", "header": "ID"},
        {"key": "version", "header": "Version"},
        {"key": "created_at", "header": "Created At"},
        {"key": "status", "header": "Status"},
        {"key": "description", "header": "Description"}
    ]
    
    table_display.display_table(
        response_data=response_data,
        columns=columns,
        title_prefix="Data Versions",
        row_formatter=lambda row: row  # Default formatter, adjust if needed
    )

def select_feature_columns(columns_data: Dict[str, Any], target_column: str, table_display: TableDisplay) -> List[str]:
    """
    Interactive feature column selection.
    
    Allows users to select multiple feature columns with continuous feedback.
    Shows max 5 selected columns at a time to avoid cluttering the UI.
    """
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns available to select.[/yellow]")
        return []
    
    # Get all column names except the target column
    all_columns = [c for c in columns_data.get('columns', []) if c != target_column]
    
    if not all_columns:
        console.print("[yellow]No columns available for features after removing target column.[/yellow]")
        return []
    
    # Initialize selected features
    selected_features = []
    
    # Function to display current selection (max 5 visible)
    def display_current_selection():
        if not selected_features:
            console.print("\n[yellow]No feature columns selected yet.[/yellow]")
            return
            
        console.print(f"\n[bold green]Currently selected feature columns: [/bold green][cyan]{len(selected_features)} total[/cyan]")
        feature_table = Table(show_header=True, header_style="bold magenta")
        feature_table.add_column("#", style="dim")
        feature_table.add_column("Column Name", style="green")
        
        # Show only first 5 columns
        display_count = min(5, len(selected_features))
        for idx in range(display_count):
            feature_table.add_row(str(idx + 1), selected_features[idx])
            
        if len(selected_features) > 5:
            feature_table.add_row("...", f"[dim]+ {len(selected_features) - 5} more columns[/dim]")
            
        console.print(feature_table)
        
        # Option to show all columns if more than 5 are selected
        if len(selected_features) > 5 and Confirm.ask("Show all selected columns?", default=False):
            all_feature_table = Table(show_header=True, header_style="bold magenta")
            all_feature_table.add_column("#", style="dim")
            all_feature_table.add_column("Column Name", style="green")
            
            for idx, col in enumerate(selected_features, 1):
                all_feature_table.add_row(str(idx), col)
                
            console.print(all_feature_table)
    
    # Function to display available columns (not yet selected)
    def display_available_columns():
        available_columns = [c for c in all_columns if c not in selected_features]
        
        if not available_columns:
            console.print("\n[yellow]All columns have been selected as features.[/yellow]")
            return available_columns
            
        console.print(f"\n[bold blue]Available columns for selection: [/bold blue][cyan]{len(available_columns)} remaining[/cyan]")
        available_table = Table(show_header=True, header_style="bold cyan")
        available_table.add_column("ID", justify="right", style="dim")
        available_table.add_column("Column Name", style="cyan")
        
        # Show only first 5 available columns to avoid cluttering
        display_count = min(5, len(available_columns))
        for idx in range(display_count):
            available_table.add_row(str(idx + 1), available_columns[idx])
            
        if len(available_columns) > 5:
            available_table.add_row("...", f"[dim]+ {len(available_columns) - 5} more columns[/dim]")
            
        console.print(available_table)
        
        # Option to show all available columns if more than 5
        if len(available_columns) > 5 and Confirm.ask("Show all available columns?", default=False):
            all_available_table = Table(show_header=True, header_style="bold cyan")
            all_available_table.add_column("ID", justify="right", style="dim")
            all_available_table.add_column("Column Name", style="cyan")
            
            for idx, col in enumerate(available_columns, 1):
                all_available_table.add_row(str(idx), col)
                
            console.print(all_available_table)
            
        return available_columns
    
    # Start the interactive selection process
    console.print(f"\n[bold]Feature Column Selection[/bold] (Target: [green]{target_column}[/green])")
    console.print("[dim]You can select multiple columns as features for your model.[/dim]")
    
    while True:
        # Display current selection
        display_current_selection()
        
        # Display available columns and get the list
        available_columns = display_available_columns()
        
        if not available_columns:
            console.print("[yellow]All columns have been selected. You can now finalize your selection.[/yellow]")
            if Confirm.ask("Finalize your feature selection?"):
                break
            else:
                # Allow removing columns if user doesn't want to finalize yet
                if selected_features and Confirm.ask("Would you like to remove some columns?"):
                    remove_columns(selected_features)
                continue
        
        # Show options
        console.print("\n[bold]Options:[/bold]")
        console.print("  1. [cyan]Add another feature column[/cyan]")
        if selected_features:
            console.print("  2. [yellow]Remove feature column(s)[/yellow]")
        console.print(f"  {'3' if selected_features else '2'}. [green]Finish selection ({len(selected_features)} columns selected)[/green]")
        
        choice = Prompt.ask(
            "Choose an option", 
            choices=["1", "2", "3"] if selected_features else ["1", "2"],
            default="1"
        )
        
        if choice == "1":
            # Add a column
            add_column(available_columns, selected_features)
        elif choice == "2" and selected_features:
            # Remove a column
            remove_columns(selected_features)
        else:
            # Finish selection
            if Confirm.ask(f"Finalize selection with {len(selected_features)} feature columns?"):
                break
    
    return selected_features

def add_column(available_columns: List[str], selected_features: List[str]):
    """Add a column to the selected features."""
    # Create completer for available columns
    column_completer = FuzzyWordCompleter(available_columns)
    
    console.print("\n[bold]Select a feature column:[/bold]")
    console.print("[dim]You can type part of the column name and press Tab for suggestions[/dim]")
    
    # Get user input with autocompletion
    selected_column = prompt(
        "Column name: ",
        completer=column_completer,
        complete_while_typing=True
    )
    
    # Verify the column exists in available columns
    if selected_column in available_columns:
        selected_features.append(selected_column)
        console.print(f"[green]Added column:[/green] {selected_column}")
    else:
        console.print("[red]Column not found in available columns. Please try again.[/red]")

def remove_columns(selected_features: List[str]):
    """Remove columns from the selected features."""
    if not selected_features:
        console.print("[yellow]No columns to remove.[/yellow]")
        return
    
    # Show the columns with numbers
    console.print("\n[bold]Currently selected columns:[/bold]")
    for idx, col in enumerate(selected_features, 1):
        console.print(f"  {idx}. {col}")
    
    # Ask which column(s) to remove
    console.print("\n[bold]Enter column numbers to remove (comma-separated) or 'all' to clear:[/bold]")
    
    remove_input = Prompt.ask("Columns to remove")
    
    if remove_input.lower() == 'all':
        if Confirm.ask("Are you sure you want to remove all selected feature columns?"):
            selected_features.clear()
            console.print("[yellow]All feature columns have been removed.[/yellow]")
        return
    
    try:
        # Parse comma-separated numbers
        to_remove = [int(x.strip()) for x in remove_input.split(',') if x.strip()]
        # Sort in reverse order to avoid index shifting during removal
        to_remove.sort(reverse=True)
        
        removed = []
        for idx in to_remove:
            if 1 <= idx <= len(selected_features):
                removed.append(selected_features.pop(idx-1))
            else:
                console.print(f"[yellow]Warning: Index {idx} is out of range and was ignored.[/yellow]")
        
        if removed:
            console.print(f"[green]Removed {len(removed)} column(s):[/green] {', '.join(removed)}")
        else:
            console.print("[yellow]No columns were removed.[/yellow]")
            
    except ValueError:
        console.print("[red]Please enter valid numbers separated by commas.[/red]")

def select_model_type(model_types: List[Dict[str, Any]], table_display: TableDisplay) -> Tuple[int, Dict[str, Any]]:
    """Allow user to select a model type from available options."""
    if not model_types:
        console.print("[yellow]No model types available for this project type.[/yellow]")
        return None, None
    
    # Display available model types
    console.print("\n[bold]Available Model Types:[/bold]")
    model_table = Table(show_header=True)
    model_table.add_column("ID", style="cyan", justify="right")
    model_table.add_column("Name", style="green")
    model_table.add_column("Description", style="dim")
    
    for model_type in model_types:
        model_table.add_row(
            str(model_type.get('id', 'N/A')),
            model_type.get('model_name', 'N/A'),
            model_type.get('description', '')
        )
    
    console.print(model_table)
    
    # If there's only one model type, select it automatically
    if len(model_types) == 1:
        model_type_id = model_types[0]['id']
        console.print(f"[green]Automatically selected the only available model type:[/green] {model_types[0]['model_name']} (ID: {model_type_id})")
        return model_type_id, model_types[0]
    
    # Let user choose a model type
    try:
        model_id_input = Prompt.ask("[bold]Enter Model Type ID[/bold]")
        model_type_id = int(model_id_input)
        
        # Verify the model type ID exists
        selected_model = next((m for m in model_types if m['id'] == model_type_id), None)
        if selected_model:
            console.print(f"[green]Selected model type:[/green] {selected_model['model_name']}")
            return model_type_id, selected_model
        else:
            console.print("[red]Invalid model type ID. Please try again.[/red]")
            return select_model_type(model_types, table_display)
    except ValueError:
        console.print("[red]Please enter a valid numeric ID.[/red]")
        return select_model_type(model_types, table_display)
    
def display_columns_enhanced(columns_data: Dict[str, Any], selected: List[str] = None) -> None:
    """Enhanced column display with better formatting and selection status."""
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns found for this data version.[/yellow]")
        return
    
    selected = selected or []
    column_names = columns_data.get('columns', [])
    
    # Create table with selection status
    table = Table(title=f"Available Columns (Table: {columns_data.get('table_name', 'N/A')})")
    table.add_column("Select", justify="center", style="cyan", width=6)
    table.add_column("ID", justify="right", style="dim", width=4)
    table.add_column("Column Name", style="green")
    table.add_column("Status", justify="center", width=10)
    
    for idx, column_name in enumerate(column_names, 1):
        status_icon = "✓" if column_name in selected else "○"
        status_color = "green" if column_name in selected else "dim"
        status_text = "Selected" if column_name in selected else "Available"
        
        table.add_row(
            f"[{status_color}]{status_icon}[/{status_color}]",
            str(idx),
            column_name,
            f"[{status_color}]{status_text}[/{status_color}]"
        )
    
    console.print(table)
    
    if selected:
        console.print(f"\n[bold green]Selected: {len(selected)} columns[/bold green]")


def select_target_column_enhanced(columns_data: Dict[str, Any]) -> str:
    """Enhanced target column selection with smart suggestions."""
    if not columns_data or not columns_data.get('columns'):
        console.print("[yellow]No columns available to select.[/yellow]")
        return None
    
    column_names = columns_data.get('columns', [])
    
    # Display columns with helpful context
    console.print("\n[bold blue]Target Column Selection[/bold blue]")
    console.print("[dim]Select the column your model should predict[/dim]")
    
    display_columns_enhanced(columns_data)
    
    # Create completer
    column_completer = FuzzyWordCompleter(column_names)
    
    console.print("\n[bold]Selection options:[/bold]")
    console.print("• Type column name (autocomplete available)")
    console.print("• Enter column number (e.g., '5')")
    
    while True:
        try:
            selection = prompt(
                "Target column: ",
                completer=column_completer,
                complete_while_typing=True
            ).strip()
            
            # Handle numeric selection
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(column_names):
                    selected = column_names[idx]
                    console.print(f"[green]Selected:[/green] {selected}")
                    return selected  # ✅ Fixed: was 'selected', now correct
                else:
                    console.print(f"[red]Invalid number. Please enter 1-{len(column_names)}[/red]")
                    continue
            
            # Handle name selection
            if selection in column_names:
                console.print(f"[green]Selected:[/green] {selection}")
                return selection  # ✅ Fixed: was 'selected', should be 'selection'
            else:
                console.print("[red]Column not found. Try again or use Tab for suggestions.[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def select_feature_columns_enhanced(columns_data: Dict[str, Any], target_column: str) -> List[str]:
    """Enhanced feature column selection with bulk operations."""
    if not columns_data or not columns_data.get('columns'):
        return []
    
    available_columns = [c for c in columns_data.get('columns', []) if c != target_column]
    if not available_columns:
        console.print("[yellow]No columns available for features.[/yellow]")
        return []
    
    selected_features = []
    
    console.print(f"\n[bold blue]Feature Column Selection[/bold blue] (Target: [green]{target_column}[/green])")
    console.print("[dim]Select columns to use for prediction[/dim]")
    
    while True:
        # Show current state
        display_columns_enhanced(
            {'columns': available_columns, 'table_name': 'Features'}, 
            selected_features
        )
        
        console.print("\n[bold]Selection options:[/bold]")
        console.print("• [cyan]Single:[/cyan] column_name or number (e.g., '5' or 'age')")
        console.print("• [cyan]Range:[/cyan] 1-5 (selects columns 1 through 5)")
        console.print("• [cyan]Multiple:[/cyan] 1,3,5 or col1,col2,col3")
        console.print("• [cyan]All:[/cyan] 'all' (select all remaining)")
        console.print("• [cyan]Remove:[/cyan] -5 or -col_name (remove selection)")
        console.print("• [cyan]Done:[/cyan] 'done' or Enter to finish")
        
        if selected_features:
            console.print(f"• [cyan]Clear:[/cyan] 'clear' (remove all {len(selected_features)} selections)")
        
        try:
            selection = prompt(
                f"Selection ({len(selected_features)} selected): ",
                completer=FuzzyWordCompleter(available_columns + ['all', 'done', 'clear']),
                complete_while_typing=True
            ).strip()
            
            if not selection or selection.lower() == 'done':
                break
            elif selection.lower() == 'all':
                selected_features = available_columns.copy()
                console.print(f"[green]Selected all {len(selected_features)} columns[/green]")
            elif selection.lower() == 'clear':
                selected_features.clear()
                console.print("[yellow]Cleared all selections[/yellow]")
            else:
                process_selection(selection, available_columns, selected_features)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    return selected_features

def process_selection(selection: str, available_columns: List[str], selected_features: List[str]):
    """Process various selection formats."""
    # Handle removal
    if selection.startswith('-'):
        target = selection[1:]
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(available_columns):
                col_name = available_columns[idx]
                if col_name in selected_features:
                    selected_features.remove(col_name)
                    console.print(f"[yellow]Removed:[/yellow] {col_name}")
                else:
                    console.print(f"[red]{col_name} was not selected[/red]")
        elif target in selected_features:
            selected_features.remove(target)
            console.print(f"[yellow]Removed:[/yellow] {target}")
        return
    
    # Handle range selection (e.g., 1-5)
    if '-' in selection and not selection.startswith('-'):
        try:
            start, end = map(int, selection.split('-'))
            for i in range(start, end + 1):
                if 1 <= i <= len(available_columns):
                    col_name = available_columns[i - 1]
                    if col_name not in selected_features:
                        selected_features.append(col_name)
            console.print(f"[green]Added range {start}-{end}[/green]")
            return
        except ValueError:
            pass
    
    # Handle comma-separated selections
    if ',' in selection:
        items = [item.strip() for item in selection.split(',')]
        added = []
        for item in items:
            if item.isdigit():
                idx = int(item) - 1
                if 0 <= idx < len(available_columns):
                    col_name = available_columns[idx]
                    if col_name not in selected_features:
                        selected_features.append(col_name)
                        added.append(col_name)
            elif item in available_columns and item not in selected_features:
                selected_features.append(item)
                added.append(item)
        
        if added:
            console.print(f"[green]Added:[/green] {', '.join(added)}")
        return
    
    # Handle single selection
    if selection.isdigit():
        idx = int(selection) - 1
        if 0 <= idx < len(available_columns):
            col_name = available_columns[idx]
            if col_name not in selected_features:
                selected_features.append(col_name)
                console.print(f"[green]Added:[/green] {col_name}")
            else:
                console.print(f"[yellow]{col_name} already selected[/yellow]")
    elif selection in available_columns:
        if selection not in selected_features:
            selected_features.append(selection)
            console.print(f"[green]Added:[/green] {selection}")
        else:
            console.print(f"[yellow]{selection} already selected[/yellow]")
    else:
        console.print("[red]Invalid selection. Try again or use Tab for suggestions.[/red]")

def collect_hyperparameters(hyperparameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collect hyperparameter values from the user."""
    if not hyperparameters:
        console.print("[yellow]No hyperparameters available for this model type.[/yellow]")
        return {}
    
    # Display hyperparameters overview
    console.print("\n[bold]Model Hyperparameters:[/bold]")
    hyper_table = Table(show_header=True)
    hyper_table.add_column("Name", style="green")
    hyper_table.add_column("Description", style="dim")
    hyper_table.add_column("Type", style="cyan")
    hyper_table.add_column("Default", style="yellow")
    
    for hp in hyperparameters:
        hp_def = hp.get('hyperparameter_def', {})
        hyper_table.add_row(
            hp_def.get('name', 'N/A'),
            hp_def.get('description', ''),
            hp_def.get('type', 'N/A'),
            hp_def.get('default_value', 'N/A')
        )
    
    console.print(hyper_table)
    
    # Collect values for each hyperparameter
    collected_values = {}
    
    for hp in hyperparameters:
        hp_def = hp.get('hyperparameter_def', {})
        hp_name = hp_def.get('name', '')
        hp_desc = hp_def.get('description', '')
        hp_type = hp_def.get('type', '')
        hp_default = hp_def.get('default_value', '')
        
        console.print(f"\n[bold]{hp_name}[/bold]: {hp_desc}")
        console.print(f"[dim]Type: {hp_type}, Default: {hp_default}[/dim]")
        
        # Use different prompt based on type
        while True:
            if hp_type == 'bool':
                use_default = Confirm.ask(f"Use default value ({hp_default})?", default=True)
                if use_default:
                    value = hp_default
                else:
                    value = Prompt.ask(f"Enter value for {hp_name} (true/false)", choices=["true", "false"])
                    value = value.lower() == "true"
                break
            else:
                value = Prompt.ask(
                    f"Enter value for {hp_name}", 
                    default=hp_default,
                    show_default=True
                )
                
                # Validate input based on type
                if hp_type == 'int':
                    try:
                        int(value)
                        break
                    except ValueError:
                        console.print("[red]Please enter a valid integer.[/red]")
                elif hp_type == 'float':
                    try:
                        float(value)
                        break
                    except ValueError:
                        console.print("[red]Please enter a valid number.[/red]")
                else:
                    # For string or other types, accept as is
                    break
        
        collected_values[hp_name] = value
        console.print(f"[green]Set {hp_name} = {value}[/green]")
    
    # Show summary of selected hyperparameters
    console.print("\n[bold]Hyperparameter Summary:[/bold]")
    for name, value in collected_values.items():
        console.print(f"  [cyan]{name}[/cyan]: [yellow]{value}[/yellow]")
    
    return collected_values


@click.group()
def experiments():
    """Experiments management commands."""
    pass

from agentcore.cli.experiments import run, view, promote