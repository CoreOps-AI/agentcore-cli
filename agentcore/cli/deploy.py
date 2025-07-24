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
from datetime import datetime
from rich.live import Live
import time
import json
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt
from rich.console import Group

from agentcore.managers.projects_manager import ProjectManager
from agentcore.managers.users_manager import UserManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.managers.deploy_manager import DeployManager
from agentcore.managers.base import BaseManager
from agentcore.managers.users_manager import UserManager
from agentcore.managers.credentials_manager import CredentialManager
from agentcore.managers.instance_manager import InstanceManager

from agentcore.cli.experiments.main import *
from agentcore.cli.experiments.helpers import *
from agentcore.cli.experiments.helpers import get_project_list
from agentcore.cli.datasource import get_datasource_search_list
from agentcore.cli.instances.utils import get_instance_list

install()

console = Console()

#Hepler
def beautify_datetime(dt_str, date_only=False):
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")  # Convert Zulu to UTC offset
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%Y-%m-%d") if date_only else dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

@BaseManager.handle_api_error
def get_deployments_list(response):
    """Get deployment list with tab completion using deployment format and return full deployment dict."""
    deploy_manager = DeployManager()
    base_manager = BaseManager()
    
    # Create mapping: formatted string => original project dict
    formatted_map = {
        f"{deployment['id']}": deployment
        for deployment in response if "id" in deployment
    }
    formatted_deployments = sorted(formatted_map.keys())
    while True:
        console.print("\n[bold]Enter Deployment ID(press Tab for suggestions and Press Enter for Selection):[/bold]")
        
        if len(formatted_deployments) == 1:
            selected_deployment = formatted_deployments[0]
            console.print(f"[green]Automatically selected the only available deployment:[/green] {selected_deployment}")
        else:
            selected_deployment = base_manager.get_input_with_tab_completion("Deployments", formatted_deployments)
        if selected_deployment in formatted_map:
            deployment = formatted_map[selected_deployment]

            if deployment.get('deploy_experiment_runid'):
                deployment['deploy_experiment_runid'] = deployment['deploy_experiment_runid'].get('id', '')
            else:
                deployment['deploy_experiment_runid'] = ''

            if deployment.get('experiment_runid'):
                deployment['experiment_runid'] = deployment['experiment_runid'].get('id', '')
            else:
                deployment['experiment_runid'] = ''

            deployment['user'] = deployment['user'].get('username', '')


            console.print("[green]Selected Deployment:[/green]")
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={'results': [deployment]},
                columns=deploy_manager.view_deployments_columns,
                title_prefix="Selected Deployment",
                row_formatter=table_display.format_project_row
            )

            return deployment
        else:
            console.print(f"\n[yellow]⚠️ '{selected_deployment}' is not a valid deployment entry.[/yellow]")
            suggestions = [p for p in formatted_deployments if selected_deployment.lower() in p.lower()]
            if suggestions:
                console.print("[blue]🔎 Did you mean one of these?[/blue]")
                for suggestion in suggestions[:5]:
                    console.print(f"  - {suggestion}")

###CLI
@click.group()
def deploy():
    """Deployment management commands."""
    pass

