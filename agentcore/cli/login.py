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
from rich.prompt import Prompt
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.traceback import install
from functools import wraps
import json
import sys
import re

from agentcore.managers.client import APIClient, APIError
from agentcore.managers.config import ConfigManager
from agentcore.utils.config import TOKEN_ENDPOINT
from agentcore.managers.login_manager import LoginManager
from agentcore.managers.base import BaseManager
from agentcore.managers.config import ConfigManager
from agentcore.utils.config import TERM_CONDITIONS_ENDPOINT, PRIVACY_POLICY_ENDPOINT

install()

console = Console()

@click.command(name="login")
@BaseManager.handle_api_error
def login_user():
    """Interactive login command."""
    login_manager = LoginManager()
    base_manager = BaseManager()
    config = ConfigManager()

    config.initialize()
    console.print("[bold blue]Logging in new user (interactive mode)[/bold blue]")
    console.print("Press Ctrl+C at any time to cancel\n")

    email = Prompt.ask("\n[bold]Email of user[/bold]")
    password = base_manager.masked_input("\n[bold]Enter password:[/bold] ")

    login_manager.user_login(email=email, password=password)

if __name__ == "__main__":
    login_user()

@click.command(name="change-password")
@BaseManager.handle_api_error
def change_password():
    """Interactive process to change user password."""
    login_manager = LoginManager()
    base_manager = BaseManager()

    console.print("[bold blue]Password Change Utility[/bold blue]")
    console.print("You can press Ctrl+C at any time to cancel the operation\n")

    try:
        # Using masked input to securely take passwords with '*' masking
        current_password = base_manager.masked_input("\n[bold]Enter current password:[/bold] ")
        new_password = base_manager.masked_input("\n[bold]Enter new password:[/bold] ")
        confirm_password = base_manager.masked_input("\n[bold]Confirm new password:[/bold] ")


        # Validate password before proceeding
        if not validate_passwords(new_password, confirm_password):
            return

        password_data = {
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": confirm_password
        }

        # Proceed with password change
        login_manager.password_change(password_data)

    except KeyboardInterrupt:
        console.print("\n[yellow]Password change operation cancelled[/yellow]")
        sys.exit(1)

def validate_passwords(new_password, confirm_password):
    """Validates new password and confirmation."""
    if new_password != confirm_password:
        console.print("[bold red]Error: New passwords do not match[/bold red]")
        return False

    if len(new_password) < 8:
        console.print("[bold red]Error: Password must be at least 8 characters long[/bold red]")
        return False

    return True

@click.command(name="reset-password")
@BaseManager.handle_api_error
def reset_password():
    """Interactive process to reset user password."""
    login_manager = LoginManager()
    base_manager = BaseManager()

    email = Prompt.ask("[bold]Enter your email[/bold]")

    if not email:
        console.print("[red]Email is required. Aborting operation.[/red]")
        return

    # Attempt to send OTP
    payload = { "email": email }
    response = login_manager.forgot_passowrd(payload)

    # Check for invalid email response
    if not response:
        # console.print("[bold red]Error: No response received from server.[/bold red]")
        return

    console.print(f"[green]{response['message']}[/green]")
    console.print("[blue]Please check your mail for the OTP[/blue]")

    # Retry OTP up to 3 times
    for attempt in range(3):
        otp = Prompt.ask(f"[bold]Please enter OTP[/bold] [dim](Attempt {attempt+1}/3)[/dim]")
        payload = { "email": email, "otp": otp }
        response = login_manager.verify_otp(payload)

        if not response:
            console.print("[bold red]Error: Invalid OTP. Please re-enter the correct OTP[/bold red]")
        else:
            console.print("[green]OTP verified successfully.[/green]")
            break

        if attempt == 2:
            console.print("[red]Maximum OTP attempts reached. Aborting.[/red]")
            return

    reset_token =  response['reset_token']
    # Retry new password input up to 3 times
    attempt = 0
    while True:
        new_password = base_manager.masked_input("\n[bold]Enter new password:[/bold] ")
        confirm_password = base_manager.masked_input("\n[bold]Confirm new password:[/bold] ")
        attempt += 1

        if validate_passwords(new_password, confirm_password):
            break
        else:
            console.print(f"[yellow]Please try again. Attempt {attempt}[/yellow]\n")

    # Call API only after successful validation 
    password_data = {
        "email": email,
        "new_password": new_password,
        "confirm_password": confirm_password,
        "reset_token":reset_token
    }

    response = login_manager.reset_password(password_data)
    if not response:
        console.print("[red]Reset Password operation failed[/red]\n")
        return 
    console.print(f"[green]{response['message']}[/green]")


@click.command()
def logout():
    """Logout from System."""
    
    config_manager = ConfigManager()
    config_manager.clear_details()

    console.print("[purple]Logged out from system Successfully.[purple]")

if __name__ == "__main__":
    logout()


