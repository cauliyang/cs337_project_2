"""Recipe parser that fetches and parses recipes from URLs."""

from recipebot.crawler import extract_title_from_url, scrape_recipe
from recipebot.model import Recipe

from .step import parse_steps_from_directions


def show_recipe(recipe: Recipe):
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(f"\n[bold cyan]Fetching recipe from:[/bold cyan] {recipe.url}\n")
    console.print(f"[green]✓[/green] Found {recipe.title} recipe\n")
    console.print(f"[green]✓[/green] Found {len(recipe.ingredients)} ingredients")
    console.print(f"[green]✓[/green] Found {len(recipe.directions)} directions\n")

    console.print(f"[green]✓[/green] Parsed into {len(recipe.steps)} atomic steps\n")

    # Display ingredients
    ing_table = Table(title="Ingredients", show_header=True)
    ing_table.add_column("Quantity", style="cyan")
    ing_table.add_column("Unit", style="magenta")
    ing_table.add_column("Name", style="green")
    ing_table.add_column("Preparation", style="yellow")
    ing_table.add_column("Misc", style="red")

    for ing in recipe.ingredients:
        ing_table.add_row(ing.quantity or "", ing.unit or "", ing.name or "", ing.preparation or "", ing.misc or "")

    console.print(ing_table)
    console.print()

    # Display parsed steps
    for i, step in enumerate(recipe.steps, 1):
        # Create step panel
        step_content = f"[bold]{step.description}[/bold]\n\n"

        if step.ingredients:
            step_content += f"[cyan]Ingredients:[/cyan] {', '.join([ing.name for ing in step.ingredients])}\n"

        if step.tools:
            step_content += f"[magenta]Tools:[/magenta] {', '.join(step.tools)}\n"

        if step.methods:
            step_content += f"[yellow]Methods:[/yellow] {', '.join(step.methods)}\n"

        if step.time:
            time_str = ""
            if "duration" in step.time:
                time_str = f"{step.time['duration']} {step.time.get('unit', '')}"
            elif "duration_min" in step.time:
                time_str = f"{step.time['duration_min']}-{step.time['duration_max']} {step.time.get('unit', '')}"
            else:
                time_str = str(step.time.get("duration", ""))
            step_content += f"[blue]Time:[/blue] {time_str}\n"

        if step.temperature:
            temp_items = [f"{k}: {v}" for k, v in step.temperature.items()]
            step_content += f"[red]Temperature:[/red] {', '.join(temp_items)}\n"

        step_content += f"\n[dim]Actionable: {step.actionable} | Preparatory: {step.is_prepared}[/dim]"

        panel = Panel(step_content, title=f"Step {i}", border_style="green" if step.actionable else "yellow")
        console.print(panel)

    console.print(
        f"\n[bold green]✓ Successfully parsed {len(recipe.steps)} steps from {len(recipe.directions)} directions![/bold green]\n"  # noqa: E501
    )


def parse_recipe(url: str, split_by_atomic_steps: bool = True) -> Recipe:
    """Fetch and parse recipe from URL.

    Returns:
        Parsed Recipe object with ingredients, directions, and steps

    Raises
        ValueError: If URL is invalid or recipe cannot be parsed
        requests.HTTPError: If HTTP request fails
    """
    try:
        ingredients, directions = scrape_recipe(url)
        if not ingredients or not directions:
            raise ValueError(f"Failed to parse recipe from {url}")

        title = extract_title_from_url(url)
        # Parse steps with full metadata
        steps = parse_steps_from_directions(directions, ingredients, split_by_atomic_steps=split_by_atomic_steps)

        # Create Recipe object
        recipe = Recipe(
            url=url,
            title=title,
            ingredients=ingredients,
            directions=directions,
            steps=steps,
        )
        return recipe
    except Exception as e:
        raise ValueError(f"Failed to parse recipe from {url}: {e}") from e
