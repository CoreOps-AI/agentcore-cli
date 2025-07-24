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
from agentcore.managers.projects_manager import ProjectManager
from rich.syntax import Syntax
import json

console = Console()

@experiments.command(name='view')
@BaseManager.handle_api_error
def view_experiments():
    "View Experiments with Project ID"
    
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)
    base_manager = BaseManager()

    # Step 1: List and select project
    selected_project = get_project_list()

    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")

    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch experiments using the provided fetch_experiments function
    experiments_data = experiments_manager.fetch_experiments(project_id)
    if not experiments_data or 'results' not in experiments_data or not experiments_data['results']:
        console.print(f"[red]No experiment records found for project {project_id}.[/red]")
        return

    experiments = experiments_data["results"]

    # Beautify datetime fields
    for exp in experiments:
        if 'run_at' in exp:
            exp['run_at'] = beautify_datetime(exp['run_at'])
        if 'created_at' in exp:
            exp['created_at'] = beautify_datetime(exp['created_at'])
        exp['model'] = exp['model_display_name']

    # Display experiments table
    # console.print("[bold blue]Experiments for selected project:[/bold blue]")
    # table_display.display_table(
    #     response_data={'results': experiments, 'count': len(experiments)},
    #     columns=experiments_manager.experiment_list_by_project_columns if hasattr(experiments_manager, 'experiment_list_by_project_columns') else list(experiments[0].keys()),
    #     title_prefix="Experiments",
    #     row_formatter=getattr(table_display, 'format_experiments_row', None)

    # Display using paginate_data
    columns = (experiments_manager.experiment_list_by_project_columns
               if hasattr(experiments_manager, 'experiment_list_by_project_columns')
               else list(experiments[0].keys()))

    row_formatter = getattr(table_display, 'format_experiments_row', lambda item, cols: [str(item.get(col, '')) for col in cols])

    base_manager.paginate_data(
        data=experiments,
        columns=experiments_manager.experiments_columns,
        title_prefix="Experiments",
        row_formatter=row_formatter,
        # search_fields=["id", "name", "run_at", "created_at"],  # Customize as needed
    )


@experiments.command(name='config')
@BaseManager.handle_api_error
def view_experiment_config():
    """View the full configuration of a specific experiment"""
    console = Console()
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)

    # Step 1: List and select project (same as your existing code)
    selected_project = get_project_list()
 
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
 
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    selected_experiment = get_experiments_by_project_search_list(project_id)
    if not selected_experiment:
        return None
    # # Step 2: Fetch experiments
    # experiments_data = experiments_manager.display_experiment_info(project_id)
    # if not experiments_data or 'results' not in experiments_data or not experiments_data['results']:
    #     console.print(f"[red]No experiment records found for project {project_id}.[/red]")
    #     return

    # experiments = experiments_data["results"]
    # experiments.sort(key =lambda x: x['created_at'])

    # # Step 3: Display experiments table for selection
    # console.print("[bold blue]Available Experiments:[/bold blue]")
    
    # # Create a simplified table for selection
    # selection_table = Table(title="Select an Experiment")
    # selection_table.add_column("Index", style="cyan", no_wrap=True)
    # selection_table.add_column("Experiment Code", style="magenta")
    # selection_table.add_column("Run ID", style="green")
    # selection_table.add_column("Version", style="yellow")
    # selection_table.add_column("Data Source", style="blue")

    # for idx, exp in enumerate(experiments):
    #     selection_table.add_row(
    #         str(idx + 1),
    #         exp.get('experiment_group_code', 'N/A'),
    #         str(exp.get('run_id', 'N/A')),
    #         exp.get('version', 'N/A'),
    #         exp.get('data_source', 'N/A')
    #     )

    # console.print(selection_table)

    # # Step 4: Get user selection
    # while True:
    #     try:
    #         selection = Prompt.ask(
    #             f"Select experiment (1-{len(experiments)})",
    #             default="1"
    #         )
    #         selected_index = int(selection) - 1
    #         if 0 <= selected_index < len(experiments):
    #             break
    #         else:
    #             console.print(f"[red]Please enter a number between 1 and {len(experiments)}[/red]")
    #     except ValueError:
    #         console.print("[red]Please enter a valid number[/red]")

    # selected_experiment = experiments[selected_index]
    
    # Step 5: Display the full configuration
    console.print(f"\n[bold green]Configuration for Experiment {selected_experiment.get('experiment_group_code')}:[/bold green]")
    
    full_config = selected_experiment.get('full_config', {})
    
    if not full_config:
        console.print("[red]No configuration data available for this experiment.[/red]")
        return

    # Display basic experiment info
    basic_info_table = Table(title="Basic Information", show_header=True)
    basic_info_table.add_column("Field", style="cyan", no_wrap=True)
    basic_info_table.add_column("Value", style="white")

    basic_fields = [
        ("Experiment Code", full_config.get('experiment_group_code')),
        ("Experiment Name", full_config.get('experiment_name')),
        ("Task", full_config.get('task')),
        ("Model", full_config.get('model')),
        ("Version", full_config.get('version')),
        ("Created By", full_config.get('created_by')),
        ("Created At", beautify_datetime(full_config.get('timestamp')) if full_config.get('timestamp') else 'N/A'),
        ("Description", full_config.get('description')),
    ]

    for field, value in basic_fields:
        basic_info_table.add_row(field, str(value) if value is not None else 'N/A')

    console.print(basic_info_table)

    # Display model parameters
    model_params = full_config.get('model_params', {})
    if model_params:
        console.print("\n[bold blue]Model Parameters:[/bold blue]")
        params_table = Table(show_header=True)
        params_table.add_column("Parameter", style="cyan")
        params_table.add_column("Value", style="white")

        for param, value in model_params.items():
            params_table.add_row(param, str(value))

        console.print(params_table)

    # Display data information
    console.print("\n[bold blue]Data Configuration:[/bold blue]")
    data_table = Table(show_header=True)
    data_table.add_column("Field", style="cyan")
    data_table.add_column("Value", style="white")

    data_fields = [
        ("Data ID", full_config.get('data_id')),
        ("Target Column", full_config.get('target_column')),
        ("Date Column", full_config.get('date_column') or 'N/A'),
        ("Train/Test Split", full_config.get('train_test_split')),
        ("Feature Columns", ', '.join(full_config.get('feature_columns', [])) if full_config.get('feature_columns') else 'N/A'),
    ]

    for field, value in data_fields:
        data_table.add_row(field, str(value) if value is not None else 'N/A')

    console.print(data_table)

    # Display raw data info
    raw_data_info = full_config.get('raw_data_info', {})
    if raw_data_info:
        console.print("\n[bold blue]Data Source Information:[/bold blue]")
        raw_data_table = Table(show_header=True)
        raw_data_table.add_column("Field", style="cyan")
        raw_data_table.add_column("Value", style="white")

        raw_data_fields = [
            ("Data Source ID", raw_data_info.get('data_source_id')),
            ("Description", raw_data_info.get('data_source_description')),
            ("Internal ID", raw_data_info.get('data_source_internal_id')),
        ]

        for field, value in raw_data_fields:
            raw_data_table.add_row(field, str(value) if value is not None else 'N/A')

        console.print(raw_data_table)

    # Option to show raw JSON
    show_raw = Prompt.ask(
        "\nWould you like to see the raw configuration JSON?",
        choices=["y", "n"],
        default="n"
    )

    if show_raw.lower() == 'y':
        console.print("\n[bold blue]Raw Configuration JSON:[/bold blue]")
        console.print(Panel(
            Syntax(
                json.dumps(full_config, indent=2),
                "json",
                theme="monokai",
                line_numbers=True
            ),
            title="Full Configuration",
            expand=False
        ))

