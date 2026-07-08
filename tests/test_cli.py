from typer.testing import CliRunner

from app.cli.main import app


def test_cli_help() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "fitness" in result.output.lower()