@deploy.command(name='create')
@BaseManager.handle_api_error
def create_deploy():
    """Create a new deployment for an experiment."""
    experiments = ExperimentManager()
    user_manager = UserManager()
    deploy_manager = DeployManager()

    # Step 1: Select Project
    selected_project = get_project_list()
    project_id = selected_project.get('id')
    if not project_id:
        console.print("[red]❌ No project is selected. Aborting operation.[/red]")
        return

    # Step 2: Fetch all experiments (detailed list)
    experiment_data = experiments.fetch_experiments(project_id=project_id)
    if not experiment_data:
        console.print("[red]❌ Could not fetch experiments. Aborting.[/red]")
        return

    experiment_results = experiment_data.get('results', [])
    if not experiment_results:
        console.print("[red]❌ No experiments found for this project. Aborting.[/red]")
        return

    # Step 3: Filter only promoted experiments for user to select
    promoted_experiments = [
        exp for exp in experiment_results if exp.get('status') == 'marked_for_promotion'
    ]
    if not promoted_experiments:
        console.print("[red]❌ No promoted experiments found. Aborting.[/red]")
        return

    # Step 4: Prepare options for autocomplete
    experiment_options = []
    experiment_lookup = {}
    for exp in promoted_experiments:
        code = exp.get('experiment_group_code')
        version = exp.get('version')
        model = exp.get('model_display_name')
        created = exp.get('created_at')
        label = f"{code}"
        experiment_options.append(label)
        experiment_lookup[label] = code  # Store group code for lookup

    # Step 5: Autocomplete selection
    selected_label = experiments.get_input_with_tab_completion(
        "Select experiment group code",
        experiment_options
    )
    if not selected_label or selected_label not in experiment_lookup:
        console.print("[red]❌ Invalid experiment selection. Aborting.[/red]")
        return

    selected_group_code = experiment_lookup[selected_label]

    # Step 6: Find full details for the chosen group code
    selected_experiment = next(
        (exp for exp in experiment_results if exp.get('experiment_group_code') == selected_group_code),
        None
    )
    if not selected_experiment:
        console.print("[red]❌ Could not find experiment details for selected group code. Aborting.[/red]")
        return

    # Proceed as before using selected_experiment (which has all needed fields)
    selected_datasource = get_datasource_search_list()
    datasource_id = selected_datasource.get('id')
    if not datasource_id:
        console.print("[red]❌ No Datasource selected. Aborting.[/red]\n")
        return

    experiment_code = selected_experiment.get('experiment_group_code')
    version = selected_experiment.get('version')
    instance_id = selected_experiment.get('instance_id')
    if instance_id == 'N/A':
        instance_id = None

    if not all([experiment_code, version, instance_id]):
        console.print("[red]❌ Experiment is missing some of the required fields (code, version, instance IP). Aborting.[/red]\n")
        return

    # Step 7: Get current user
    current_user = user_manager.get_current_user()
    user_id = current_user.get('id')
    if not user_id:
        console.print("[red]❌ Could not fetch current user info. Aborting.[/red]\n")
        return

    console.print("[bold green]Select GitHUB Credentials:[/bold green]")
    github_credentials = get_user_credentials_search_list(user_id=user_id)
    github_id = github_credentials.get('id')
    if not github_id:
        console.print("[red]❌ No GitHub credential selected. Aborting.[/red]\n")
        return

    payload = {
        "project_id": project_id,
        "experiment_group_code": experiment_code,
        "datasource_id": datasource_id,
        "version_id": version,
        "github_id": github_id,
        "instance_id": instance_id,
    }

    response = deploy_manager.create_deploy(payload=payload)
    if not response:
        console.print("[red]❌ Promotion failed. No response from server.[/red]\n")
        return

    message = response.get("message")
    job_id = response.get("job_id")

    console.print(f"[green]{message}[/green]\n")
    if job_id:
        console.print(f"[cyan]🚀 Job ID:[/cyan] {job_id}\n")

    if Prompt.ask("\n[bold]Do you want to track status?[/bold]", choices=["yes", "no"], default="yes") == "no":
        return None

    fetch_status(job_id)