@experiments.command(name='plots')
@BaseManager.handle_api_error
def view_experiment_plots():
    """View plots for a specific experiment"""
    console = Console()
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)

    # Step 1: List and select project (same as your existing code)
    selected_project = get_project_list()
 
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
 
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch all experiments with plots for the project
    console.print(f"[bold blue]\nFetching experiments with plots for project {project_id}...[/bold blue]")
    
    try:
        plots_data = experiments_manager.display_plots(project_id)
    except Exception as e:
        console.print(f"[red]Error fetching plots: {e}[/red]")
        return
    
    if not plots_data or 'results' not in plots_data or not plots_data['results']:
        console.print(f"[red]No experiments with plots found for project {project_id}.[/red]\n")
        return

    experiments_with_plots = plots_data['results']
    
    # Filter experiments that actually have plots
    experiments_with_available_plots = []
    for exp in experiments_with_plots:
        if exp.get('plots') and len(exp['plots']) > 0:
            experiments_with_available_plots.append(exp)
    
    if not experiments_with_available_plots:
        console.print(f"[red]No experiments with available plots found for project {project_id}.[/red]")
        return

    # Step 3: Display experiments that have plots
    console.print(f"\n[bold blue]Experiments with Available Plots ({len(experiments_with_available_plots)} found):[/bold blue]")
    
    selected_experiment = get_experiments_by_project_search_list(data = experiments_with_available_plots)
    if not selected_experiment:
        return None

    experiment_code = selected_experiment.get('experiment_group_code')
    plots = selected_experiment.get('plots', [])

    # Step 5: Display available plots for the selected experiment
    console.print(f"\n[bold blue]Available Plots for Experiment {experiment_code} ({len(plots)} plots):[/bold blue]")
    
    plots_table = Table(title="Select a Plot to View")
    plots_table.add_column("Index", style="cyan", no_wrap=True)
    plots_table.add_column("Plot Type", style="magenta")
    plots_table.add_column("Status", style="green")

    for idx, plot in enumerate(plots):
        plot_type = plot.get('plot_type', 'Unknown')
        has_image = "✓ Available" if plot.get('image_base64') else "✗ No Image"
        plots_table.add_row(
            str(idx + 1),
            plot_type,
            has_image
        )

    console.print(plots_table)

    # Step 6: Plot selection and viewing loop
    while True:
        try:
            plot_selection = Prompt.ask(
                f"Select plot to view (1-{len(plots)}), 'a' for all plots, or 'q' to quit",
                default="1"
            )
            
            if plot_selection.lower() == 'q':
                console.print("[yellow]Exiting plot viewer.[/yellow]")
                break
            elif plot_selection.lower() == 'a':
                # Display all plots
                for idx, plot in enumerate(plots):
                    console.print(f"\n[bold cyan]═══ Plot {idx + 1} of {len(plots)} ═══[/bold cyan]")
                    display_plot(console, plot, experiment_code, idx + 1)
                
                # Ask if user wants to continue
                continue_viewing = Prompt.ask(
                    "\nWould you like to select individual plots or quit?",
                    choices=["select", "quit"],
                    default="quit"
                )
                
                if continue_viewing.lower() == 'quit':
                    break
                else:
                    continue
            else:
                plot_index = int(plot_selection) - 1
                if 0 <= plot_index < len(plots):
                    selected_plot = plots[plot_index]
                    display_plot(console, selected_plot, experiment_code, plot_index + 1)
                    
                    # Ask if user wants to view another plot
                    continue_viewing = Prompt.ask(
                        "\nWould you like to view another plot?",
                        choices=["y", "n"],
                        default="y"
                    )
                    
                    if continue_viewing.lower() == 'n':
                        break
                else:
                    console.print(f"[red]Please enter a number between 1 and {len(plots)}, 'a' for all, or 'q' to quit[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number, 'a' for all, or 'q' to quit[/red]")


