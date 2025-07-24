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

import logging
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

import click
import json
import logging
from rich.console import Console

from agentcore.cli.projects import projects
from agentcore.cli.config import config
from agentcore.cli.users import users
from agentcore.cli.experiments.main import experiments
from agentcore.cli.instances.cli import instances
from agentcore.cli.credentials import credentials
from agentcore.cli.data_version import data_version
from agentcore.cli.datasource import datasource
from agentcore.cli.datapipeline import datapipeline
from agentcore.cli.observability import observability
from agentcore.cli.login import logout,change_password,reset_password, login_user, signup_user
from agentcore.cli.deploy import deploy
from agentcore.cli.data.main import data

console = Console()

@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """AgentCORE CLI - Manage your ML projects with ease."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level)

@cli.command("list")
@click.pass_context
def list_all_commands(ctx):
    """List all commands, including subcommands, with descriptions."""
    console.print("[bold cyan]Listing all available commands in AgentCORE:[/bold cyan]\n")
    
    def list_commands(command, level=0):
        indent = "  " * level  # Indentation for subcommands
        if isinstance(command, click.Group):
            for subcommand_name, subcommand in command.commands.items():
                # Group header for top-level commands
                if level == 0:
                    console.print("\n[bold magenta]" + "=" * 40 + "[/bold magenta]")
                    console.print(f"[bold yellow]{subcommand_name.capitalize()} Commands:[/bold yellow]")
                    console.print("[bold magenta]" + "=" * 40 + "[/bold magenta]")
                
                # Display the command name and its help text
                console.print(f"{indent}- [green]{subcommand_name}[/green]: {subcommand.help}")
                
                # Recursively list subcommands
                list_commands(subcommand, level + 1)

    list_commands(cli)
    console.print("\n[bold cyan]Finished listing all available commands in AgentCORE[/bold cyan]")

cli.add_command(projects) #create, set-details, view, stop rest
cli.add_command(config)
cli.add_command(users) #stop all 
cli.add_command(experiments) 
cli.add_command(instances) #only create, view, action
cli.add_command(credentials)
cli.add_command(data)
# cli.add_command(git)
# cli.add_command(data_version)
# cli.add_command(datasource)
cli.add_command(observability)
# cli.add_command(datapipeline)
cli.add_command(logout)
cli.add_command(login_user)
cli.add_command(change_password)
cli.add_command(reset_password)
cli.add_command(deploy)
cli.add_command(signup_user)

if __name__ == "__main__":
    cli()