@BaseManager.handle_api_error
# @deploy.command(name="test")
@BaseManager.handle_api_error
def fetch_status(job_id=None):
    """Fetch Status by Job ID."""
    deploy_manager = DeployManager()
    if not job_id:
        job_id = Prompt.ask("\n[bold]Enter Job ID[/bold]")
    
    if not job_id:
        console.print("[red]Error: Job ID is required. Aborting operation.[/red]")
        exit(1)
    
    console.print("\n[yellow]Monitoring job status... Press Ctrl+C to stop[/yellow]")
    
    try:
        seen_steps = set()
        
        with Live(refresh_per_second=2, console=console) as live:
            while True:
                response = deploy_manager.fetch_status(job_id)
                if not response or not isinstance(response, dict):
                    console.print("[red]❌ Failed to fetch job status or invalid response.[/red]")
                    return
                
                details = response.get("details", [])
                status = response.get("status", "UNKNOWN")
                
                # Initialize steps table
                steps_table = Table(title="Job Steps", title_style="bold green", border_style="blue")
                steps_table.add_column("Step", style="cyan", no_wrap=True)
                steps_table.add_column("Status", style="green")
                steps_table.add_column("Message", style="white")
                steps_table.add_column("Timestamp", style="magenta")
                
                # Add all steps to steps table
                for step in details:
                    step_id = (step.get("step"), step.get("timestamp"))
                    if step_id not in seen_steps:
                        seen_steps.add(step_id)
                    
                    steps_table.add_row(
                        step.get("step", "N/A"),
                        step.get("status", "N/A"),
                        step.get("message", "N/A"),
                        beautify_datetime(step.get("timestamp", ""), date_only=False)
                    )
                
                # Use Group to stack tables without gaps
                # display_group = Group(job_info_table, "", steps_table)
                live.update(steps_table)
                
                # Stop polling if job is in a final state
                if status.upper() in ["SUCCESS", "FAILED"]:
                    break
                
                time.sleep(3)
        
        console.print(f"\n[bold]{status}[/bold] - Monitoring complete.\n")

        # Show test summary results if available
        result = response.get("result", {})
        message = result.get("message", "")
        console.print(f"[bold green]Result Message:[/bold green] {message}\n")
        testing_summary = result.get("testing_summary", {})
        results = testing_summary.get("results", [])

        if results:
            results_table = Table(title="Test Results Summary", title_style="bold blue", border_style="blue")
            results_table.add_column("Metric", style="cyan")
            results_table.add_column("Value", style="green")
            # results_table.add_column("Status", style="magenta")
            # results_table.add_column("Details", style="white")
            # results_table.add_column("Artifact", style="magenta")

            for r in results:
                if r['metric'] == 'rolling_mae_w5':
                    # r['value'] = r['value'][:5]
                    continue
                if r['metric'] == 'rolling_mse_w5':
                    # r['value'] = r['value'][:5]
                    continue
                results_table.add_row(
                    str(r.get("metric", "N/A")),
                    str(r.get("value", "N/A")),
                    # str(r.get("status", "N/A")),
                    # r.get("details", "N/A"),
                    # r.get("artifact", "N/A")
                )

            console.print(results_table)
        else:
            console.print("[yellow]No test results available.[/yellow]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring interrupted by user.[/yellow]\n")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")

@deploy.command(name='view')
@BaseManager.handle_api_error
def view_deploy():
    """View all deployments."""
    deploy_manager = DeployManager()
    table_display = TableDisplay()
    base_manager = BaseManager()
    

    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    response = deploy_manager.view_deployments(project_id)
    
    if not response:
        console.print("[yellow]No deployments found under this project.[/yellow]\n")
        return
    
    response_copy = json.loads(json.dumps(response))
    for deploy in response_copy:
        if deploy.get('deploy_experiment_runid'):
            deploy['deploy_experiment_runid'] = deploy['deploy_experiment_runid'].get('id', '')
        else:
            deploy['deploy_experiment_runid'] = ''

        if deploy.get('experiment_runid'):
            deploy['experiment_runid'] = deploy['experiment_runid'].get('id', '')
        else:
            deploy['experiment_runid'] = ''

        deploy['user'] = deploy['user'].get('username', '')

    console.print("[green]Project Deployments:[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': response_copy},
        columns=deploy_manager.view_deployments_columns,
        title_prefix="Project Deployments",
        row_formatter=table_display.format_project_row
    )

    if Prompt.ask("\n[bold]Do you want to view particular deployment details?[/bold]", choices=["yes", "no"], default="yes") == "no":
        return None
    
    # deployment = None
    # while not deployment:
    #     id = Prompt.ask("[bold]Enter ID from above table[/bold]")
    #     for deployments in response_copy:
    #         if id == deployments['id']:
    #             deployment = deployments
    #             break
    #     if not deployment:
    #         console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")


    # console.print("\n[green]Selected Deployment:[/green]")
    # table_display = TableDisplay(console)
    # table_display.display_table(
    #     response_data={'results': [deployment]},
    #     columns=deploy_manager.view_deployments_columns,
    #     title_prefix="Selected Deployment",
    #     row_formatter=table_display.format_project_row
    # )

    deployment = get_deployments_list(response)
    
    deployment_details = deployment.get('details', '')
    if not deployment_details:
        console.print("[yellow]No details found under selected deployment.[/yellow]\n")
        return
    
    for detail in deployment_details:
        detail['timestamp'] = beautify_datetime(detail['timestamp'])
    
    console.print("\n[green]Deployment Details:[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': deployment_details},
        columns=deploy_manager.details_deployment_columns,
        title_prefix="Deployment Details",
        row_formatter=table_display.format_project_row
    )