def display_plot(console, plot_data, experiment_code, plot_number):
    """Display a single plot"""
    plot_type = plot_data.get('plot_type', 'Unknown')
    image_base64 = plot_data.get('image_base64')
    
    console.print(f"\n[bold green]Plot {plot_number}: {plot_type} for Experiment {experiment_code}[/bold green]")
    
    if not image_base64:
        console.print("[red]No image data available for this plot.[/red]")
        return
    
    # Simplified - just save the file and optionally open it
    save_plot_to_file(console, image_base64, experiment_code, plot_type, plot_number)


def save_plot_to_file(console, image_base64, experiment_code, plot_type, plot_number):
    """Save plot to file and optionally open it"""
    import base64
    import os
    from datetime import datetime
    
    try:
        # Create plots directory if it doesn't exist
        plots_dir = "experiment_plots"
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)
        
        # Create filename with current date
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{plots_dir}/exp_{experiment_code}_{plot_type}_plot{plot_number}_{timestamp}.png"
        
        # Decode and save
        image_data = base64.b64decode(image_base64)
        
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        console.print(f"[green]✓ Plot saved as: {filename}[/green]")
        
        # Ask if user wants to open the file
        open_file = Prompt.ask(
            "Would you like to open the plot file?",
            choices=["y", "n"],
            default="y"
        )
        
        if open_file.lower() == 'y':
            try:
                import webbrowser
                import os
                file_path = os.path.abspath(filename)
                webbrowser.open(f'file://{file_path}')
                console.print("[green]✓ Plot opened in default image viewer.[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not open file automatically: {e}[/yellow]")
                console.print(f"[yellow]Please open manually: {os.path.abspath(filename)}[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error saving plot: {e}[/red]")

@experiments.command(name='metrics')
@BaseManager.handle_api_error
def view_experiment_metrics():
    """View metrics for experiments in a specific project"""
    console = Console()
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)

    # Step 1: List and select project (same as your existing code)
    selected_project = get_project_list()
 
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
 
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch metrics for the project
    console.print(f"\n[bold blue]Fetching metrics for project {project_id}...[/bold blue]")
    
    try:
        metrics_data = experiments_manager.metrics(project_id)
    except Exception as e:
        console.print(f"\n[red]Error fetching metrics: {e}[/red]")
        return
    
    if not metrics_data or 'results' not in metrics_data or not metrics_data['results']:
        console.print(f"[red]No experiments with metrics found for project {project_id}.[/red]\n")
        return

    experiments_with_metrics = metrics_data['results']
    
    # Filter experiments that actually have metrics
    experiments_with_available_metrics = []
    for exp in experiments_with_metrics:
        # Check if experiment has any metric fields (exclude basic info fields)
        has_metrics = any(key in exp for key in ['r2', 'mae', 'mse', 'rmse', 'mape', 'aic', 'bic'])
        if has_metrics:
            experiments_with_available_metrics.append(exp)
    
    if not experiments_with_available_metrics:
        console.print(f"[red]No experiments with available metrics found for project {project_id}.[/red]")
        return

    # Step 3: Display experiments that have metrics
    console.print(f"\n[bold blue]Experiments with Available Metrics ({len(experiments_with_available_metrics)} found):[/bold blue]")
    
    selected_experiment = get_experiments_by_project_search_list(data = experiments_with_available_metrics)
    if not selected_experiment:
        return None
    display_experiment_metrics(console, selected_experiment)



