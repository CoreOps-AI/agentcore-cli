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

from agentcore.cli.experiments.main import *
from agentcore.cli.experiments.helpers import *

from agentcore.managers.base import BaseManager
from agentcore.managers.users_manager import UserManager
from agentcore.managers.credentials_manager import CredentialManager

from rich.syntax import Syntax
import json

console = Console()
    


@experiments.command(name='promote')
@BaseManager.handle_api_error
def promote_experiment():
    """Promote an experiment to production."""
    console = Console()
    experiment_manager = ExperimentManager()
    experiments_manager = ExperimentsManager()
    user_manager = UserManager()
    table_display = TableDisplay(console)
    credential_manager = CredentialManager()

    # Step 1: Select Project
    selected_project = get_project_list()
    project_id = selected_project.get('id')
    if not project_id:
        console.print("[red]❌ No project is selected. Aborting operation.[/red]")
        return

    # Step 2: Select Experiment
    selected_experiment = get_experiments_by_project_search_list(project_id=project_id)
    if not selected_experiment:
        return
    # console.print(selected_experiment)

    experiment_code = selected_experiment.get('experiment_group_code')
    version = selected_experiment.get('version')
    instance_id = selected_experiment.get('instance_id')
    if instance_id == 'N/A':
        instance_id = None
    # console.print(instance_id)

    if not all([experiment_code, version, instance_id]):
        console.print("[red]❌ Experiment is missing some of the required fields (code, version, instance IP). Aborting.[/red]\n")
        return

    # Step 3: Get current user
    current_user = user_manager.get_current_user()
    user_id = current_user.get('id')
    if not user_id:
        console.print("[red]❌ Could not fetch current user info. Aborting.[/red]\n")
        return

    console.print("[bold green]Select GitHUB Credentials:[/bold green]")
    # Step 4: Select GitHub credentials
    github_credentials = get_user_credentials_search_list(user_id=user_id)
    github_id = github_credentials.get('id')
    if not github_id:
        console.print("[red]❌ No GitHub credential selected. Aborting.[/red]\n")
        return

    # Step 5: Construct Payload
    payload = {
        "project_id": project_id,
        "experiment_group_code": experiment_code,
        "version_id": version,
        "github_id": github_id,
        "instance_id": instance_id,
    }

    console.print(f"\n[bold green]🚀 Pushing Experiment: {experiment_code} (Version: {version}) to GIT[/bold green]\n")

    # Step 6: Trigger Git Push
    response = experiment_manager.experiment_gitpush(payload=payload)
    if not response:
        console.print("[red]❌ Promotion failed. No response from server.[/red]\n")
        return
    console.print(response)
    # Step 7: Display Success Output
    if response.get("status") == "success":
        console.print("[bold green]✅ GitHub Push Successful[/bold green]")
        console.print(f"[bold]Message:[/bold] {response.get('message')}")
        console.print("\n[bold]Output:[/bold]")
        console.print(f"[blue]{response.get('output')}[/blue]")
    else:
        console.print("[red]❌ GitHub Push Failed and Promote is aborted.[/red]")
        console.print(f"[bold]Message:[/bold] {response.get('message') or 'No message provided.'}")
        if "output" in response:
            console.print(f"[bold]Output:[/bold] {response['output']}")
        return None

    response = experiment_manager.promote_experiment(project_id, experiment_code, version)

    console.print(f"\n[bold green]🚀 Promoting Experiment: {experiment_code} (Version: {version})[/bold green]\n")
    # Step 6: Handle the response
    if response.get('message') == "Run marked for promotion successfully.":
        data = response.get('data', {})
        console.print(f"[bold green]Experiment {data.get('experiment_group_code')} version {data.get('version')} "
                      f"successfully marked for promotion.[/bold green]")
        console.print(f"Details:\n"
                      f"- Project ID: {data.get('project_id')}\n"
                      f"- Experiment Name: {data.get('experiment_name')}\n"
                      f"- Executed By: {data.get('executed_by')}\n"
                      f"- Target Column: {data.get('target_column')}\n"
                      f"- Train/Test Split: {data.get('train_test_split')}\n"
                      f"- Started At: {data.get('started_at')}\n"
                      f"- Completed At: {data.get('completed_at')}\n"
                      f"- Created At: {data.get('created_at')}")
    else:
        console.print(f"\n[red]Failed to mark Experiment {experiment_code} version {version} for promotion.[/red]")
        console.print(f"[yellow]Warning: {response.get('message', 'Unknown error')}[/yellow]\n")

if __name__ == "__main__":
    experiments()