@deploy.command(name='production')
@BaseManager.handle_api_error
def production_promote():
    """Deploy project to production"""
    deploy_manager = DeployManager()
    table_display = TableDisplay()
    base_manager = BaseManager()
    instance_manager = InstanceManager()

    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    project_instances = instance_manager.project_instance_show(project_id)
    if not project_instances:
        console.print(f"[red]No Instances are found with this Project ID-{project_id}[/red]")
        return
    
    if project_instances:
        filtered_columns = [col for col in instance_manager.project_instance_columns
                            if col not in ['CPU Count', 'Memory Size', 'Stopped At', 'AWS Region', 'OS Type']]
 
    console.print(f"\n[blue]Instances of Project:[green]{project_details['name']}[/green][/blue]")
    table_display = TableDisplay()
    table_display.display_table(
                response_data={'results': project_instances['instances']},
                columns=filtered_columns,
                title_prefix='Project Instance',
                row_formatter=table_display.format_instance_row
            )
    
    instance = get_instance_list(project_id)
    instance_id = instance['id']
    
    if not instance_id:
        console.print("[red]Error: Instance ID is required. Aborting operation.[/red]")
        exit(1) 

    response = deploy_manager.fetch_deployment_job_ids(project_id)
    
    if not response:
        console.print("[yellow]No deployments found under this project.[/yellow]\n")
        return
    
    response_copy = json.loads(json.dumps(response))
    for deploy in response_copy:
        if deploy.get('deploy_experiment_runid'):
            deploy['deploy_experiment_runid'] = deploy['deploy_experiment_runid'].get('id', '')
        else:
            deploy['deploy_experiment_runid'] = ''

        if deploy.get('experiment_runid'):
            deploy['experiment_runid'] = deploy['experiment_runid'].get('id', '')
        else:
            deploy['experiment_runid'] = ''

        deploy['user'] = deploy['user'].get('username', '')

    console.print("[green]Project Deployments:[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': response_copy},
        columns=deploy_manager.view_deployments_columns,
        title_prefix="Project Deployments",
        row_formatter=table_display.format_project_row
    )

    # deployment = None
    # while not deployment:
    #     deployment_id = Prompt.ask("[bold]Enter ID from above table[/bold]")
    #     for deployments in response_copy:
    #         if deployment_id == deployments['id']:
    #             deployment = deployments
    #             break
    #     if not deployment:
    #         console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")

    deployment = get_deployments_list(response)
    deployment_id = deployment['id']

    if deployment['is_test_passed'] == False:
        console.print("\n[yellow]Selected deployment is test failed. Test status can be changed using [blue]'agentcore deploy override'[/blue] command[/yellow]\n")
        return 

    payload = {
        "project_id":project_id,
        "instance_id": instance_id,
        "deployment_job_id": deployment_id
    }
    if Prompt.ask("\n[bold]Do you want to deploy to production?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Deployment to production cancelled.[/yellow]")
        return 
    
    response = deploy_manager.promote_production(payload=payload)
    if not response:
        console.print("[red]Deployment to production failed.[/red]\n")
        return None
        
    console.print("\n[bold green]✅ Promotion initiated successfully![/bold green]")
    console.print(f"[cyan]🆔 Promotion ID:[/cyan] {response.get('promotion_id', 'N/A')}")
    console.print(f"[cyan]ℹ️ Message:[/cyan] {response.get('detail', 'No detail provided.')}\n")
    
    if Prompt.ask("\n[bold]Do you want to track status?[/bold]", choices=["yes", "no"], default="yes") == "no":
        return 

    fetch_production_status(response['promotion_id'])
    