def display_experiment_metrics(console, experiment_data):
    """Display comprehensive metrics for a single experiment"""
    experiment_code = experiment_data.get('experiment_group_code', 'N/A')
    run_id = experiment_data.get('run_id', 'N/A')
    
    console.print(f"\n[bold green]Metrics for Experiment {experiment_code} (Run ID: {run_id})[/bold green]")

    # Basic experiment info
    basic_info_table = Table(title="Experiment Information", show_header=True)
    basic_info_table.add_column("Field", style="cyan", no_wrap=True)
    basic_info_table.add_column("Value", style="white")

    basic_fields = [
        ("Experiment Code", experiment_data.get('experiment_group_code')),
        ("Run ID", experiment_data.get('run_id')),
        ("Version", experiment_data.get('version')),
        ("Data Version", experiment_data.get('data_version')),
        ("Data Source", experiment_data.get('data_source')),
    ]

    for field, value in basic_fields:
        basic_info_table.add_row(field, str(value) if value is not None else 'N/A')

    console.print(basic_info_table)

    # Core Performance Metrics
    core_metrics = ['r2', 'mae', 'mse', 'rmse', 'mape', 'medae', 'explained_variance', 'msle', 'smape']
    core_metrics_data = []
    
    for metric in core_metrics:
        if metric in experiment_data and experiment_data[metric] is not None:
            metric_value = experiment_data[metric].get(metric, 'N/A') if isinstance(experiment_data[metric], dict) else experiment_data[metric]
            core_metrics_data.append((metric.upper(), format_metric_value(metric_value)))
    
    if core_metrics_data:
        console.print(f"\n[bold blue]Core Performance Metrics:[/bold blue]")
        core_table = Table(show_header=True)
        core_table.add_column("Metric", style="cyan")
        core_table.add_column("Value", style="white")
        
        for metric_name, metric_value in core_metrics_data:
            core_table.add_row(metric_name, metric_value)
        
        console.print(core_table)

    # Additional Metrics
    additional_metrics = ['directional_accuracy', 'mpe', 'mfe', 'mase', 'aic', 'bic']
    additional_metrics_data = []
    
    for metric in additional_metrics:
        if metric in experiment_data and experiment_data[metric] is not None:
            metric_value = experiment_data[metric].get(metric, 'N/A') if isinstance(experiment_data[metric], dict) else experiment_data[metric]
            additional_metrics_data.append((metric.upper(), format_metric_value(metric_value)))
    
    if additional_metrics_data:
        console.print(f"\n[bold blue]Additional Metrics:[/bold blue]")
        additional_table = Table(show_header=True)
        additional_table.add_column("Metric", style="cyan")
        additional_table.add_column("Value", style="white")
        
        for metric_name, metric_value in additional_metrics_data:
            additional_table.add_row(metric_name, metric_value)
        
        console.print(additional_table)

    # Rolling Metrics (if available)
    rolling_metrics = ['rolling_mae_w5', 'rolling_mse_w5']
    for rolling_metric in rolling_metrics:
        if rolling_metric in experiment_data and experiment_data[rolling_metric] is not None:
            rolling_data = experiment_data[rolling_metric].get(rolling_metric, []) if isinstance(experiment_data[rolling_metric], dict) else experiment_data[rolling_metric]
            if rolling_data and isinstance(rolling_data, list):
                display_rolling_metrics(console, rolling_metric, rolling_data)

    # Option to save metrics to JSON
    save_option = Prompt.ask(
        "\nWould you like to save these metrics to a JSON file?",
        choices=["y", "n"],
        default="n"
    )
    
    if save_option.lower() == 'y':
        save_metrics_to_file(console, experiment_data, experiment_code)

@experiments.command(name='system-metrics')
@BaseManager.handle_api_error
def view_experiment_system_metrics():
    """View system metrics for experiments in a specific project"""
    console = Console()
    experiments_manager = ExperimentManager()
    project_manager = ProjectManager()
    table_display = TableDisplay(console)

    # Step 1: List and select project (same as your existing code)
    selected_project = get_project_list()
    
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Step 2: Fetch system metrics for the project
    console.print(f"\n[bold blue]Fetching system metrics for project {project_id}...[/bold blue]")
    
    try:
        system_metrics_data = experiments_manager.system_metrics(project_id)
    except Exception as e:
        console.print(f"[red]Error fetching system metrics: {e}[/red]")
        return
    
    if not system_metrics_data or 'results' not in system_metrics_data or not system_metrics_data['results']:
        console.print(f"[red]No experiments with system metrics found for project {project_id}.[/red]\n")
        return

    experiments_with_system_metrics = system_metrics_data['results']
    
    # Filter experiments that actually have system metrics
    experiments_with_available_system_metrics = []
    for exp in experiments_with_system_metrics:
        # Check if experiment has system_metrics field
        if 'system_metrics' in exp and exp['system_metrics'] is not None:
            experiments_with_available_system_metrics.append(exp)
    
    if not experiments_with_available_system_metrics:
        console.print(f"[red]No experiments with available system metrics found for project {project_id}.[/red]")
        return

    # Step 3: Display experiments that have system metrics
    console.print(f"\n[bold blue]Experiments with Available System Metrics ({len(experiments_with_available_system_metrics)} found):[/bold blue]")

    selected_experiment = get_experiments_by_project_search_list(data = experiments_with_available_system_metrics)
    if not selected_experiment:
        return None
    display_experiment_system_metrics(console, selected_experiment)


