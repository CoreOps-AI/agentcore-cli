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

from functools import wraps
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.text import Text

from agentcore.managers.config import ConfigManager
from agentcore.managers.client import APIClient, APIError
from agentcore.utils.config import CONFIG_FILE, CONFIG_DIR
from agentcore.managers.table_manager import TableDisplay

import sys
import os
from rich.console import Console
from rich.prompt import Prompt
 
console = Console()

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid"""
    pass

class BaseManager:
    _shared_client = None
    SUPPORT_EMAIL = "support-agentcore@coreops.ai"
    
    def __init__(self, config_manager=None, api_client=None):
        """
        Allow dependency injection for easier testing and flexibility.
        Separates configuration and client creation from specific managers.
        """
        self.config_manager = config_manager or ConfigManager()
        
        # FIXED: Use shared client or create one if not exists
        if api_client:
            self.api_client = api_client
        else:
            self.api_client = self._get_or_create_shared_client()
            
        self.console = Console()

    def _get_or_create_shared_client(self):
        """
        Get existing shared client or create a new one if it doesn't exist.
        This ensures the same client instance is used across all API calls.
        """
        if BaseManager._shared_client is None:
            BaseManager._shared_client = self._create_api_client()
        else:
            # Update the existing client with current token (in case it was refreshed)
            current_token = self.config_manager.access_token()
            if current_token:
                BaseManager._shared_client.set_token(current_token)
        
        return BaseManager._shared_client

    @classmethod
    def reset_shared_client(cls):
        """
        Reset the shared client. Useful for testing or when switching contexts.
        """
        cls._shared_client = None

    def _create_api_client(self):
        """
        Centralized method for creating API client with consistent error handling.
        """
        if not CONFIG_DIR.exists() or not CONFIG_FILE.exists():
            raise ConfigurationError("Please use 'agentcore config set-url' to connect to an existing Agentcore service")
        if not self.config_manager.url():
            raise ConfigurationError("API URL not configured. Use 'agentcore config set-url' command")
            
        client = APIClient(
            base_url=self.config_manager.url(), 
            config=self.config_manager,  # FIXED: Pass config to client
            verify_ssl=False
        )
        current_token = self.config_manager.access_token()
        if current_token:
            client.set_token(current_token)
        
        return client
    
    def format_error_message(self,error):
        # Convert JSON string to Python dict if necessary
        if isinstance(error, str):
            try:
                error = json.loads(error)  # Parse JSON string
            except json.JSONDecodeError:
                return error  # Return the original string if it's not a JSON

        if isinstance(error, dict):
            return "\n".join(self.format_dict_message(error))
        elif isinstance(error, list):
            return "\n".join(error)
        return "An unknown error occurred."

    def format_dict_message(self,error_dict, prefix=""):
        formatted_messages = []
        for key, value in error_dict.items():
            if isinstance(value, list):
                for message in value:
                    formatted_messages.append(f"{prefix}{key.capitalize()}: {message}")
            elif isinstance(value, dict):
                formatted_messages.extend(self.format_dict_message(value, prefix=f"{key}."))
            else:
                formatted_messages.append(f"{prefix}{key.capitalize()}: {value}")
        return formatted_messages


    def _execute_with_progress(self, description, operation):
        """
        Centralized progress tracking for API operations.
        Only retries for specific token validation errors.
        Leverages APIClient's built-in token refresh mechanism.
        """
        retries = 1
        max_retries = 3
        success = False
        last_error = None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description=description, total=None)

            while not success and retries <= max_retries:
                try:
                    result = operation()
                    if result is not None:
                        success = True
                        return result
                    # Retry only if result is None
                    wait = retries * 2
                    progress.update(
                        task,
                        # description=f"{description} (Retry {retries}/{max_retries})"
                        description=f"{description}"
                    )
                    time.sleep(wait)
                    retries += 1
                    
                except APIError as e:
                    last_error = e
                    
                    # Only retry for specific 401 token validation error
                    # This handles cases where client's auto-retry might have failed
                    if (e.status_code == 401 and 
                        "Given token not valid for any token type" in str(e.message)):
                        
                        wait = retries * 2
                        progress.update(
                            task,
                            # description=f"{description} (Token refresh retry {retries}/{max_retries} - waiting {wait}s)"
                            description=f"{description}"
                        )
                        time.sleep(wait)
                        retries += 1
                    else:
                        # For all other APIErrors, don't retry - raise immediately
                        raise APIError(message=f"\n{self.format_error_message(e.message)}", status_code=e.status_code)
                        
                except Exception as e:
                    # For non-APIError exceptions, don't retry - raise immediately
                    last_error = e
                    raise APIError(message=f"\n{self.format_error_message(e.message)}", status_code=e.status_code)

            if not success:
                if last_error:
                    # Re-raise the actual error - let handle_api_error decorator handle display
                    raise last_error
                else:
                    self.console.print("\n[red]Operation failed after maximum retry attempts.[/red]")
                    return None


    @staticmethod
    def handle_api_error(func=None, *, show_details=False, custom_messages=None):
        """
        Decorator to handle API errors with clean, user-friendly messages.
        Backwards compatible - works with both old and new usage patterns.
        Every error message includes support email for escalation.

        Args:
            func: The function being decorated (for backwards compatibility)
            show_details (bool): Whether to show technical error details
            custom_messages (dict): Custom messages for specific status codes
        """
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                console = Console()
                default_messages = {
                    400: "Invalid request. Please check your input and try again.",
                    401: "Please login to run the Agentcore.",
                    403: "Access denied. You don't have permission to perform this action.",
                    404: "Resource not found. Please verify the information and try again.",
                    409: "Conflict detected. The resource already exists or is being modified.",
                    422: "Invalid data provided. Please check your input format.",
                    429: "Too many requests. Please wait a moment and try again.",
                    500: "Server error occurred. Please try again later.",
                    502: "Service temporarily unavailable. Please try again later.",
                    503: "Service unavailable. Please try again later.",
                }
                if custom_messages:
                    default_messages.update(custom_messages)

                try:
                    return f(*args, **kwargs)
                except APIError as e:
                    status_code = e.status_code or 500
                    user_message = default_messages.get(
                        status_code,
                        "An unexpected error occurred. Please try again."
                    )
                    # Add Support Email
                    error_text = Text()
                    error_text.append("❌ ", style="red")
                    error_text.append(user_message, style="red")
                    error_text.append("\nIf you need further assistance, please contact: ", style="red")
                    error_text.append(BaseManager.SUPPORT_EMAIL, style="bold blue")
                    console.print(error_text)
                    if show_details:
                        console.print(f"\n[dim]Additional details:[/dim]")
                        console.print(f"[dim]Status Code: {status_code}[/dim]")
                        if hasattr(e, 'message') and e.message:
                            console.print(f"[dim]Details: {e.message}[/dim]")
                        if hasattr(e, 'response') and e.response:
                            console.print(f"[dim]Response: {json.dumps(e.response, indent=2)}[/dim]")

                except Exception as e:
                    error_text = Text()
                    error_text = Text()
                    error_text.append("❌ ", style="red")
                    error_text.append("An unexpected error occurred. Please try again.\n", style="red")
                    error_text.append("If you need further assistance, please contact: ", style="red")
                    error_text.append(f"{BaseManager.SUPPORT_EMAIL}\n", style="bold blue")
                    console.print(error_text)
                    
                    if show_details:
                        console.print(f"\n[dim]Technical details: {str(e)}[/dim]")
                return None
            return wrapper

        # Backwards compatibility (support both @handle_api_error and @handle_api_error(...))
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def masked_input(self, prompt: str) -> str:
        self.console.print(prompt, end="", style="bold")
        password = []
        
        try:
            import readchar
            
            while True:
                char = readchar.readchar()
                
                # Handle Enter key
                if char in ('\r', '\n'):
                    print()
                    break
                
                # Handle Ctrl+C
                elif char == '\x03':
                    print()
                    self.console.print("[red]Cancelled by user.[/red]")
                    sys.exit(0)
                
                # Handle Backspace
                elif char in ('\x08', '\x7f'):
                    if password:
                        password.pop()
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                
                # Handle normal characters
                else:
                    password.append(char)
                    sys.stdout.write('*')
                    sys.stdout.flush()
            
            return ''.join(password)
        
        except ImportError:
            self.console.print("\n[yellow]For better password masking, install readchar: pip install readchar[/yellow]")
            import getpass
            return getpass.getpass(prompt="Password: ")
        
    # Reusable tab-completion input function
    def get_input_with_tab_completion(self,prompt_text: str, options: list[str]) -> str:
        """Prompt user with tab-completion from options."""
        class FullWordCompleter(Completer):
            def __init__(self, words):
                self.words = words

            def get_completions(self, document, complete_event):
                text = document.text_before_cursor.lower()
                for word in self.words:
                    if text in word.lower():
                        yield Completion(word, start_position=-len(text))
        completer = FullWordCompleter(options)
        session = PromptSession()

        print("Type partial name and press Tab for suggestions.")
        return session.prompt(f"{prompt_text} > ", completer=completer)
    
    @staticmethod
    def paginate_data(data, columns, title_prefix, row_formatter, 
                page_size=10, allow_jump=True, 
                custom_actions=None, search_fields=None, 
                allow_selection=False, selection_field='id'):
        """
        Enhanced pagination function with search, filter, and selection features.
        
        Args:
            data (list): List of data items to paginate
            columns (list): Table column headers
            title_prefix (str): Prefix for table title
            row_formatter (callable): Function to format each row
            page_size (int, optional): Number of items per page. Defaults to 10
            allow_jump (bool, optional): Allow jumping to specific page. Defaults to True
            custom_actions (dict, optional): Custom actions {key: (description, callback)}
            search_fields (list, optional): List of field names that can be searched/filtered
            allow_selection (bool, optional): Enable row selection functionality. Defaults to False
            selection_field (str, optional): Field to use for selection identification. Defaults to 'id'
            
        Returns:
            dict or None: Selected item if allow_selection=True and item selected, None otherwise
        """
        if not data:
            console.print(f"[yellow]No {title_prefix.lower()} found.[/yellow]")
            return None

        # Store original data and current filtered data
        original_data = data.copy()
        filtered_data = data.copy()
        current_search_term = ""
        
        table_display = TableDisplay()

        def search_and_filter_data(search_term, data_list):
            """Search and filter data based on search term and specified fields."""
            if not search_term or not search_fields:
                return data_list, None
                
            search_term = search_term.lower().strip()
            matches = []
            exact_match = None
            
            for item in data_list:
                # Check each search field
                for field in search_fields:
                    if field in item:
                        field_value = str(item[field]).lower()
                        
                        # Check for exact match
                        if field_value == search_term:
                            exact_match = item
                            matches.append(item)
                            break
                        # Check for partial match
                        elif search_term in field_value:
                            matches.append(item)
                            break
            
            # Remove duplicates while preserving order
            unique_matches = []
            seen = set()
            for item in matches:
                # Use a combination of fields as identifier
                identifier = tuple(item.get(field, '') for field in search_fields[:2])  # Use first 2 fields as identifier
                if identifier not in seen:
                    seen.add(identifier)
                    unique_matches.append(item)
            
            return unique_matches, exact_match

        def create_search_completer(data_list):
            """Create completer for search functionality."""
            if not search_fields:
                return None
                
            suggestions = set()
            for item in data_list:
                for field in search_fields:
                    if field in item:
                        suggestions.add(str(item[field]))
            
            return WordCompleter(list(suggestions), ignore_case=True)

        def display_search_info():
            """Display current search status."""
            if current_search_term:
                console.print(f"[cyan]Current filter: '{current_search_term}' | Showing {len(filtered_data)} of {len(original_data)} items[/cyan]")
            else:
                console.print(f"[green]Showing all {len(filtered_data)} items[/green]")
            
            if allow_selection:
                console.print(f"[magenta]Selection Mode: ON - You can select items using [r] option[/magenta]")

        def display_selectable_table(page_data, start_index):
            """Display table with row numbers for selection."""
            if not page_data:
                return
                
            # Add row numbers to the display
            enhanced_columns = ['#'] + columns
            enhanced_data = []
            
            for i, item in enumerate(page_data):
                # Call row_formatter with both item and columns parameters
                # since TableDisplay methods expect (item, columns)
                formatted_row = row_formatter(item, columns)
                row_data = [str(start_index + i + 1)] + formatted_row
                enhanced_data.append(row_data)
            
            # Create a temporary response structure for table display
            table_display.display_table(
                response_data={'results': enhanced_data, 'count': len(filtered_data)},
                columns=enhanced_columns,
                title_prefix=title_prefix,
                row_formatter=lambda x, cols: x  # Data is already formatted, just return as-is
            )

        def select_from_current_page(page_data, start_index):
            """Allow user to select a row from current page."""
            if not page_data:
                console.print("[yellow]No items to select from.[/yellow]")
                return None
                
            console.print(f"\n[bold]Select an item from current page (1-{len(page_data)}):[/bold]")
            
            try:
                selection = input("Enter row number or press Enter to cancel: ").strip()
                if not selection:
                    return None
                    
                row_num = int(selection)
                if 1 <= row_num <= len(page_data):
                    selected_item = page_data[row_num - 1]
                    console.print(f"\n[green]Selected:[/green] {selected_item.get(selection_field, 'N/A')} - {selected_item.get('name', str(selected_item))}")
                    
                    # Confirm selection
                    confirm = Prompt.ask(
                        "\n[bold]Confirm selection?[/bold]",
                        choices=['y', 'n', 'yes', 'no'],
                        default='y'
                    ).lower()
                    
                    if confirm in ['y', 'yes']:
                        return selected_item
                    else:
                        console.print("[yellow]Selection cancelled.[/yellow]")
                        return None
                else:
                    console.print(f"[red]Invalid row number. Please enter 1-{len(page_data)}[/red]")
                    return None
                    
            except ValueError:
                console.print("[red]Invalid input. Please enter a valid number[/red]")
                return None

        current_page = 0

        while True:
            # Calculate pagination for current filtered data
            total_pages = (len(filtered_data) + page_size - 1) // page_size if filtered_data else 1
            
            # Ensure current page is valid
            if current_page >= total_pages:
                current_page = max(0, total_pages - 1)
                
            start_index = current_page * page_size
            end_index = start_index + page_size
            page_data = filtered_data[start_index:end_index] if filtered_data else []

            # Clear screen and display header with colors
            console.print(f"\n[blue]{'='*80}[/blue]")
            console.print(f"[bold cyan]Page {current_page + 1} of {total_pages}[/bold cyan] | [yellow]Page Size: {page_size}[/yellow]")
            display_search_info()
            console.print(f"[blue]{'='*80}[/blue]\n")

            # Display the table for current page
            if page_data:
                if allow_selection:
                    display_selectable_table(page_data, start_index)
                else:
                    table_display.display_table(
                        response_data={'results': page_data, 'count': len(filtered_data)},
                        columns=columns,
                        title_prefix=title_prefix,
                        row_formatter=lambda item, cols: row_formatter(item, cols)
                    )
            else:
                console.print(f"[yellow]No {title_prefix.lower()} found matching current criteria.[/yellow]")

            # Build navigation options
            navigation_options = []
            if len(filtered_data) > 0 and current_page < total_pages - 1:
                navigation_options.append("\\[n] Next")
            if current_page > 0:
                navigation_options.append("\\[p] Previous")
            if allow_jump and total_pages > 1:
                navigation_options.append("\\[j] Jump to page")
            
            # Search/Filter options
            if search_fields:
                navigation_options.append("\\[s] Search/Filter")
                if current_search_term:
                    navigation_options.append("\\[c] Clear filter")
            
            # Selection option
            if allow_selection and page_data:
                navigation_options.append("\\[r] Select Item")
            
            if custom_actions:
                for key, (description, _) in custom_actions.items():
                    navigation_options.append(f"[{key}] {description}")
            navigation_options.append("\\[q] Quit")
            
            console.print(f"\n[bright_white]{' | '.join(navigation_options)}[/bright_white]")
            choice = input("Enter your choice: ").strip().lower()

            if choice == 'n' and len(filtered_data) > 0 and current_page < total_pages - 1:
                current_page += 1
            elif choice == 'p' and current_page > 0:
                current_page -= 1
            elif choice == 'j' and allow_jump and total_pages > 1:
                try:
                    page_num = int(input(f"Enter page number (1-{total_pages}): "))
                    if 1 <= page_num <= total_pages:
                        current_page = page_num - 1
                    else:
                        console.print(f"[red]Invalid page number. Please enter 1-{total_pages}[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter a valid number[/red]")
            elif choice == 's' and search_fields:
                # Search/Filter functionality
                console.print(f"\n[bold]Search/Filter {title_prefix}:[/bold]")
                console.print(f"[dim]Searchable fields: {', '.join(search_fields)}[/dim]")
                console.print("[dim]Tip: Type part of any field value and press Tab for suggestions[/dim]")
                
                # Create completer for current data
                search_completer = create_search_completer(original_data)
                
                try:
                    search_input = prompt(
                        "Enter search term: ",
                        completer=search_completer,
                        complete_while_typing=True
                    ) if search_completer else input("Enter search term: ")
                    
                    if search_input.strip():
                        # Perform search
                        new_filtered_data, exact_match = search_and_filter_data(search_input, original_data)
                        
                        if exact_match:
                            console.print(f"[green]Found exact match![/green]")
                            filtered_data = new_filtered_data
                            current_search_term = search_input.strip()
                            current_page = 0
                        elif new_filtered_data:
                            console.print(f"[green]Found {len(new_filtered_data)} matching items[/green]")
                            filtered_data = new_filtered_data
                            current_search_term = search_input.strip()
                            current_page = 0
                        else:
                            console.print("[yellow]No matches found. Keeping current view.[/yellow]")
                            input("Press Enter to continue...")
                    else:
                        console.print("[yellow]Empty search term. Keeping current view.[/yellow]")
                        input("Press Enter to continue...")
                        
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[yellow]Search cancelled.[/yellow]")
                    
            elif choice == 'c' and current_search_term:
                # Clear filter
                filtered_data = original_data.copy()
                current_search_term = ""
                current_page = 0
                console.print("[green]Filter cleared. Showing all items.[/green]")
                
            elif choice == 'r' and allow_selection and page_data:
                # Row selection
                selected_item = select_from_current_page(page_data, start_index)
                if selected_item:
                    table_display.display_table(
                        response_data={'results': [selected_item]},
                        columns=columns,
                        title_prefix="Selected Item",
                        row_formatter=lambda item, cols: row_formatter(item, cols)
                    )
                    return selected_item
                # If no selection made, continue pagination
                
            elif choice == 'q':
                break
            elif custom_actions and choice in custom_actions:
                # Execute custom action
                callback = custom_actions[choice][1]
                result = callback(page_data, current_page)
                # If callback returns True, continue pagination; if False, exit
                if result is False:
                    break
            else:
                # Handle invalid choices with helpful messages
                if choice == 'n' and (len(filtered_data) == 0 or current_page >= total_pages - 1):
                    console.print("[yellow]Already on last page or no data to display[/yellow]")
                elif choice == 'p' and current_page <= 0:
                    console.print("[yellow]Already on first page[/yellow]")
                elif choice == 's' and not search_fields:
                    console.print("[yellow]Search functionality not available for this data[/yellow]")
                elif choice == 'c' and not current_search_term:
                    console.print("[yellow]No active filter to clear[/yellow]")
                elif choice == 'r' and not allow_selection:
                    console.print("[yellow]Row selection not enabled for this view[/yellow]")
                elif choice == 'r' and not page_data:
                    console.print("[yellow]No items available for selection[/yellow]")
                else:
                    console.print("[red]Invalid choice. Please enter a valid option[/red]")
                
                input("Press Enter to continue...")
        
        # Return None if no selection was made and allow_selection is True
        return None
    
    def demo_user_check(func):
        """Decorator to check if user is demo user and prevent access to certain features."""

        from agentcore.managers.users_manager import UserManager

        @wraps(func)
        def wrapper(*args, **kwargs):
            user = UserManager()
            if user.is_demo_user():
                console.print("[red]This feature is not available in the trial version[/red]\n")
                return None
            return func(*args, **kwargs)
        return wrapper
    
    def clear_auth_details(func):
        """Decorator to clear all authentication details (used for logout)."""

        from agentcore.managers.config import ConfigManager
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = ConfigManager()
            config.clear_details()
            return func(*args, **kwargs)
        
        return wrapper
