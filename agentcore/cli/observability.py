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
from rich import box
from rich.traceback import install
from rich.panel import Panel
from rich.prompt import Prompt
from typing import Optional
import json
from collections import defaultdict
from datetime import datetime
from rich.syntax import Syntax
from rich.box import MINIMAL_HEAVY_HEAD
import matplotlib.pyplot as plt
import seaborn as sns
from rich.prompt import Prompt
from rich.traceback import install
from agentcore.managers.observability_manager import ObservabilityManager
from agentcore.managers.base import BaseManager
from agentcore.managers.table_manager import TableDisplay
from rich import print as rprint
import requests
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys
from agentcore.managers.client import APIClient, APIError
from agentcore.managers.config import ConfigManager
from agentcore.managers.observability_manager import ObservabilityManager
from agentcore.managers.projects_manager import ProjectManager
from agentcore.cli.experiments.helpers import get_project_list, beautify_datetime

install()

console = Console()

@click.group()
def observability():
    """Project observability management commands."""
    pass


@observability.command('view')
@BaseManager.handle_api_error
def view_observability():
    """View Deployments for a Project"""
    
    observability_manager = ObservabilityManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)
    base_manager = BaseManager()

    # Step 1: List and select project
    selected_project = get_project_list()
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")

    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch deployment listing
    deployments_data = observability_manager.get_listing(str(project_id))
    if not deployments_data or 'models' not in deployments_data or not deployments_data['models']:
        console.print(f"[red]No deployment records found for project {project_id}.[/red]")
        return

    deployments = deployments_data["models"]

    # Step 3: Format deployment data for display
    for deployment in deployments:
        # Beautify datetime fields
        if 'promoted_at' in deployment and deployment['promoted_at']:
            deployment['promoted_at'] = beautify_datetime(deployment['promoted_at'])
        if 'created_at' in deployment.get('deployment_job', {}):
            deployment['deployment_job']['created_at'] = beautify_datetime(deployment['deployment_job']['created_at'])
        if 'updated_at' in deployment.get('deployment_job', {}):
            deployment['deployment_job']['updated_at'] = beautify_datetime(deployment['deployment_job']['updated_at'])
        
        # Extract username from promoted_by object
        if 'promoted_by' in deployment and deployment['promoted_by']:
            if isinstance(deployment['promoted_by'], dict):
                deployment['promoted_by'] = deployment['promoted_by'].get('username', 'N/A')
        else:
            deployment['promoted_by'] = 'N/A'
        
        # Ensure other fields are properly formatted
        deployment['status'] = deployment.get('status', 'N/A')
        deployment['api_endpoint'] = deployment.get('api_endpoint', 'N/A')

    # Step 4: Display deployments using paginate_data
    columns = (observability_manager.deployment_list_columns
               if hasattr(observability_manager, 'deployment_list_columns')
               else ['id', 'status', 'promoted_by', 'promoted_at', 'api_endpoint'])

    row_formatter = getattr(table_display, 'format_deployments_row', 
                          lambda item, cols: [str(item.get(col, '')) for col in cols])

    base_manager.paginate_data(
        data=deployments,
        columns=columns,
        title_prefix="Deployments",
        row_formatter=row_formatter,
        # search_fields=["id", "status", "promoted_by", "api_endpoint"],  # Customize as needed
    )