def display_experiment_system_metrics(console: Console, experiment: Dict[str, Any]):
    """Display system metrics for a single experiment"""
    
    # Display experiment info
    exp_info_table = Table(title=f"Experiment {experiment.get('experiment_group_code', 'N/A')} - Run {experiment.get('run_id', 'N/A')}")
    exp_info_table.add_column("Property", style="cyan")
    exp_info_table.add_column("Value", style="white")
    
    exp_info_table.add_row("Experiment Code", str(experiment.get('experiment_group_code', 'N/A')))
    exp_info_table.add_row("Run ID", str(experiment.get('run_id', 'N/A')))
    exp_info_table.add_row("Version", str(experiment.get('version', 'N/A')))
    exp_info_table.add_row("Data Version", str(experiment.get('data_version', 'N/A')))
    exp_info_table.add_row("Data Source", str(experiment.get('data_source', 'N/A')))
    
    console.print(exp_info_table)
    
    # Display system metrics
    system_metrics = experiment.get('system_metrics', {})
    if not system_metrics:
        console.print("[red]No system metrics available for this experiment[/red]")
        return
    
    metrics_table = Table(title="System Metrics")
    metrics_table.add_column("Metric", style="yellow")
    metrics_table.add_column("Value", style="green")
    metrics_table.add_column("Unit", style="blue")
    
    # Add system metrics rows
    metrics_table.add_row("CPU Usage", f"{system_metrics.get('cpu_usage_percent', 'N/A')}", "%")
    
    # Format per-core CPU usage
    per_core_cpu = system_metrics.get('per_core_cpu', [])
    if per_core_cpu:
        per_core_str = ", ".join([f"Core {i+1}: {usage}%" for i, usage in enumerate(per_core_cpu)])
        metrics_table.add_row("Per-Core CPU", per_core_str, "")
    
    metrics_table.add_row("Memory Used", f"{system_metrics.get('memory_used_mb', 'N/A')}", "MB")
    metrics_table.add_row("Disk Read", f"{system_metrics.get('disk_read_mb', 'N/A')}", "MB")
    metrics_table.add_row("Disk Write", f"{system_metrics.get('disk_write_mb', 'N/A')}", "MB")
    
    gpu_usage = system_metrics.get('gpu_usage_percent')
    metrics_table.add_row("GPU Usage", f"{gpu_usage if gpu_usage is not None else 'N/A'}", "%" if gpu_usage is not None else "")
    
    metrics_table.add_row("Timestamp", str(system_metrics.get('timestamp', 'N/A')), "")
    metrics_table.add_row("Metrics ID", str(system_metrics.get('id', 'N/A')), "")
    
    console.print(metrics_table)
    console.print()  # Add spacing between experiments
def display_rolling_metrics(console, metric_name, rolling_data):
    """Display rolling metrics with basic statistics"""
    console.print(f"\n[bold blue]{metric_name.replace('_', ' ').title()}:[/bold blue]")
    
    # Calculate basic statistics
    import statistics
    
    try:
        avg_value = statistics.mean(rolling_data)
        min_value = min(rolling_data)
        max_value = max(rolling_data)
        median_value = statistics.median(rolling_data)
        
        stats_table = Table(show_header=True)
        stats_table.add_column("Statistic", style="cyan")
        stats_table.add_column("Value", style="white")
        
        stats_table.add_row("Count", str(len(rolling_data)))
        stats_table.add_row("Average", f"{avg_value:.6f}")
        stats_table.add_row("Minimum", f"{min_value:.6f}")
        stats_table.add_row("Maximum", f"{max_value:.6f}")
        stats_table.add_row("Median", f"{median_value:.6f}")
        
        console.print(stats_table)
        
        # Option to show all values
        show_all = Prompt.ask(
            f"Would you like to see all {len(rolling_data)} values?",
            choices=["y", "n"],
            default="n"
        )
        
        if show_all.lower() == 'y':
            console.print(f"\n[bold blue]All {metric_name} Values:[/bold blue]")
            
            # Display in chunks of 10 for better readability
            chunk_size = 10
            for i in range(0, len(rolling_data), chunk_size):
                chunk = rolling_data[i:i + chunk_size]
                values_str = ", ".join([f"{val:.6f}" for val in chunk])
                console.print(f"[{i+1:3d}-{min(i+chunk_size, len(rolling_data)):3d}]: {values_str}")
                
    except Exception as e:
        console.print(f"[red]Error calculating statistics for {metric_name}: {e}[/red]")


def format_metric_value(value):
    """Format metric values for display"""
    if isinstance(value, (int, float)):
        if abs(value) >= 1000:
            return f"{value:,.6f}"
        else:
            return f"{value:.6f}"
    return str(value)


def save_metrics_to_file(console, experiment_data, experiment_code):
    """Save experiment metrics to a JSON file"""
    import json
    import os
    from datetime import datetime
    
    try:
        # Create metrics directory if it doesn't exist
        metrics_dir = "experiment_metrics"
        if not os.path.exists(metrics_dir):
            os.makedirs(metrics_dir)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{metrics_dir}/metrics_{experiment_code}_{timestamp}.json"
        
        # Save metrics
        with open(filename, 'w') as f:
            json.dump(experiment_data, f, indent=2)
        
        console.print(f"[green]✓ Metrics saved as: {filename}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error saving metrics: {e}[/red]")

def get_all_model_types():
    """Fetch and display all models types."""
    console = Console()
    experiment_manager = ExperimentManager()
    base_manager = BaseManager()
    
    response = experiment_manager.all_model_types()

    if not response:
            console.print("[yellow]No model types found or invalid response format.[/yellow]")
            return
    
    response.sort(key=lambda x: x['id'])
    
    console.print("[bold green]Model Types:[/bold green]")
    base_manager.paginate_data(
        data=response,
        columns=experiment_manager.all_model_types_columns,
        title_prefix='Model Types List',
        row_formatter=TableDisplay().format_experiments_row,
        page_size=10
    )
