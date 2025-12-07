"""CLI interface for LLM-only recipe assistant."""

import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from recipebot.llm.agent import RecipeAssistant

app = typer.Typer(invoke_without_command=True)
console = Console()


def print_welcome():
    """Print welcome message."""
    welcome_text = """
[bold cyan]Recipe Assistant - LLM-Powered[/bold cyan]

I'm your AI cooking assistant powered by Google Gemini 2.5 Flash Lite.
I can help you understand recipes, answer questions, and guide you
through cooking!

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


def main():
    """Start interactive chat with recipe assistant."""
    print_welcome()

    try:
        assistant = RecipeAssistant()
    except ValueError as e:
        print_error(str(e))
        console.print(
            "\n[dim]Make sure GEMINI_API_KEY is set in gemini.env[/dim]"
        )
        sys.exit(1)

    console.print(
        "\n[dim]Ready! Provide a recipe URL or ask a question.[/dim]\n"
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ["quit", "exit", "q"]:
                console.print(
                    "\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n"
                )
                break

            if user_input.lower() == "reset":
                assistant.reset()
                console.print(
                    "[dim]Conversation reset. Ready for a new recipe![/dim]"
                )
                continue

            # Check if input looks like a URL
            if user_input.startswith("http://") or user_input.startswith(
                "https://"
            ):
                console.print(f"[dim]Loading recipe from: {user_input}[/dim]")
                try:
                    response = assistant.load_recipe(user_input)
                    print_assistant(response)
                except Exception as e:
                    print_error(f"Failed to load recipe: {e}")
            else:
                # Regular question
                if not assistant.current_recipe_text:
                    print_error(
                        "No recipe loaded. Please provide a recipe URL first."
                    )
                    continue

                print_user(user_input)
                response = assistant.ask(user_input)
                print_assistant(response)

        except KeyboardInterrupt:
            console.print(
                "\n\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n"
            )
            break
        except EOFError:
            console.print(
                "\n\n[bold cyan]Goodbye! Happy cooking! 👨‍🍳[/bold cyan]\n"
            )
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Recipe Assistant - LLM-Powered."""
    if ctx.invoked_subcommand is None:
        main()


@app.command()
def chat():
    """Start interactive chat with recipe assistant."""
    main()


if __name__ == "__main__":
    app()

