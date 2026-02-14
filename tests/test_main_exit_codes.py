from typer.testing import CliRunner

from ai_rom_batch_renamer.main import app


runner = CliRunner()


def test_rename_no_input_exit_code_2():
    result = runner.invoke(app, ["rename"])
    assert result.exit_code == 2


def test_revert_no_input_exit_code_2():
    result = runner.invoke(app, ["revert"])
    assert result.exit_code == 2