@experiments.command(name="compare")
@BaseManager.handle_api_error
def experiment_metrics():
    """
    Fetch experiment run metrics by project ID with improved UX.
    Shows data in a clean, readable format with smart column selection.
    Dynamically handles both regression and classification metrics.
    """
    experiment_manager = ExperimentsManager()
    selected_project = get_project_list()
    project_id = selected_project['id']
    project_type_id = selected_project.get("project_type_id")
    console.print(f"[bold green]Selected Project ID: {project_id} (Type ID: {project_type_id})[/bold green]")

    # Fetch all experiment runs for project
    response = experiment_manager.get_experiment_metrics(project_id=int(project_id))
    if not response or not response.get("results"):
        console.print(f"[yellow]No experiment runs found for project_id-{project_id}.[/yellow]")
        return

    experiments_data = response.get("results", [])
    
    # Filter out failed experiments
    experiments_data = [item for item in experiments_data if item.get("status") != "failed"]
    
    if not experiments_data:
        console.print(f"[yellow]No non-failed experiment runs found for project_id-{project_id}.[/yellow]")
        return
    
    # Extract unique values for filtering
    unique_group_codes = sorted(set(item.get("experiment_group_code") for item in experiments_data if item.get("experiment_group_code")))
    unique_data_versions = sorted(set(str(item.get("data_version")) for item in experiments_data if item.get("data_version")))
    unique_data_sources = sorted(set(item.get("data_source") for item in experiments_data if item.get("data_source")))
    unique_statuses = sorted(set(item.get("status") for item in experiments_data if item.get("status") and item.get("status") != "failed"))
    unique_models = sorted(set(item.get("model_code") for item in experiments_data if item.get("model_code")))

    # Display available options in a clean format
    console.print("\n[bold cyan]📊 Available Options:[/bold cyan]")
    console.print(f"• Group Codes: [green]{', '.join(unique_group_codes)}[/green]")
    console.print(f"• Data Versions: [green]{', '.join(unique_data_versions)}[/green]")
    console.print(f"• Data Sources: [green]{', '.join(unique_data_sources)}[/green]")
    console.print(f"• Models: [green]{', '.join(unique_models)}[/green]")
    console.print(f"• Statuses: [green]{', '.join(unique_statuses)}[/green]")

    # Simplified filtering menu
    filter_choice = Prompt.ask("""
[bold]🔍 Choose filter:[/bold]
1. By Group Code(s)
2. By Data Version(s) 
3. By Model(s)
4. Show All
Enter choice (1-4)""", default="4")

    filters = {}
    if filter_choice == "1":
        input_codes = Prompt.ask(f"Enter Group Code(s) (comma-separated)")
        filters['experiment_group_code'] = [code.strip() for code in input_codes.split(",") if code.strip()]
    elif filter_choice == "2":
        input_versions = Prompt.ask(f"Enter Data Version(s) (comma-separated)")
        filters['data_version'] = [version.strip() for version in input_versions.split(",") if version.strip()]
    elif filter_choice == "3":
        input_models = Prompt.ask(f"Enter Model(s) (comma-separated)")
        filters['model_code'] = [model.strip() for model in input_models.split(",") if model.strip()]

    def round_metric(value):
        """Round metric values safely"""
        if isinstance(value, dict):
            # Handle nested dict structure like {'accuracy': 1.0}
            for key in value:
                return round_metric(value[key])
        elif isinstance(value, (int, float)):
            return round(float(value), 3)
        elif isinstance(value, str):
            try:
                return round(float(value), 3)
            except (ValueError, TypeError):
                return value
        return None

    def matches_filters(item, filters):
        """Check if item matches filters"""
        if item.get("status") == "failed":
            return False
        if not filters:
            return True
        for filter_key, filter_values in filters.items():
            if str(item.get(filter_key, "")) not in filter_values:
                return False
        return True

    def detect_and_extract_metrics(item):
        """Dynamically detect and extract metrics from experiment data"""
        metrics = {}
        
        # Define known metric categories
        regression_metrics = ['r2', 'mae', 'mse', 'rmse', 'mape', 'directional_accuracy', 'smape', 'mase', 'aic', 'bic', 'medae', 'explained_variance']
        classification_metrics = ['accuracy', 'balanced_accuracy', 'f1', 'precision', 'recall', 'roc_auc', 'log_loss']
        
        # Check for both direct metrics and nested dict metrics
        all_possible_metrics = regression_metrics + classification_metrics
        
        for metric in all_possible_metrics:
            if metric in item:
                value = round_metric(item[metric])
                if value is not None:
                    metrics[metric] = value
        
        return metrics

    # Process experiments and categorize by what data they have
    experiments_with_metrics = []
    experiments_with_errors = []
    experiments_with_rolling_only = []

    for item in experiments_data:
        if not matches_filters(item, filters):
            continue
            
        base_info = {
            "group_code": item.get("experiment_group_code", "N/A"),
            "version": item.get("version", "N/A"), 
            "data_version": item.get("data_version", "N/A"),
            "model": item.get("model_code", "N/A"),
            "status": item.get("status", "N/A"),
            "task_type": item.get("task_type", "N/A"),
            "created_at": item.get("created_at", "N/A")[:10] if item.get("created_at") else "N/A"
        }
        
        # Extract metrics dynamically
        detected_metrics = detect_and_extract_metrics(item)
        
        # Check for metric errors
        if 'metric_error' in item and item['metric_error']:
            error_msg = item['metric_error'].get('metric_error', '')
            if error_msg and "Error computing metrics" in error_msg:
                base_info['error'] = "❌ Metric Error"
                experiments_with_errors.append(base_info)
                continue
        
        # If we found standard metrics, add them
        if detected_metrics:
            base_info.update(detected_metrics)
            experiments_with_metrics.append(base_info)
            continue
        
        # Check for rolling metrics if no standard metrics
        rolling_count = 0
        for key in item:
            if key.startswith('rolling_') and isinstance(item[key], dict):
                rolling_data = item[key].get(key, [])
                if isinstance(rolling_data, list) and rolling_data:
                    avg_val = round(sum(rolling_data) / len(rolling_data), 3)
                    base_info[f"{key.replace('rolling_', '').replace('_w5', '')}_avg"] = avg_val
                    rolling_count += 1
        
        if rolling_count > 0:
            experiments_with_rolling_only.append(base_info)

    # Display results in sections
    total_found = len(experiments_with_metrics) + len(experiments_with_errors) + len(experiments_with_rolling_only)
    
    if total_found == 0:
        console.print("[yellow]No experiments found matching filters.[/yellow]")
        return

    console.print(f"\n[bold green]📈 Found {total_found} experiments[/bold green]")

    # 1. Show experiments with standard metrics (most important)
    if experiments_with_metrics:
        console.print(f"\n[bold blue]✅ Experiments with Standard Metrics ({len(experiments_with_metrics)}):[/bold blue]")
        
        # Smart column selection - only show columns that have data
        all_keys = set()
        for exp in experiments_with_metrics:
            all_keys.update(exp.keys())
        
        # Define column order with only populated columns
        base_cols = ["group_code", "model", "data_version", "task_type", "status"]
        
        # Dynamically determine metric columns based on what's available
        regression_metrics = ['r2', 'mae', 'mse', 'rmse', 'mape', 'directional_accuracy', 'smape', 'mase', 'aic', 'bic', 'medae', 'explained_variance']
        classification_metrics = ['accuracy', 'balanced_accuracy', 'f1', 'precision', 'recall', 'roc_auc', 'log_loss']
        
        # Prioritize metrics based on task type if available
        task_types = set(exp.get('task_type', '') for exp in experiments_with_metrics)
        
        if 'Classification' in task_types:
            priority_metrics = [col for col in classification_metrics if col in all_keys]
            secondary_metrics = [col for col in regression_metrics if col in all_keys]
        else:
            priority_metrics = [col for col in regression_metrics if col in all_keys]
            secondary_metrics = [col for col in classification_metrics if col in all_keys]
        
        metric_cols = priority_metrics + secondary_metrics
        other_cols = [col for col in all_keys if col not in base_cols + metric_cols and col != "created_at"]
        
        display_columns = base_cols + metric_cols + other_cols
        
        # Create clean table data
        table_data = []
        for exp in experiments_with_metrics:
            row = {}
            for col in display_columns:
                row[col] = exp.get(col, "-")
            table_data.append(row)
        
        table_display = TableDisplay(console)
        table_display.display_table(
            response_data={"results": table_data},
            columns=display_columns,
            title_prefix="Standard Metrics",
            row_formatter=table_display.format_experiments_row
        )

    # 2. Show experiments with rolling metrics only
    if experiments_with_rolling_only:
        console.print(f"\n[bold yellow]📊 Experiments with Rolling Metrics Only ({len(experiments_with_rolling_only)}):[/bold yellow]")
        
        # Show a simplified view
        for exp in experiments_with_rolling_only:
            rolling_metrics = {k: v for k, v in exp.items() if k.endswith('_avg')}
            console.print(f"• {exp['group_code']} ({exp['model']}) - Rolling metrics: {len(rolling_metrics)} available")

    # 3. Show experiments with errors
    if experiments_with_errors:
        console.print(f"\n[bold red]❌ Experiments with Metric Errors ({len(experiments_with_errors)}):[/bold red]")
        
        for exp in experiments_with_errors:
            console.print(f"• {exp['group_code']} ({exp['model']}, v{exp['data_version']}) - {exp['error']}")

    # Summary view option
    if len(experiments_with_metrics) > 1:
        show_summary = Prompt.ask("\n[bold]📋 Show summary comparison? (y/n)[/bold]", default="y")
        if show_summary.lower() == "y":
            console.print(f"\n[bold cyan]📋 Summary Comparison:[/bold cyan]")
            
            # Create summary table with key metrics only
            all_metric_keys = set()
            for exp in experiments_with_metrics:
                all_metric_keys.update(exp.keys())
            
            # Remove base columns to focus on metrics
            metric_keys = [k for k in all_metric_keys if k not in ["group_code", "model", "data_version", "task_type", "status", "version", "created_at"]]
            summary_cols = ["group_code", "model", "task_type"] + metric_keys[:6]  # Limit to first 6 metrics for readability
            
            summary_data = []
            for exp in experiments_with_metrics:
                row = {}
                for col in summary_cols:
                    row[col] = exp.get(col, "-")
                summary_data.append(row)
            
            table_display = TableDisplay(console)
            table_display.display_table(
                response_data={"results": summary_data},
                columns=summary_cols,
                title_prefix="Summary",
                row_formatter=table_display.format_experiments_row
            )

    # Export option
    if total_found > 3:
        export_choice = Prompt.ask("\n[bold]💾 Export to CSV? (y/n)[/bold]", default="n")
        if export_choice.lower() == "y":
            import csv
            import datetime
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"experiment_metrics_{timestamp}.csv"
            
            # Combine all data for export
            all_data = experiments_with_metrics + experiments_with_rolling_only + experiments_with_errors
            
            if all_data:
                all_columns = set()
                for exp in all_data:
                    all_columns.update(exp.keys())
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=sorted(all_columns))
                    writer.writeheader()
                    writer.writerows(all_data)
                    console.print(f"[green]✅ Exported to {filename}[/green]")