@observability.command('metrics')
@BaseManager.handle_api_error
def view_metrics():
    """View Observability Metrics for a Deployment"""
    
    observability_manager = ObservabilityManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)
    base_manager = BaseManager()

    # Step 1: List and select project
    selected_project = get_project_list()
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")

    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch deployment listing
    deployments_data = observability_manager.get_listing(str(project_id))
    if not deployments_data or 'models' not in deployments_data or not deployments_data['models']:
        console.print(f"[red]No deployment records found for project {project_id}.[/red]")
        return

    deployments = deployments_data["models"]

    # Step 3: Prepare deployment options for tab completion
    deployment_options = []
    deployment_map = {}
    
    for deployment in deployments:
        promoted_by = deployment.get('promoted_by', {}).get('username', 'Unknown') if deployment.get('promoted_by') else 'Unknown'
        promoted_at = beautify_datetime(deployment.get('promoted_at', '')) if deployment.get('promoted_at') else 'Unknown'
        status = deployment.get('status', 'Unknown')
        
        display_name = f"{deployment['id'][:8]}... - {status} - by {promoted_by} - {promoted_at}"
        deployment_options.append(display_name)
        deployment_map[display_name] = deployment

    # Step 4: Show available deployments first
    console.print("\n[bold blue]Available Deployments:[/bold blue]")
    deployment_table = Table()
    deployment_table.add_column("Short ID", style="cyan", no_wrap=True)
    deployment_table.add_column("Status", style="green")
    deployment_table.add_column("Promoted By", style="blue")
    deployment_table.add_column("Promoted At", style="yellow")
    deployment_table.add_column("API Endpoint", style="white")
    
    for deployment in deployments:
        promoted_by = deployment.get('promoted_by', {}).get('username', 'N/A') if deployment.get('promoted_by') else 'N/A'
        promoted_at = beautify_datetime(deployment.get('promoted_at', '')) if deployment.get('promoted_at') else 'N/A'
        
        deployment_table.add_row(
            deployment['id'][:8] + "...",
            deployment.get('status', 'N/A'),
            promoted_by,
            promoted_at,
            deployment.get('api_endpoint', 'N/A')
        )
    
    console.print(deployment_table)

    # Step 5: Use tab completion to select deployment
    console.print(f"\n[bold yellow]Select a deployment (you can type partial ID or use tab completion):[/bold yellow]")
    
    try:
        selected_display = base_manager.get_input_with_tab_completion(
            "Select deployment", 
            deployment_options
        )
        
        if selected_display not in deployment_map:
            console.print("[red]Invalid selection. Please try again.[/red]")
            return
            
        selected_deployment = deployment_map[selected_display]
        
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Operation cancelled.[/red]")
        return

    # Step 6: Get experiment ID from the selected deployment

    experiment_run_id = selected_deployment['id']
    
    console.print(f"\n[bold green]Selected Deployment: {selected_deployment['id'][:8]}... (Experiment Run ID: {experiment_run_id})[/bold green]")

    # Step 7: Fetch metrics
    with console.status("[bold green]Fetching observability metrics..."):
        metrics_data = observability_manager.get_new_metrics(str(experiment_run_id))
    
    if not metrics_data:
        console.print(f"[red]No metrics found for experiment run ID {experiment_run_id}.[/red]")
        return

    # Step 8: Display metrics overview and allow metric selection
    if 'metrics' not in metrics_data:
        console.print("[red]No metrics data found in response.[/red]")
        return

    metrics = metrics_data['metrics']
    
    # Show overall uptime if available
    if 'uptime' in metrics_data:
        console.print(f"\n[bold green]📈 System Uptime: {metrics_data['uptime']} hours[/bold green]")
    
    console.print(f"\n[bold blue]📊 Metrics Overview for Deployment {selected_deployment['id'][:8]}...[/bold blue]")
    
    # Create metrics overview table
    overview_table = Table(title="Metrics Summary")
    overview_table.add_column("Metric", style="cyan", no_wrap=True)
    overview_table.add_column("Data Points", style="yellow")
    overview_table.add_column("Latest Value", style="green")
    overview_table.add_column("Average", style="blue")
    overview_table.add_column("Min/Max", style="magenta")
    overview_table.add_column("Time Range", style="white")
    
    metric_details = {}
    
    for metric_name, metric_data in metrics.items():
        if not metric_data:
            continue
            
        # Calculate summary stats
        values = [entry['metric_value'] for entry in metric_data if isinstance(entry.get('metric_value'), (int, float))]
        timestamps = [entry['timestamp'] for entry in metric_data if entry.get('timestamp')]
        
        if values and timestamps:
            latest_entry = max(metric_data, key=lambda x: x.get('timestamp', ''))
            latest_value = latest_entry.get('metric_value', 'N/A')
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            
            # Sort timestamps to get range
            sorted_timestamps = sorted(timestamps)
            time_range = f"{beautify_datetime(sorted_timestamps[0])} to {beautify_datetime(sorted_timestamps[-1])}"
            
            # Format values based on metric type
            def format_metric_value(value, metric_name):
                if not isinstance(value, (int, float)):
                    return str(value)
                if 'percent' in metric_name or 'rate' in metric_name:
                    return f"{value:.1f}%"
                elif 'mb' in metric_name or 'memory' in metric_name:
                    return f"{value:.1f} MB"
                elif 'sec' in metric_name or 'latency' in metric_name or 'time' in metric_name:
                    return f"{value:.3f}s"
                elif 'count' in metric_name or 'requests' in metric_name or 'rps' in metric_name:
                    return f"{value:.0f}"
                elif 'hours' in metric_name:
                    return f"{value:.1f}h"
                else:
                    return f"{value:.2f}"
            
            formatted_latest = format_metric_value(latest_value, metric_name)
            formatted_avg = format_metric_value(avg_value, metric_name)
            formatted_min = format_metric_value(min_value, metric_name)
            formatted_max = format_metric_value(max_value, metric_name)
            
            overview_table.add_row(
                metric_name.replace('_', ' ').title(),
                str(len(metric_data)),
                formatted_latest,
                formatted_avg,
                f"{formatted_min} / {formatted_max}",
                time_range
            )
            
            # Store details for later use
            metric_details[metric_name] = {
                'data': metric_data,
                'values': values,
                'latest': latest_value,
                'avg': avg_value,
                'min': min_value,
                'max': max_value
            }
        else:
            overview_table.add_row(
                metric_name.replace('_', ' ').title(),
                str(len(metric_data)),
                "No data",
                "No data",
                "No data",
                "No data"
            )
    
    console.print(overview_table)
    
    # Step 9: Allow user to drill down into specific metrics
    if metric_details:
        console.print(f"\n[bold yellow]📋 Available actions:[/bold yellow]")
        console.print("1. View detailed data for a specific metric")
        console.print("2. Export all metrics to file")
        console.print("3. Exit")
        
        while True:
            choice = click.prompt("\nSelect an option", type=click.Choice(['1', '2', '3']), default='3')
            
            if choice == '3':
                break
            elif choice == '2':
                # Export functionality
                _export_metrics_data(selected_deployment, experiment_run_id, metrics_data)
                break
            elif choice == '1':
                # Metric selection for detailed view
                metric_names = list(metric_details.keys())
                formatted_names = [name.replace('_', ' ').title() for name in metric_names]
                
                console.print(f"\n[bold cyan]Select a metric to view in detail:[/bold cyan]")
                try:
                    selected_metric_display = base_manager.get_input_with_tab_completion(
                        "Select metric",
                        formatted_names
                    )
                    
                    # Find the original metric name
                    selected_metric = None
                    for original, formatted in zip(metric_names, formatted_names):
                        if formatted == selected_metric_display:
                            selected_metric = original
                            break
                    
                    if selected_metric and selected_metric in metric_details:
                        _show_detailed_metric_view(selected_metric, metric_details[selected_metric], base_manager)
                    else:
                        console.print("[red]Invalid metric selection.[/red]")
                        
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[red]Operation cancelled.[/red]")
                    break


