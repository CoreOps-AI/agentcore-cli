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

import json
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.syntax import Syntax
from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers import PythonLexer

from agentcore.cli.data.main import data

console = Console()

def get_code_input(data_type="Tabular", operation_type=""):
    """Enhanced code input with proper editing capabilities"""
    console.print(f"\n[bold]💻 Implementation Code for {data_type} Data[/bold]")
    
    # Show template example
    template_example = get_template_example(data_type)
    console.print("\n[bold]📋 Template Structure:[/bold]")
    console.print(Syntax(template_example, "python", theme="monokai"))
    
    console.print("\n[bold yellow]Enter your operation logic:[/bold yellow]")
    console.print("[dim]Tip: Use arrow keys to navigate, Ctrl+C to cancel, Alt+Enter or Ctrl+D to finish[/dim]\n")
    
    # Style for the prompt
    style = Style.from_dict({
        'prompt': '#ansigreen bold',
    })
    
    try:
        # Multi-line prompt with Python syntax highlighting
        user_code = prompt(
            ">>> ",
            lexer=PygmentsLexer(PythonLexer),
            style=style,
            multiline=True,
            prompt_continuation="... ",
            complete_style='column',
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Code input cancelled.[/yellow]")
        return None
    except EOFError:
        console.print("\n[yellow]Code input cancelled.[/yellow]")
        return None
    
    user_code = user_code.strip()
    
    if not user_code:
        console.print("[yellow]No code entered. Using placeholder.[/yellow]")
        user_code = "# Add your operation logic here"
    
    # Generate final code with template
    final_code = generate_final_code(user_code, data_type)
    
    console.print("\n[green]✅ Code added successfully![/green]")
    return final_code

def get_template_example(data_type):
    """Get template example for the data type"""
    if data_type == "Tabular":
        return '''# Template structure (auto-generated parts):
# 1. Validation: Check data_container.data_type == 'Tabular'
# 2. Setup: df = data_container.as_dataframe()
# 3. YOUR CODE HERE (what you need to write)
# 4. Cleanup: data_container.primary_data = df; return data_container

# Example of what YOU write:
df = df.dropna()  # Remove missing values
df['new_col'] = df['old_col'] * 2  # Transform data
df = df[df['column'] > 0]  # Filter data'''
    
    elif data_type == "Text":
        return '''# Template structure (auto-generated parts):
# 1. Validation: Check data_container.data_type == 'Text'  
# 2. Setup: import re
# 3. YOUR CODE HERE (what you need to write)
# 4. Cleanup: return data_container

# Example of what YOU write:
if isinstance(data_container.primary_data, str):
    data_container.primary_data = data_container.primary_data.upper()
elif isinstance(data_container.primary_data, list):
    data_container.primary_data = [text.upper() for text in data_container.primary_data]'''
    
    else:  # Image
        return '''# Template structure (auto-generated parts):
# 1. Validation: Check data_container.data_type == 'Image'
# 2. YOUR CODE HERE (what you need to write)  
# 3. Cleanup: return data_container

# Example of what YOU write:
# Add your image processing logic here
# Apply filters, resize, convert formats, etc.'''

def generate_final_code(user_code, data_type):
    """Generate the complete code with user's logic embedded"""
    if data_type == "Tabular":
        return f'''# Validation and setup (auto-generated - do not edit)
if data_container.data_type != 'Tabular':
    raise ValueError("Operation requires Tabular data")

df = data_container.as_dataframe()
if df is None:
    raise ValueError("Failed to get DataFrame from container")

# ═══════════════════════════════════════════════════════════
# USER OPERATION LOGIC
# ═══════════════════════════════════════════════════════════

{user_code}

# ═══════════════════════════════════════════════════════════
# Cleanup and return (auto-generated - do not edit)
# ═══════════════════════════════════════════════════════════

# Update the container with the modified DataFrame
data_container.primary_data = df

# Return the updated container
result = data_container'''
    
    elif data_type == "Text":
        return f'''# Validation and setup (auto-generated - do not edit)
if data_container.data_type != 'Text':
    raise ValueError("Operation requires Text data")

import re

# ═══════════════════════════════════════════════════════════
# USER OPERATION LOGIC
# ═══════════════════════════════════════════════════════════

{user_code}

# ═══════════════════════════════════════════════════════════
# Cleanup and return (auto-generated - do not edit)
# ═══════════════════════════════════════════════════════════

# Return the updated container
result = data_container'''
    
    else:  # Image
        return f'''# Validation and setup (auto-generated - do not edit)
if data_container.data_type != 'Image':
    raise ValueError("Operation requires Image data")

# ═══════════════════════════════════════════════════════════
# USER OPERATION LOGIC
# ═══════════════════════════════════════════════════════════

{user_code}

# ═══════════════════════════════════════════════════════════
# Cleanup and return (auto-generated - do not edit)
# ═══════════════════════════════════════════════════════════

# Return the updated container
result = data_container'''

def operations_create():
    """Create a data processing operation"""
    
    console.print("\n[bold blue]🚀 Create Data Processing Operation[/bold blue]\n")
    
    # Basic Information
    console.print("[bold]📝 Basic Information[/bold]")
    name = Prompt.ask("[bold]Enter Operation Name[/bold]")
    if not name:
        console.print("[red]Error: Operation Name is required. Aborting the operation.[/red]")
        return

    description = Prompt.ask("[bold]Enter Operation Description[/bold]")
    if not description:
        console.print("[red]Error: Operation Description is required. Aborting the operation.[/red]")
        return

    # Configuration
    console.print("\n[bold]⚙️ Configuration[/bold]")
    stage = Prompt.ask(
        "[bold]Enter Stage[/bold]", 
        choices=["RAW", "PROCESSED", "ANALYZED"], 
        default="RAW"
    )

    operation_type = Prompt.ask("[bold]Enter Operation Type[/bold]")
    if not operation_type:
        console.print("[red]Error: Operation Type is required. Aborting the operation.[/red]")
        return

    data_type_name = Prompt.ask(
        "[bold]Enter Data Type[/bold]", 
        choices=["Tabular", "Text", "Image"],
        default="Tabular"
    )

    # Source Types
    console.print("\n[bold]📊 Source Types[/bold]")
    console.print("Available source types: DATABASE, FILES, API")
    source_types_input = Prompt.ask(
        "[bold]Enter Source Types (comma-separated)[/bold]", 
        default="DATABASE,FILES,API"
    )
    source_types = [s.strip().upper() for s in source_types_input.split(',')]
    
    # Validate source types
    valid_source_types = ["DATABASE", "FILES", "API"]
    source_types = [st for st in source_types if st in valid_source_types]
    if not source_types:
        console.print("[red]Error: At least one valid source type is required.[/red]")
        return

    # Required Parameters
    console.print("\n[bold]📋 Required Parameters[/bold]")
    console.print("Enter required parameter names (comma-separated, leave empty if none):")
    console.print("Example: columns, value, rename_dict")
    required_params_input = Prompt.ask("[bold]Required Parameters[/bold]", default="")
    required_parameters = [p.strip() for p in required_params_input.split(',') if p.strip()]

    # Default Parameters
    console.print("\n[bold]📋 Default Parameters[/bold]")
    console.print("Enter default parameters as JSON (leave empty for {}):")
    console.print('Example: {"columns": null, "method": "mean"}')
    default_params_input = Prompt.ask("[bold]Default Parameters[/bold]", default="{}")
    
    try:
        default_parameters = json.loads(default_params_input) if default_params_input else {}
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON format for default parameters.[/red]")
        return

    # Implementation Code
    implementation_code = get_code_input(data_type_name, operation_type)
    
    if implementation_code is None:
        console.print("[yellow]Code input cancelled. Operation creation aborted.[/yellow]")
        return

    # Build payload
    payload = {
        "name": name,
        "stage": stage,
        "operation_type": operation_type,
        "description": description,
        "required_parameters": required_parameters,
        "default_parameters": default_parameters,
        "data_type_name": data_type_name,
        "source_types": source_types,
        "implementation_code": implementation_code
    }

    # Display summary
    console.print("\n[bold]📋 Operation Summary:[/bold]")
    
    # Create a nice table for the summary
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    for key, value in payload.items():
        if key == "implementation_code":
            # Show first few lines of code
            code_lines = str(value).split('\n')[:3]
            display_value = f"{' '.join(line.strip() for line in code_lines)}... ({len(str(value).split())} total lines)"
        elif isinstance(value, list):
            display_value = ', '.join(map(str, value))
        else:
            display_value = str(value)
        
        table.add_row(key, display_value)
    
    console.print(table)

    # Confirmation
    if Prompt.ask("\n[bold]Create Operation?[/bold]", choices=["yes", "no"], default="yes") == "no":
        console.print("[yellow]Operation creation cancelled.[/yellow]")
        return None

    # Create operation
    console.print("\n[bold blue]Creating operation...[/bold blue]")
    
    try:
        
        
        # For demo purposes:
        console.print(f"[bold green]✅ Operation '{payload['name']}' created successfully![/bold green]")
        
        # Display created operation details
        console.print("\n[bold]📊 Created Operation Details:[/bold]")
        created_table = Table(show_header=True, header_style="bold green")
        created_table.add_column("Field", style="cyan")
        created_table.add_column("Value", style="white")
        
        # Simulate API response
        response = {
            "id": 123,
            "name": payload["name"],
            "operation_type": payload["operation_type"],
            "stage": payload["stage"],
            "data_type_name": payload["data_type_name"],
            "created_at": "2025-07-08T04:34:45Z"
        }
        
        for key, value in response.items():
            created_table.add_row(key, str(value))
        
        console.print(created_table)
        
    except Exception as e:
        console.print(f"[red]❌ Error creating operation: {str(e)}[/red]")
        return None

# Quick templates function
def show_operation_templates():
    """Show common operation templates"""
    console.print("\n[bold]📝 Common Operation Templates[/bold]\n")
    
    templates = {
        "1": {
            "name": "Drop Columns",
            "type": "DROP",
            "data_type": "Tabular",
            "code": "columns = parameters.get('columns', [])\nexisting_columns = [col for col in columns if col in df.columns]\nif existing_columns:\n    df = df.drop(columns=existing_columns)"
        },
        "2": {
            "name": "Fill Missing Values",
            "type": "FILL_NA", 
            "data_type": "Tabular",
            "code": "value = parameters.get('value')\ndf = df.fillna(value)"
        },
        "3": {
            "name": "Normalize Text",
            "type": "NORMALIZE",
            "data_type": "Text", 
            "code": "if isinstance(data_container.primary_data, str):\n    data_container.primary_data = data_container.primary_data.lower().strip()"
        }
    }
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=5)
    table.add_column("Name", style="white", width=20)
    table.add_column("Type", style="yellow", width=15)
    table.add_column("Data Type", style="green", width=15)
    
    for template_id, template in templates.items():
        table.add_row(template_id, template["name"], template["type"], template["data_type"])
    
    console.print(table)
    
    template_choice = Prompt.ask("\n[bold]Select template ID (or press Enter to skip)[/bold]", default="")
    
    if template_choice in templates:
        return templates[template_choice]
    return None

# CLI command integration
@data.command(name='operations')
def create():
    """Create a data processing operation with enhanced UI"""
    operations_create()