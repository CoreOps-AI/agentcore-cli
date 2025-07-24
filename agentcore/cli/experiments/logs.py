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

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Set
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

console = Console()

class LogMonitor:
    def __init__(self, experiment_manager, project_id: int, experiment_group_code: str, version: str = "1.0"):
        self.experiment_manager = experiment_manager
        self.project_id = project_id
        self.experiment_group_code = experiment_group_code
        self.version = version
        self.displayed_logs: Set[str] = set()
        self.all_logs: List[Dict[str, Any]] = []
        self.last_poll_time = None
        self.poll_interval = 2  # seconds
        self.max_display_logs = 50  # Maximum logs to display in the table
        
    def create_log_table(self) -> Table:
        """Create a formatted table for displaying logs."""
        table = Table(
            title=f"Live Logs - Project {self.project_id} | Group {self.experiment_group_code} | Version {self.version}",
            show_header=True,
            header_style="bold blue"
        )
        
        table.add_column("Time", style="dim", width=12)
        table.add_column("Level", width=8)
        table.add_column("Source", style="cyan", width=20)
        table.add_column("Message", style="white", min_width=40)
        
        # Display recent logs (limit to prevent overwhelming the display)
        recent_logs = self.all_logs[-self.max_display_logs:] if len(self.all_logs) > self.max_display_logs else self.all_logs
        
        for log in recent_logs:
            # Format timestamp
            timestamp = log.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8]  # fallback
            else:
                time_str = "N/A"
            
            # Color code log levels
            level = log.get('level', '').upper()
            if level == 'ERROR':
                level_style = "bold red"
            elif level == 'WARNING' or level == 'WARN':
                level_style = "bold yellow"
            elif level == 'INFO':
                level_style = "bold green"
            elif level == 'DEBUG':
                level_style = "dim"
            else:
                level_style = "white"
            
            # Truncate long messages
            message = log.get('message', '')
            if len(message) > 80:
                message = message[:77] + "..."
            
            table.add_row(
                time_str,
                Text(level, style=level_style),
                log.get('source', 'Unknown'),
                message
            )
        
        return table
    
    def create_status_panel(self) -> Panel:
        """Create a status panel showing monitoring information."""
        now = datetime.now()
        status_text = f"🔄 Monitoring active | Last updated: {now.strftime('%H:%M:%S')}\n"
        status_text += f"📊 Total logs: {len(self.all_logs)} | "
        status_text += f"🕐 Poll interval: {self.poll_interval}s\n"
        status_text += f"📁 Project: {self.project_id} | Group: {self.experiment_group_code} | Version: {self.version}\n"
        status_text += "Press Ctrl+C to stop monitoring"
        
        return Panel(
            status_text,
            title="Log Monitor Status",
            style="blue"
        )
    
    def fetch_new_logs(self) -> List[Dict[str, Any]]:
        """Fetch new logs from the API."""
        try:
            response = self.experiment_manager.fetch_logs(
                self.project_id, 
                self.experiment_group_code, 
                self.version
            )
            
            if response and 'logs' in response:
                logs = response['logs']
                
                # Filter for new logs only
                new_logs = []
                for log in logs:
                    # Create a unique identifier for each log
                    log_id = f"{log.get('timestamp', '')}-{log.get('source', '')}-{log.get('message', '')}"
                    
                    if log_id not in self.displayed_logs:
                        new_logs.append(log)
                        self.displayed_logs.add(log_id)
                        self.all_logs.append(log)
                
                return new_logs
            
            return []
            
        except Exception as e:
            # Create an error log entry
            error_log = {
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'source': 'LogMonitor',
                'message': f"Failed to fetch logs: {str(e)}",
                'user': 'system'
            }
            return [error_log]
    
    def print_new_logs(self, new_logs: List[Dict[str, Any]]):
        """Print new logs to console (alternative to live display)."""
        for log in new_logs:
            timestamp = log.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8]
            else:
                time_str = "N/A"
            
            level = log.get('level', '').upper()
            source = log.get('source', 'Unknown')
            message = log.get('message', '')
            
            # Color code the output
            if level == 'ERROR':
                console.print(f"[red]{time_str} [{level}] {source}: {message}[/red]")
            elif level == 'WARNING' or level == 'WARN':
                console.print(f"[yellow]{time_str} [{level}] {source}: {message}[/yellow]")
            elif level == 'INFO':
                console.print(f"[green]{time_str} [{level}] {source}: {message}[/green]")
            else:
                console.print(f"[white]{time_str} [{level}] {source}: {message}[/white]")
    
    def start_monitoring(self, use_live_display: bool = True):
        """Start monitoring logs with live updates."""
        console.print(f"[bold green]Starting log monitoring for experiment group {self.experiment_group_code}...[/bold green]")
        
        # Initial fetch
        initial_logs = self.fetch_new_logs()
        if initial_logs:
            console.print(f"[dim]Found {len(initial_logs)} existing logs[/dim]")
            self.print_new_logs(initial_logs)
        
        if use_live_display:
            # Use Rich Live display for real-time table updates
            try:
                with Live(self.create_log_table(), refresh_per_second=1) as live:
                    while True:
                        time.sleep(self.poll_interval)
                        
                        new_logs = self.fetch_new_logs()
                        if new_logs:
                            # Update the live display
                            live.update(self.create_log_table())
                            
                            # Also print new logs for immediate feedback
                            for log in new_logs:
                                if log.get('level') == 'ERROR':
                                    console.print(f"[bold red]🚨 NEW ERROR: {log.get('message', '')}[/bold red]")
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]Log monitoring stopped by user.[/yellow]")
        else:
            # Simple console output mode
            try:
                while True:
                    time.sleep(self.poll_interval)
                    
                    new_logs = self.fetch_new_logs()
                    if new_logs:
                        self.print_new_logs(new_logs)
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]Log monitoring stopped by user.[/yellow]")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get a summary of all logs collected."""
        if not self.all_logs:
            return {}
        
        summary = {
            'total_logs': len(self.all_logs),
            'levels': {},
            'sources': {},
            'time_range': {
                'start': self.all_logs[0].get('timestamp', ''),
                'end': self.all_logs[-1].get('timestamp', '')
            }
        }
        
        for log in self.all_logs:
            level = log.get('level', 'UNKNOWN')
            source = log.get('source', 'Unknown')
            
            summary['levels'][level] = summary['levels'].get(level, 0) + 1
            summary['sources'][source] = summary['sources'].get(source, 0) + 1
        
        return summary