@BaseManager.handle_api_error
def fetch_production_status(task_id=None):
    """Fetch Status by Task ID"""

    deploy_manager = DeployManager()

    if not task_id:
        task_id = Prompt.ask("\n[bold]Enter Task ID[/bold]")

    if not task_id:
        console.print("[red]Error: Task ID is required. Aborting operation.[/red]")
        exit(1)

    console.print("\n[yellow]Monitoring job status... Press Ctrl+C to stop[/yellow]")

    # Initial setup
    live = None

    try:
        while True:
            response = deploy_manager.promote_production_staus(task_id)

            if not response:
                if live:
                    live.stop()
                console.print("[red]❌ Failed to get response[/red]")
                return None

            if isinstance(response, dict):
                # Beautify datetime if present
                if response.get("promoted_at"):
                    response["promoted_at"] = beautify_datetime(response["promoted_at"])

                # Extract values with safety
                task_id_val = response.get("id", "N/A")
                project_name = response.get("project", {}).get("name", "N/A")
                status = response.get("status", "N/A")
                promoted_by = response.get("promoted_by", {}).get("username", "N/A")
                promoted_at = response.get("promoted_at", "N/A")
                api_endpoint = response.get("api_endpoint", "N/A")
                result = response.get("result", {})

                # Build new table
                new_table = Table(title="\nTask Status Summary", title_style="bold green")
                new_table.add_column("Field", style="cyan", no_wrap=True)
                new_table.add_column("Value", style="white")

                new_table.add_row("Task ID", task_id_val)
                new_table.add_row("Project", project_name)
                new_table.add_row("Status", status)
                new_table.add_row("Promoted by", promoted_by)
                new_table.add_row("Promoted At", promoted_at)
                new_table.add_row("API Endpoint", str(api_endpoint))

                if result:
                    new_table.add_row("Result Status", result.get("status", "N/A"))
                    new_table.add_row("Message", result.get("message", "N/A"))
                    new_table.add_row("Instance ID", str(result.get("instance_id", "N/A")))

                # Start or update live display
                if live is None:
                    live = Live(new_table, console=console, refresh_per_second=1)
                    live.start()
                else:
                    live.update(new_table)

                # Stop if terminal status reached
                if status in ["FAILED", "SUCCESS"]:
                    live.stop()
                    console.print(f"\n[bold yellow]Task ended with status: {status}[/bold yellow]\n")
                    break

            else:
                if live:
                    live.stop()
                console.print("[red]❌ Unexpected response format[/red]")
                console.print(response)
                break

            import time
            time.sleep(5)

    except KeyboardInterrupt:
        if live:
            live.stop()
        console.print("\n[yellow]Monitoring stopped by user[/yellow]\n")

    except Exception as e:
        if live:
            live.stop()
        console.print(f"[red]❌ Error occurred: {e}[/red]")