@experiments.command(name='models')
@BaseManager.handle_api_error
def fetch_model_details():
    """Fetch models details by project type and project."""

    experiments_manager = ExperimentsManager()
    experiment_manager = ExperimentManager()
    # table_display = TableDisplay(console)
    base_manager = BaseManager()

    # Ask user for the mode
    mode = Prompt.ask("\n[bold]Choose mode[/bold] (1: By Project ID, 2: By Project Type)", choices=["1", "2"], default="1")

    if mode == "1":
        model = get_models_by_project_id()
    elif mode == "2":
        model = get_models_by_project_type()
    
    if not model:
        return None
    
    model_id = model['id']
    response = experiment_manager.get_model_hyperparameters(model_id)

    if not response:
            console.print("[yellow]No hyperparameters found with model type id-{model_id} existing.[/yellow]")
            return

    hyperparameters = []
    for item in response:
        hyper_def = item.get('hyperparameter_def', {})
        hyperparameters.append({
            key: hyper_def.get(key, 'N/A')
            for key in ['id', 'name', 'description', 'type']
        })
    
    console.print("[bold green]Model Hyperparameters:[/bold green]")
    # Display the project types in a table
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={"results": hyperparameters},
        columns=experiment_manager.model_hyperparameter_columns, 
        title_prefix="Model Hyperparameters",
        row_formatter=table_display.format_experiments_row
    )