def _show_detailed_metric_view(metric_name: str, metric_details: dict, base_manager):
    """Show detailed view of a specific metric with pagination"""
    data = metric_details['data']
    
    console.print(f"\n[bold blue]📊 Detailed View: {metric_name.replace('_', ' ').title()}[/bold blue]")
    
    # Show summary first
    summary_table = Table(title=f"{metric_name} Statistics")
    summary_table.add_column("Statistic", style="bold cyan")
    summary_table.add_column("Value", style="green")
    
    def format_value(value, metric_name):
        if not isinstance(value, (int, float)):
            return str(value)
        if 'percent' in metric_name or 'rate' in metric_name:
            return f"{value:.1f}%"
        elif 'mb' in metric_name or 'memory' in metric_name:
            return f"{value:.1f} MB"
        elif 'sec' in metric_name or 'latency' in metric_name or 'time' in metric_name:
            return f"{value:.3f}s"
        elif 'count' in metric_name or 'requests' in metric_name or 'rps' in metric_name:
            return f"{value:.0f}"
        elif 'hours' in metric_name:
            return f"{value:.1f}h"
        else:
            return f"{value:.2f}"
    
    summary_table.add_row("Total Data Points", str(len(data)))
    summary_table.add_row("Latest Value", format_value(metric_details['latest'], metric_name))
    summary_table.add_row("Average", format_value(metric_details['avg'], metric_name))
    summary_table.add_row("Minimum", format_value(metric_details['min'], metric_name))
    summary_table.add_row("Maximum", format_value(metric_details['max'], metric_name))
    
    console.print(summary_table)
    
    # Sort data by timestamp (newest first)
    sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Use base_manager pagination for the detailed data
    console.print(f"\n[bold yellow]📋 Recent Data Points (showing newest first):[/bold yellow]")
    
    # Prepare data for pagination
    display_data = []
    for entry in sorted_data:
        display_data.append({
            'timestamp': beautify_datetime(entry.get('timestamp', '')),
            'value': format_value(entry.get('metric_value', 'N/A'), metric_name),
            'promote_id': entry.get('promote_id', '')[:8] + "..." if entry.get('promote_id') else 'N/A'
        })
    
    # Define columns for the detailed view
    columns = ['timestamp', 'value', 'promote_id']
    
    def row_formatter(item, cols):
        return [str(item.get(col, '')) for col in cols]
    
    base_manager.paginate_data(
        data=display_data,
        columns=columns,
        title_prefix=f"{metric_name.replace('_', ' ').title()} Data",
        row_formatter=row_formatter
    )


def _export_metrics_data(selected_deployment: dict, experiment_run_id: str, metrics_data: dict):
    """Export metrics data to JSON file"""
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"observability_metrics_{selected_deployment['id'][:8]}_{timestamp}.json"
    
    try:
        export_data = {
            'deployment_info': {
                'deployment_id': selected_deployment['id'],
                'experiment_run_id': experiment_run_id,
                'status': selected_deployment.get('status'),
                'api_endpoint': selected_deployment.get('api_endpoint'),
                'promoted_at': selected_deployment.get('promoted_at'),
                'promoted_by': selected_deployment.get('promoted_by', {}).get('username') if selected_deployment.get('promoted_by') else None
            },
            'metrics_data': metrics_data,
            'exported_at': datetime.now().isoformat(),
            'exported_by': 'aryan2899'
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        console.print(f"[green]✅ Metrics data saved to {filename}[/green]")
        
        # Show file size
        import os
        file_size = os.path.getsize(filename)
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        console.print(f"[dim]File size: {size_str}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error saving file: {str(e)}[/red]")


if __name__ == "__main__":
    observability()