@deploy.command(name='compare')
@BaseManager.handle_api_error
def compare_metrics():
    """Compare metrics of deployments"""
    deploy_manager = DeployManager()
    table_display = TableDisplay()
    base_manager = BaseManager()
    instance_manager = InstanceManager()

    project_details = get_project_list()
    if not project_details:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None
    
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    response = deploy_manager.fetch_deployment_job_ids(project_id)
    
    if not response:
        console.print("[yellow]No deployments found under this project.[/yellow]\n")
        return
    
    response_copy = json.loads(json.dumps(response))

    for deploy in response_copy:
        # Flatten nested fields
        deploy['deploy_experiment_runid'] = deploy.get('deploy_experiment_runid', {}).get('id', '')

        deploy['experiment_runid'] = deploy.get('experiment_runid', {}).get('id', '')
        deploy['user'] = deploy.get('user', {}).get('username', '')

    # Display table
    console.print("\n[green]Project Deployments:[/green]")
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': response_copy},
        columns=deploy_manager.view_deployments_columns,
        title_prefix="Project Deployments",
        row_formatter=table_display.format_project_row
    )

    # # Prompt for valid deploy_experiment_runid
    # deployment = None
    # while not deployment:
    #     deploy_experiment_runid = int(Prompt.ask("[bold]Enter Deploy Experiment RunID from above table[/bold]").strip())
    #     for deploy in response_copy:
    #         if deploy['deploy_experiment_runid'] == deploy_experiment_runid:
    #             deployment = deploy
    #             break
    #     if not deployment:
    #         console.print("[red]❌ Invalid Deploy Experiment RunID. Please choose a valid one from the table.[/red]")

    deployment = get_deployments_list(response)
    deploy_experiment_runid = deployment['deploy_experiment_runid']
    response = deploy_manager.metrics_compare(deploy_experiment_runid)

    if not response:
        console.print("[red]❌ No metrics found.[/red]")
        return 

    results = response.get('results', [])
    passed = response.get('passed', False)

    # Show summary before table
    console.print(f"\n[bold]✅ Metrics Passed:[/bold] {'[green]Yes[/green]' if passed else '[red]No[/red]'}")
    console.print(f"[bold]📊 Total Checks:[/bold] {len(results)}")

    # Classify metrics
    valid_metrics = []
    missing_values = []
    missing_thresholds = []

    for metric in results:
        has_value = 'value' in metric and metric['value'] is not None
        has_threshold = 'threshold' in metric and metric['threshold'] is not None

        if has_value and has_threshold:
            valid_metrics.append(metric)
        else:
            if not has_value:
                missing_values.append(metric.get('metric', 'Unknown'))
            if not has_threshold:
                missing_thresholds.append(metric.get('metric', 'Unknown'))

    # Show valid metrics in table
    if valid_metrics:
        console.print("\n[green]Metric Comparison Results:[/green]")
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': valid_metrics},
            columns=deploy_manager.details_compare_metric_columns,
            title_prefix="Metric Comparison",
            row_formatter=table_display.format_project_row
        )
    else:
        console.print("[yellow]⚠️ No metrics with both value and threshold available for display.[/yellow]")

    # Show missing value info
    if missing_values:
        formatted_missing_values = ", ".join([f"[bold]{metric}[/bold]" for metric in missing_values])
        count = len(missing_values)
        console.print(f"\n[yellow]⚠️ No value fetched from experiment for the following {count} metric(s):[/yellow]")
        console.print(f"• {formatted_missing_values}")

    if missing_thresholds:
        formatted_missing_thresholds = ", ".join([f"[bold]{metric}[/bold]" for metric in missing_thresholds])
        count = len(missing_thresholds)
        console.print(f"\n[yellow]⚠️ Threshold is not set for the following {count} metrics:[/yellow]")
        console.print(f"• {formatted_missing_thresholds}")