@click.command(name="signup")
@BaseManager.clear_auth_details
@BaseManager.handle_api_error
def signup_user():
    """Interactive signup command with 3-step process."""
    login_manager = LoginManager()
    base_manager = BaseManager()
    config_manager = ConfigManager()

    config_manager.initialize()
    console.print("[bold blue]User Registration (interactive mode)[/bold blue]")
    console.print("Press Ctrl+C at any time to cancel\n")

    try:
        # Step 1: Send OTP to email
        email = Prompt.ask("\n[bold]Enter your email[/bold]")
        
        if not email:
            console.print("[red]Email is required. Aborting operation.[/red]")
            return

        # Send OTP
        payload = {
            "step": "send_otp",
            "email": email
        }
        
        response = login_manager.user_signup(payload)
        if not response:
            console.print("[bold red]Error: Failed to send OTP. Please try again.[/bold red]")
            return

        console.print(f"[green]{response.get('message', 'OTP sent successfully!')}[/green]")
        console.print("[blue]Please check your email for the OTP[/blue]")

        # Step 2: Verify OTP (with retry mechanism)
        verified = False
        for attempt in range(3):
            otp = Prompt.ask(f"[bold]Please enter OTP[/bold] [dim](Attempt {attempt+1}/3)[/dim]")
            
            payload = {
                "step": "verify_otp",
                "email": email,
                "otp": otp
            }
            
            response = login_manager.user_signup(payload)
            
            if not response:
                console.print("[bold red]Error: Invalid OTP. Please re-enter the correct OTP[/bold red]")
                if attempt == 2:
                    console.print("[red]Maximum OTP attempts reached. Registration failed.[/red]")
                    return
            else:
                console.print("[green]OTP verified successfully![/green]")
                verified = True
                break

        if not verified:
            return
        
        terms_conditions_url = config_manager.get("url") + TERM_CONDITIONS_ENDPOINT
        privacy_policy_url = config_manager.get("url") + PRIVACY_POLICY_ENDPOINT

        console.print("\n[bold underline]Terms and Conditions & Privacy Policy[/bold underline]\n")
        console.print(f"• [bold]Terms and Conditions:[/bold] [blue underline]{terms_conditions_url}[/blue underline]")
        console.print(f"• [bold]Privacy Policy:[/bold] [blue underline]{privacy_policy_url}[/blue underline]")

        consent = Prompt.ask(
            "\n[bold]Do you confirm that you have read and agree to the above Terms and Conditions and Privacy Policy?[/bold]",
            choices=["YES", "NO"],
            default="NO"
        )

        if consent.lower() != "yes":
            console.print("\n[yellow]You did not accept the Terms and Conditions. Sign-up has been cancelled.[/yellow]\n")
            return None

        # Step 3: Complete signup with user details
        console.print("\n[bold blue]Please provide your details to complete registration:[/bold blue]")
        
        name = Prompt.ask("\n[bold]Full Name[/bold]")
        if not name:
            console.print("[red]Name is required. Aborting operation.[/red]")
            return

        organization = Prompt.ask("\n[bold]Organization[/bold]")
        if not organization:
            console.print("[red]Organization is required. Aborting operation.[/red]")
            return

        # Password input with validation
        attempt = 0
        while True:
            password = base_manager.masked_input("\n[bold]Enter password:[/bold] ")
            confirm_password = base_manager.masked_input("\n[bold]Confirm password:[/bold] ")
            attempt += 1

            if validate__signup_passwords(password, confirm_password):
                break
            else:
                console.print(f"[yellow]Please try again. Attempt {attempt}[/yellow]\n")
                if attempt >= 3:
                    console.print("[red]Maximum password attempts reached. Registration failed.[/red]")
                    return

        # Complete signup
        payload = {
            "step": "complete_signup",
            "email": email,
            "name": name,
            "password": password,
            "company": organization
        }

        response = login_manager.user_signup(payload)
        if not response:
            console.print("[bold red]Error: Registration failed. Please try again.[/bold red]")
            return

        console.print(f"[green]{response.get('message', 'Registration completed successfully!')}[/green]")
        console.print("[bold green]Welcome! You can now login with your credentials using 'agentcore login' command.[/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Registration cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {str(e)}[/bold red]")
        sys.exit(1)

def validate__signup_passwords(new_password, confirm_password):
    """Validates new password and confirmation with rules."""

    if new_password != confirm_password:
        console.print("[bold red]❌ Error: New passwords do not match[/bold red]")
        return False

    # Rule 1: Must be a string
    if not isinstance(new_password, str):
        console.print("[bold red]❌ Error: Password must be a string[/bold red]")
        return False

    # Rule 2: Length 6–20 characters
    if not (6 <= len(new_password) <= 20):
        console.print("[bold red]❌ Error: Password length must be 6-20 characters[/bold red]")
        return False

    # Rule 3: At least one digit
    if not re.search(r"[0-9]", new_password):
        console.print("[bold red]❌ Error: Password must include at least one digit[/bold red]")
        return False

    # Rule 4: At least one uppercase letter
    if not re.search(r"[A-Z]", new_password):
        console.print("[bold red]❌ Error: Password must include at least one uppercase letter[/bold red]")
        return False

    # Rule 5: At least one lowercase letter
    if not re.search(r"[a-z]", new_password):
        console.print("[bold red]❌ Error: Password must include at least one lowercase letter[/bold red]")
        return False

    # Rule 6: At least one special character
    if not re.search(r"[@$!%*#?&]", new_password):
        console.print("[bold red]❌ Error: Password must include at least one special character (@$!%*#?&)[/bold red]")
        return False

    return True


if __name__ == "__main__":
    signup_user()