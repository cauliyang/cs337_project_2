import typer

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


@app.command()
def hello(name: str):
    """Greet the user by name."""
    typer.echo(f"Hello, {name}!")


if __name__ == "__main__":
    app()