@deploy.command(name='override')
@BaseManager.handle_api_error(show_details=True)
def status_override():
    """Override the status of a deployment"""

    deploy_manager = DeployManager()
    table_display = TableDisplay()
    base_manager = BaseManager()
    

    project_details = get_project_list()
    project_id = project_details['id']

    if not project_id:
        console.print("[red]Error: Project ID is required. Aborting operation.[/red]")
        return None

    response = deploy_manager.view_deployments(project_id)
    
    if not response:
        console.print("[yellow]No deployments found under this project.[/yellow]\n")
        return

    deployment_jobs = []
    response_copy = json.loads(json.dumps(response))

    for deploy in response_copy:
        # if deploy.get('is_test_passed', True):  # Skip if test passed
        #     continue

        # Safely extract nested fields
        deploy_experiment = deploy.get('deploy_experiment_runid') or {}
        experiment = deploy.get('experiment_runid') or {}
        user = deploy.get('user') or {}

        deploy['deploy_experiment_runid'] = str(deploy_experiment.get('id', ''))
        deploy['experiment_runid'] = str(experiment.get('id', ''))
        deploy['user'] = user.get('username', '')


        deployment_jobs.append(deploy)

    if not deployment_jobs:
        console.print("[yellow]No deployments found under this project.[/yellow]\n")
        return

    console.print("[green]Project Deployments:[/green]")

    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={'results': deployment_jobs},
        columns=deploy_manager.view_deployments_columns,
        title_prefix="Project Deployments",
        row_formatter=table_display.format_project_row
    )

    # deployment = None
    # while not deployment:
    #     deployment_id = Prompt.ask("[bold]Enter ID from above table[/bold]")
    #     for deployments in deployment_jobs:
    #         if deployment_id == deployments['id']:
    #             deployment = deployments
    #             break
    #     if not deployment:
    #         console.print("[red]❌ Invalid ID. Please choose a valid ID from the table.[/red]")

    deployment = get_deployments_list(response)
    deployment_id = deployment['id']

    payload = {
        "test_passed" : True
    }

    response = deploy_manager.override_status(deployment_id,payload)
    if not response:
        console.print("[red]Overriding failed[/red]")
        return 
    console.print(f"[green]{response['message']}[/green]")

    response = deploy_manager.view_deployments(project_id)
    if response:
        modified_deployment =[]
        for deploy in response:
            if deployment_id ==deploy.get('id'):  

                # Safely extract nested fields
                deploy_experiment = deploy.get('deploy_experiment_runid') or {}
                experiment = deploy.get('experiment_runid') or {}
                user = deploy.get('user') or {}

                deploy['deploy_experiment_runid'] = str(deploy_experiment.get('id', ''))
                deploy['experiment_runid'] = str(experiment.get('id', ''))
                deploy['user'] = user.get('username', '')
                modified_deployment.append(deploy)
                break

        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={'results': modified_deployment},
            columns=deploy_manager.view_deployments_columns,
            title_prefix="Updated deployment",
            row_formatter=table_display.format_project_row
        )

from rich.table import Table

@deploy.command(name='ready')
def view_promoted_experiments():
    """View promoted experiments for a specific project."""
    
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)

    # Step 1: List and select project
    selected_project = get_project_list()
    project_id = selected_project['id']

    # Step 2: Fetch promoted experiments
    console.print(f"\n[bold blue]Fetching promoted experiments for project {project_id}...[/bold blue]")
    promoted_experiments = experiments_manager.get_promoted_experiments(project_id)

    if not promoted_experiments or 'projects' not in promoted_experiments or not promoted_experiments['projects']:
        console.print(f"[red]No promoted experiments found for project {project_id}.[/red]\n")
        return
    
    # Step 3: Extract and display promoted experiments
    project_data = next((proj for proj in promoted_experiments['projects'] if str(proj['project_id']) == str(project_id)), None)

    if not project_data or 'runs' not in project_data or not project_data['runs']:
        console.print(f"[red]No promoted experiments found for project {project_id}.[/red]")
        return

    runs = project_data['runs']
    for run in runs:
        run['started_at'] = beautify_datetime(run['started_at'])
        run['completed_at'] = beautify_datetime(run['completed_at'])
        run['created_at'] = beautify_datetime(run['created_at'])

    # Now display the full table directly
    table = Table(title="Promoted Experiments", show_lines=True)

    table.add_column("Experiment Code", style="magenta")
    table.add_column("Version", style="yellow")
    table.add_column("Experiment Name", style="cyan")
    table.add_column("Executed By", style="green")
    table.add_column("Target Column", style="blue")
    table.add_column("Train/Test Split", style="white")
    table.add_column("Started At", style="white")

    for run in runs:
        table.add_row(
            run.get('experiment_group_code', 'N/A'),
            run.get('version', 'N/A'),
            run.get('experiment_name', 'N/A'),
            run.get('executed_by', 'N/A'),
            run.get('target_column', 'N/A'),
            str(run.get('train_test_split', 'N/A')),
            run.get('started_at') or 'N/A',
        )

    console.print(table)



if __name__ == "__main__":
    deploy()