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

from rich.table import Table
from rich.console import Console
class TableDisplay:
    def __init__(self, console=None):
        """
        Initialize TableDisplay with optional console.
        
        Args:
            console (Console, optional): Rich console for output. Defaults to new Console.
        """
        self.console = console or Console()
        self.special_mappings = {
            'Password': 'generated_password',
            'Active Status': 'is_active'
            # Add other special mappings as needed
        }

    @staticmethod
    def get_safe(item, key, default='-'):
        """
        Safely retrieve a value from a dictionary.
        
        Args:
            item (dict): Dictionary to retrieve value from
            key (str or callable): Key or function to extract value
            default (str, optional): Default value if key not found
        
        Returns:
            str: Safely retrieved value
        """
        return str(item.get(key, default)) if isinstance(key, str) else str(key(item))
    
    def get_column_key(self, column):
        """
        Get the correct data key for a column name.
        Handles special cases and normal column names.
        """
        # Check if this column has a special mapping
        if column in self.special_mappings:
            return self.special_mappings[column]
        # Default behavior: convert to lowercase and replace spaces
        return column.lower().replace(' ', '_')

    def format_generic_row(self, item, mapping):
        """
        Generate a formatted row for table display.
        
        Args:
            item (dict): Data item to format
            mapping (list): Column mapping or extraction functions
        
        Returns:
            list: Formatted row values
        """
        return [self.get_safe(item, key) for key in mapping]

    def format_project_row(self, project, columns):
        """
        Format a project-specific row with custom logic.
        
        Args:
            project (dict): Project data
            columns (list): Column definitions
        
        Returns:
            list: Formatted project row
        """
        row_data = []
        for column in columns:
            if column == 'Deployed':
                row_data.append("✓" if project.get('deployed', False) else "✗")
            elif column == 'Users':
                row_data.append(", ".join([user['username'] for user in project.get('users', [])]) or '-')
            elif column == 'Metrics Name':
                row_data.append(project.get('metric_name') if project.get('metric_name') else '-')
            else:
                key = self.get_column_key(column)
                row_data.append(self.get_safe(project, key))
        return row_data
    
    def format_user_row(self, user, columns):
        """
        Format a user-specific row with custom logic.
        
        Args:
            user (dict): User data
            columns (list): Column definitions
        
        Returns:
            list: Formatted user row
        """
        row_data = []
        for column in columns:
            if column == 'Active Status':
                row_data.append("✓" if user.get('is_active', False) else "✗")
            else:
                key = self.get_column_key(column)
                row_data.append(self.get_safe(user, key))
        return row_data

    def format_instance_row(self, instance, columns):
        """
        Format an instance-specific row with custom logic.

        Args:
            instance (dict): Instance data.
            columns (list): Column definitions.

        Returns:
            list: Formatted instance row.
        """
        row_data = []
        for column in columns:
            key = self.get_column_key(column)
            row_data.append(self.get_safe(instance, key))
        return row_data
    
    def format_dataversion_row(self, dataversion, columns):
        """data version columns format"""
        row_data = []
        for column in columns:
            key = self.get_column_key(column)
            row_data.append(self.get_safe(dataversion, key))
        return row_data
    
    def format_datasource_row(self, datasource, columns):
        """data source columns format"""
        row_data = []
        for column in columns:
            key = self.get_column_key(column)
            row_data.append(self.get_safe(datasource, key))
        return row_data

    def format_experiments_row(self, experiment_response, columns):
        """Format experiment run response into a row for table display"""
        row_data = []
        for column in columns:
            key = self.get_column_key(column)  # usually converts "Instance ID" to "instance_id"
            row_data.append(self.get_safe(experiment_response, key))
        return row_data


    def display_table(self, response_data, columns, title_prefix='Items', 
                      row_formatter=None, row_mapping=None):
        """
        Display a table from API response data.
        
        Args:
            response_data (dict): API response containing results
            columns (list): Table column headers
            title_prefix (str, optional): Prefix for table title
            row_formatter (callable, optional): Custom row formatting function
            row_mapping (list, optional): Mapping for row formatting
        """
        # Handle response data structure gracefully
        results = response_data.get('results', [])
        
        if not results:
            self.console.print(f"[yellow]No {title_prefix.lower()} found.[/yellow]\n")
            return

        table = Table(
            title=f"{title_prefix} (Total: {response_data.get('count', len(results))})",
            title_style="bold magenta",
            border_style="blue",
            header_style="bold cyan",
            show_lines=True
        )
        
        # Add columns to the table
        for column in columns:
            table.add_column(column)

        # Dynamically map columns to keys
        formatter = row_formatter or self.format_generic_row
        
        for item in results:
            table.add_row(*formatter(item, columns))

        self.console.print(table)

        # Pagination info
        if any(key in response_data for key in ['next', 'previous']):
            pagination_info = f"""
    [cyan]Total Items:[/cyan] {response_data.get('count', len(results))} 
    [cyan]Previous:[/cyan] {'Yes' if response_data.get('previous') else 'No'} 
    [cyan]Next:[/cyan] {'Yes' if response_data.get('next') else 'No'}
    """
            self.console.print(pagination_info)

    # def display_table(self, response_data, columns, title_prefix='Items',row_formatter=None, row_mapping=None,search_fields=None, allow_selection=False,selection_field='id', page_size=10):
        

    #     """
    #     Display a paginated table from API response data.

    #     Args:
    #         response_data (dict): API response containing results
    #         columns (list): Table column headers
    #         title_prefix (str, optional): Prefix for table title
    #         row_formatter (callable, optional): Custom row formatting function
    #         row_mapping (list, optional): Mapping for row formatting
    #         search_fields (list, optional): Fields to allow filtering
    #         allow_selection (bool, optional): Whether to allow item selection
    #         selection_field (str, optional): Field used for selection return
    #         page_size (int, optional): Number of items per page
    #     """
    # results = response_data.get('results', [])

    # if not results:
    #     self.console.print(f"[yellow]No {title_prefix.lower()} found.[/yellow]")
    #     return

    # # Use BaseManager for pagination
    # #from agentcore.managers.base_manager import BaseManager  # Adjust import if needed
    # base_manager = BaseManager()

    # selected_item = base_manager.paginate_data(
    #     data=results,
    #     columns=columns,
    #     title_prefix=title_prefix,
    #     row_formatter=row_formatter or self.format_generic_row,
    #     search_fields=search_fields,
    #     allow_selection=allow_selection,
    #     selection_field=selection_field,
    #     page_size=page_size
    # )

    # # If selection is enabled, return the selected item
    # if allow_selection:
    #     return selected_item
    



    def format_dataversion_processed_row(self, item, index):
        """Format a data version processed row for display."""
        return[
            str(item.get('id', 'N/A')),
            str(item.get('data_version', 'N/A')), 
            str(item.get('tablename', 'N/A')),
            str(item.get('operation', 'N/A')),
            item.get('created_by', 'N/A'),
            item.get('updated_by', 'N/A'),
            item.get('created_at', 'N/A'),
            item.get('updated_at', 'N/A')
        ]