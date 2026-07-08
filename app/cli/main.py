import typer

app = typer.Typer(help="Local-first fitness and fat-loss assistant.")


@app.callback()
def main() -> None:
    """Fitness Agent command line interface."""


if __name__ == "__main__":
    app()
