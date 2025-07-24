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
import json
from collections import defaultdict
import os

from agentcore.managers.data_manager import DataManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager

install()

console = Console()

@click.group()
def data():
    """data management commands."""
    pass

@data.command(name='upload')
@BaseManager.handle_api_error
def data_upload():
    """Upload data to cloud."""
    
    console.print("\n[bold blue]🔹 Select Data Type 🔹[/bold blue]\n")

    data_type = Prompt.ask(
        "[bold]Choose an option:[/bold]\n1. File\n2. Datasource",
        choices=["1", "2"],
        default="1"
    )

    selected_type = "File" if data_type == "1" else "Datasource"

    console.print(f"\n[bold green]✅ You selected: {selected_type}[/bold green]\n")

    if selected_type == "File":
        data_upload_files()
    else:
        data_upload_datasource()


@BaseManager.handle_api_error
def data_upload_files():
    """Upload through files to cloud."""
    
    name = Prompt.ask("[bold]Enter name[/bold]")
    file_path = Prompt.ask("[bold]Provide the file path[/bold]")

    # Validate file path before attempting to open
    if not os.path.exists(file_path):
        console.print(f"[bold red]Error: File not found at '{file_path}'[/bold red]")
        return

    try:
        data_manager = DataManager()
        response = data_manager.upload_data_files(name, file_path)
        
        console.print(f"[bold green]✅ File uploaded successfully![/bold green]")
        console.print(response)
    except Exception as e:
        console.print(f"[bold red]Error during file upload: {str(e)}[/bold red]")


@BaseManager.handle_api_error
def data_upload_datasource():
    """Upload datasource to cloud."""
    
    name = Prompt.ask("[bold]Enter name[/bold]")
    db_type = Prompt.ask("[bold]Enter database type[/bold]")
    host = Prompt.ask("[bold]Enter host[/bold]")
    database = Prompt.ask("[bold]Enter database name[/bold]")
    table_name = Prompt.ask("[bold]Enter table name[/bold]")
    port = Prompt.ask("[bold]Enter port[/bold]")
    username = Prompt.ask("[bold]Enter username[/bold]")
    password = Prompt.ask("[bold]Enter password[/bold]", password=True)

    payload = {
        "name": name,
        "db_type": db_type,
        "host": host,
        "database": database,
        "table_name": table_name,
        "port": port,
        "username": username,
        "password": password,
    }

    try:
        data_manager = DataManager()
        response = data_manager.upload_data_source(payload)
        azure_url = response.get("azure_url")
        
        console.print("\n[bold green]✅ Datasource uploaded in cloud successfully![/bold green]")
        if azure_url:
            console.print(f"[bold cyan]🔗 Download Link:[/bold cyan] {azure_url}")
        console.print("[bold yellow]Response Details:[/bold yellow]", response)
    except Exception as e:
        console.print(f"[bold red]Error during datasource upload: {str(e)}[/bold red]")


# c:\Work-projects\proj-excel\new_dummy_output_1.xlsx
# c:\Work-projects\proj-excel\updated_file.xlsx
    


if __name__ == "__main__":
    data()