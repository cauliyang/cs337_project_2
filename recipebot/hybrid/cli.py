"""CLI interface for Hybrid recipe assistant."""

import os
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from recipebot.hybrid.agent import HybridAgent

PRINT_USER = os.getenv("PRINT_USER_INPUT", "false").lower() in ("true", "1", "yes")

app = typer.Typer(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
console = Console()


def print_welcome():
    """Print welcome message."""
    welcome_text = """
[bold cyan]Recipe Assistant - Hybrid-Powered[/bold cyan]

I'm your AI cooking assistant powered by Google Gemini 2.5 Flash Lite with external search capabilities.
I can help you understand recipes, answer questions, guide you through cooking, and search for additional information!

[dim]Commands:[/dim]
  • Type a recipe URL to load a recipe
  • Ask questions about ingredients, steps, techniques, etc.
  • Type 'quit' or 'exit' to end the conversation
  • Type 'reset' to start a new conversation
    """
    console.print(Panel(welcome_text, border_style="cyan"))


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_assistant(message: str):
    """Print assistant response."""
    console.print(
        Panel(
            message,
            title="[bold green]Assistant[/bold green]",
            border_style="green",
        )
    )


def print_user(message: str):
    """Print user input."""
    console.print(f"[bold blue]You:[/bold blue] {message}")


def main(parse_html: bool = False):
    """Start interactive chat with hybrid recipe assistant.

    Args:
        parse_html: If True, parse HTML to extract structured recipe data.
                   If False, pass raw HTML to the agent.
    """
    print_welcome()

    try:
        assistant = HybridAgent()
    except ValueError as e:
        print_error(str(e))
        console.print("\n[dim]Make sure GEMINI_API_KEY is set in .env[/dim]")
        sys.exit(1)

    console.print("\n[dim]Ready! Provide a recipe URL or ask a question.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n")
                break

            if user_input.lower() == "reset":
                assistant.reset()
                console.print("[dim]Conversation reset. Ready for a new recipe![/dim]")
                continue

            # Check if input looks like a URL
            if user_input.startswith("http://") or user_input.startswith("https://"):
                console.print(f"[dim]Loading recipe from: {user_input}[/dim]")
                try:
                    recipe_state = assistant.load_recipe(user_input, parse_html=parse_html)
                    response = (
                        f"Recipe loaded successfully!\n\n"
                        f"**{recipe_state.title}**\n\n"
                        f"• {len(recipe_state.ingredients)} ingredients\n"
                        f"• {len(recipe_state.directions)} directions\n"
                        f"• {len(recipe_state.steps)} parsed steps\n"
                    )
                    print_assistant(response)
                except Exception as e:
                    print_error(f"Failed to load recipe: {e}")
            else:
                # Regular question
                if not assistant.current_recipe_state:
                    print_error("No recipe loaded. Please provide a recipe URL first.")
                    continue
                if PRINT_USER:
                    print_user(user_input)
                response = assistant.ask(user_input)
                # print current step as prefix of the response
                response = f"Step {assistant.current_recipe_state.current_step}: \n {response}"
                markdown = Markdown(response)
                print_assistant(markdown)

        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n")
            break
        except EOFError:
            console.print("\n\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n")
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context, parse_html: bool = False):
    """Recipe Assistant - Hybrid-Powered.

    Args:
        ctx: Typer context.
        parse_html: If True, parse HTML to extract structured recipe data.
    """
    if ctx.invoked_subcommand is None:
        main(parse_html=parse_html)


@app.command()
def chat(parse_html: bool = False):
    """Start interactive chat with hybrid recipe assistant.

    Args:
        parse_html: If True, parse HTML to extract structured recipe data.
                   If False, pass raw HTML to the agent.
    """
    main(parse_html=parse_html)


if __name__ == "__main__":
    app()
