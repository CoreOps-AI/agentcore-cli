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
import datetime
from agentcore.managers.base import BaseManager
from agentcore.managers.datasource_manager import DatasourceManager
from agentcore.managers.table_manager import TableDisplay
from rich.console import Console
from rich.prompt import Prompt
from datetime import datetime

console = Console()

def get_datasource_search_list():
    """Get Datasource list with tab completion using id-type(description) format and return full Datasource dict."""
 
    datasource_manager = DatasourceManager()
    base_manager = BaseManager()
    response = datasource_manager.view_datasources()
 
    if not response:
        console.print("[red]No Datasources found.[/red]")
        return None
    
    # Create mapping: formatted string => original datasource dict
    formatted_map = {
        f"{datasource['id']}-{datasource['source_type']}({datasource['description']})": datasource
        for datasource in response if "source_type" in datasource and "id" in datasource and "description" in datasource
    }
    formatted_datasources = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter ID-Type(description)(press Tab for suggestions and Press Enter for Datasource Selection):[/bold]")
        selected_datasource = base_manager.get_input_with_tab_completion("Datasources", formatted_datasources)
        if selected_datasource in formatted_map:
            datasource = formatted_map[selected_datasource]
 
            # Format date-time fields
            datasource["created_at"] = beautify_datetime(datasource.get("created_at", ""), date_only=True)
            datasource["updated_at"] = beautify_datetime(datasource.get("updated_at", ""), date_only=True)
 
            console.print(f"\n[green]✅ Selected Datasource: {datasource['id']}-{datasource['source_type']}({datasource['description']})[/green]")
            console.print("[bold]Selected Datasource Details:[/bold]")
            table_display = TableDisplay(console)

            # Prepare data for table
            table_data = [
                {
                    "ID": datasource["id"],
                    "Source Type": datasource["source_type"],
                    "Description": datasource["description"],
                    "Created By": datasource.get("created_by", "-"),
                    "Created At": datasource.get("created_at", "-"),
                    "Data Source Type": datasource.get("data_source_type", "-"),
                    "Project": ", ".join([proj["name"] for proj in datasource.get("projects", [])]) or "-"
                }
            ]
            
            # Define columns for display
            columns = ["ID", "Source Type", "Description", "Created By", "Created At", "Data Source Type", "Project"]
            
            # Display the table
            table_display.display_table(
                response_data={"results": table_data},
                columns=columns,
                title_prefix="Selected Datasource"
            )
 
            return datasource
        else:
            console.print(f"\n[yellow]⚠️ '{selected_datasource}' is not a valid datasource entry.[/yellow]")
            suggestions = [p for p in formatted_datasources if selected_datasource.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")


@click.group()
def data():
    """Experiments management commands."""
    pass

@BaseManager.handle_api_error
def beautify_datetime(dt_str, date_only=False):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Convert Zulu to UTC offset
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d") if date_only else dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

from agentcore.cli.data import operations, source, transform, fetch