@BaseManager.handle_api_error
def get_models_by_project_type():
    """Fetch models details by project type."""

    experiments_manager = ExperimentsManager()
    experiment_manager = ExperimentManager()
    base_manager = BaseManager()

    project_types_response = experiments_manager.list_project_types()
    if not project_types_response:
        console.print("[red]No project types found.[/red]")
        return
    
    project_types_response.sort(key=lambda x: x["id"])

    console.print("[bold]Project Types:[/bold]")
    # Display the project types in a table
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={"results": project_types_response},
        columns=experiments_manager.experiments_project_types_columns,
        title_prefix="Project Types",
        row_formatter=table_display.format_experiments_row
    )
    project_type = get_project_type_search_list()
    if not project_type:
        console.print("[red]Error: Project Type is not selected. Aborting operation.[/red]")

    model_types = project_type['model_types']
    if not model_types:
        console.print("[red]\nNo models associated with this project type.[/red]\n")
        return None
    model_types.sort(key=lambda x: x['id'])
    base_manager.paginate_data(
        data=model_types,
        columns=experiment_manager.all_model_types_columns,
        title_prefix='Model Types List',
        row_formatter=TableDisplay().format_experiments_row,
        page_size=10
    )

    if Prompt.ask("[bold]Do you want to view hyperparameters of a Model?[bold]", choices=["yes","no"], default="yes") == "no":
        return None
    
    model = get_model_search_list(model_types)
    return model

@BaseManager.handle_api_error
def get_models_by_project_id():
    """Fetch models details by project."""

    experiments_manager = ExperimentsManager()
    experiment_manager = ExperimentManager()
    base_manager = BaseManager()

    project = get_project_list()
    if not project:
        console.print("[red]Error: Project is required. Aborting operation.[/red]")
        return None

    project_type = project['project_type_details']
    console.print("\n[bold]Project Type of selected project:[/bold]")
    # Display the project types in a table
    table_display = TableDisplay(console)
    table_display.display_table(
        response_data={"results": [project_type]},
        columns=experiments_manager.experiments_project_types_columns,
        title_prefix="Project Type",
        row_formatter=table_display.format_experiments_row
    )

    model_types = project_type['model_types']
    if not model_types:
        console.print("[red]\nNo models associated with this project type.[/red]\n")
        return None
    model_types.sort(key=lambda x: x['id'])
    base_manager.paginate_data(
        data=model_types,
        columns=experiment_manager.all_model_types_columns,
        title_prefix='Model Types List',
        row_formatter=TableDisplay().format_experiments_row,
        page_size=10
    )

    if Prompt.ask("\n[bold]Do you want to view hyperparameters of a Model?[bold]", choices=["yes","no"], default="yes") == "no":
        console.print("[yellow]Model selection cancelled[yellow]\n")
        return None
    
    model = get_model_search_list(model_types)
    return model

if __name__ == "__main__":
    experiments()