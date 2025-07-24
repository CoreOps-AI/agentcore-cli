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

from agentcore.managers.instance_manager import InstanceManager
from agentcore.managers.table_manager import TableDisplay
from agentcore.managers.base import BaseManager
from agentcore.cli.experiments.helpers import get_project_list
import cv2
import numpy as np

install()

console = Console()


def displayItemsForSelection(items, title="Select Item", messageType="item"):
    """
    Display a list of items in a paginated window for selection.
    
    Args:
        items (list): List of items to display
        title (str): Title to display at the top of the window
        messageType (str): Type of items being displayed (e.g., "region", "instance", etc.)
    
    Returns:
        The selected item or None if no selection was made
    """
    try:
        if not items:
            console.print(f"[bold red]No {messageType}s found to display[/bold red]")
            return None
            
        # Window setup
        window_name = f"{title}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        bg_color = (255, 255, 255)  # White background
        text_color = (0, 0, 0)      # Black text
        highlight_color = (0, 0, 255)  # Red for instructions
        nav_color = (0, 120, 0)     # Green for navigation info
        thickness = 1
        
        # Window dimensions
        window_width = 600
        window_height = 650
        
        # Pagination settings
        items_per_page = 30
        items_per_column = 15
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        current_page = 1
        
        # Function to draw a page
        def draw_page(page_num):
            array_created = np.full((window_height, window_width, 3), bg_color, dtype=np.uint8)
            
            # Add header
            cv2.putText(array_created, f"{title}", (50, 40), 
                       font, 0.7, text_color, 2, cv2.LINE_AA)
            
            # Calculate start and end indices for this page
            start_idx = (page_num - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(items))
            page_items = items[start_idx:end_idx]
            
            # Display page navigation info
            nav_text = f"Page {page_num}/{total_pages} | Items {start_idx+1}-{end_idx} of {len(items)}"
            cv2.putText(array_created, nav_text, (50, 70), 
                       font, 0.5, nav_color, thickness, cv2.LINE_AA)
            
            # Add navigation buttons text
            if total_pages > 1:
                prev_text = "< Previous (P key)" if page_num > 1 else ""
                next_text = "Next (N key) >" if page_num < total_pages else ""
                
                cv2.putText(array_created, prev_text, (50, 90), 
                           font, 0.5, nav_color, thickness, cv2.LINE_AA)
                
                # Calculate position for next button text (right-aligned)
                next_text_size = cv2.getTextSize(next_text, font, 0.5, thickness)[0]
                next_text_x = window_width - 50 - next_text_size[0]
                cv2.putText(array_created, next_text, (next_text_x, 90), 
                           font, 0.5, nav_color, thickness, cv2.LINE_AA)
            
            # Display items in two columns
            start_y = 110  # Adjusted to account for navigation text
            col_width = (window_width - 300) // 1  # Use your specified column width
            
            for i, item in enumerate(page_items):
                # Calculate item index in the overall list
                item_idx = start_idx + i + 1
                
                # Determine column and row
                col_idx = i // items_per_column
                row_idx = i % items_per_column
                
                x_pos = 50 + col_idx * col_width
                y_pos = start_y + row_idx * 25
                
                text = f"{item_idx}: {item}"
                cv2.putText(array_created, text, (x_pos, y_pos), 
                           font, 0.5, text_color, thickness, cv2.LINE_AA)
            
            # Draw instruction box
            instruction_box_top = window_height - 170
            instruction_box_bottom = window_height - 20
            
            cv2.rectangle(array_created, (40, instruction_box_top), 
                         (window_width - 40, instruction_box_bottom), 
                         (240, 240, 255), -1)  # Light blue background
            cv2.rectangle(array_created, (40, instruction_box_top), 
                         (window_width - 40, instruction_box_bottom), 
                         (200, 200, 220), 1)  # Border
            
            # Add instruction text
            instruction_text_y = instruction_box_top + 20
            line_spacing = 25
            
            cv2.putText(array_created, "Instructions:", (50, instruction_text_y), 
                       font, 0.6, highlight_color, thickness, cv2.LINE_AA)
            cv2.putText(array_created, "1. Type the index number of your desired " + messageType, 
                       (70, instruction_text_y + line_spacing), font, 0.5, text_color, thickness, cv2.LINE_AA)
            cv2.putText(array_created, "2. Press ENTER to confirm selection", 
                       (70, instruction_text_y + line_spacing * 2), font, 0.5, text_color, thickness, cv2.LINE_AA)
            # cv2.putText(array_created, "3. Press ESC to cancel, BACKSPACE to correct", 
            #            (70, instruction_text_y + line_spacing * 3), font, 0.5, text_color, thickness, cv2.LINE_AA)
            
            # if total_pages > 1:
            #     cv2.putText(array_created, "3. Press 'N' for next page, 'P' for previous page", 
            #                (70, instruction_text_y + line_spacing * 4), font, 0.5, text_color, thickness, cv2.LINE_AA)
            
            # Input box
            input_box_y = instruction_box_bottom - 25
            # Draw the text first
            cv2.putText(array_created, "Your selection:", (70, input_box_y - 5),
                        font, 0.5, text_color, thickness, cv2.LINE_AA)
            # Draw the rectangle with more space to the right of the text
            cv2.rectangle(array_created, (200, input_box_y - 20), (285, input_box_y), (240, 240, 240), -1)
            
            return array_created
        
        # Initial display
        array_created = draw_page(current_page)
        cv2.imshow(window_name, array_created)
        cv2.moveWindow(window_name, 650, 0)  # Position window on screen
        
        # Handle user input
        keyStrokes = []
        while True:
            # Show current input
            input_display = np.copy(array_created)
            input_box_y = window_height - 45
            cv2.rectangle(input_display, (200, input_box_y - 20), (285, input_box_y), (240, 240, 240), -1)
            cv2.putText(input_display, f"{''.join(keyStrokes)}", 
                       (200, input_box_y - 5), font, 0.5, text_color, thickness, cv2.LINE_AA)
            cv2.imshow(window_name, input_display)
            
            key = cv2.waitKey(0)
            
            # Use N and P keys for navigation
            if key == ord('n') or key == ord('N'):  # Next page
                if current_page < total_pages:
                    current_page += 1
                    array_created = draw_page(current_page)
                    # Clear any keystrokes when changing pages
                    keyStrokes = []
                    
            elif key == ord('p') or key == ord('P'):  # Previous page
                if current_page > 1:
                    current_page -= 1
                    array_created = draw_page(current_page)
                    # Clear any keystrokes when changing pages
                    keyStrokes = []
                    
            # ESC to cancel
            elif key == 27:  # ESC key
                console.print("[yellow]Selection cancelled by user[/yellow]")
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                return None
                
            # Enter to confirm
            elif key == 10 or key == 13:  # Enter key
                break
                
            # Backspace to delete last character
            elif key in [8, 127] and keyStrokes:  # Backspace (Windows=8, Linux/macOS=127)
                keyStrokes.pop()
                
            # Only accept digits
            elif 48 <= key <= 57:  # Numbers 0-9
                keyStrokes.append(chr(key))

        # Process selection
        selectedItem = None
        try:
            if keyStrokes:
                keyStrokesStr = ''.join(keyStrokes)
                selectedIdx = int(keyStrokesStr)
                
                if 1 <= selectedIdx <= len(items):
                    selectedItem = items[selectedIdx - 1]
                    # console.print(f"[green]Selected {messageType}: {selectedItem}[/green]")
                else:
                    console.print(f"[bold red]Error: Index {selectedIdx} out of range (1-{len(items)})[/bold red]")
            else:
                console.print("[yellow]No selection made[/yellow]")
                
        except Exception as e:
            console.print(f"[bold red]Invalid input: {''.join(keyStrokes)}, error: {e}[/bold red]")

        # Clean up
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Ensure windows close properly
        
        return selectedItem
        
    except Exception as e:
        console.print(f"[bold red]Error displaying selection window: {e}[/bold red]")
        return None