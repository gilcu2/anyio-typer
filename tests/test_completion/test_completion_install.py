import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest
import shellingham
import typer
from typer.testing import CliRunner

from docs_src.asynchronous import tutorial001 as async_mod
from docs_src.first_steps import tutorial001 as sync_mod

mod_params = ("mod", (sync_mod, async_mod))

runner = CliRunner()


@pytest.mark.parametrize(*mod_params)
def test_completion_install_no_shell(mod):
    result = subprocess.run(
        ["coverage", "run", mod.__file__, "--install-completion"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_TYPER_COMPLETE_TESTING": "True",
            "_TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION": "True",
        },
    )
    # TODO: when deprecating Click 7, remove second option
    assert (
        "Error: Option '--install-completion' requires an argument" in result.stderr
        or "Error: --install-completion option requires an argument" in result.stderr
    )


@pytest.mark.parametrize(*mod_params)
def test_completion_install_bash(bashrc_lock, mod):
    bash_completion_path: Path = Path.home() / ".bashrc"
    text = ""
    if bash_completion_path.is_file():
        text = bash_completion_path.read_text()
    result = subprocess.run(
        ["coverage", "run", mod.__file__, "--install-completion", "bash"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_TYPER_COMPLETE_TESTING": "True",
            "_TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION": "True",
        },
    )
    new_text = bash_completion_path.read_text()
    bash_completion_path.write_text(text)
    install_source = ".bash_completions/tutorial001.py.sh"
    assert install_source not in text
    assert install_source in new_text
    assert "completion installed in" in result.stdout
    assert "Completion will take effect once you restart the terminal" in result.stdout
    install_source_path = Path.home() / install_source
    assert install_source_path.is_file()
    install_content = install_source_path.read_text()
    install_source_path.unlink()
    assert (
        "complete -o default -F _tutorial001py_completion tutorial001.py"
        in install_content
    )


@pytest.mark.parametrize(*mod_params)
def test_completion_install_zsh(zshrc_lock, mod):
    completion_path: Path = Path.home() / ".zshrc"
    text = ""
    if not completion_path.is_file():  # pragma: nocover
        completion_path.write_text('echo "custom .zshrc"')
    if completion_path.is_file():
        text = completion_path.read_text()
    result = subprocess.run(
        ["coverage", "run", mod.__file__, "--install-completion", "zsh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_TYPER_COMPLETE_TESTING": "True",
            "_TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION": "True",
        },
    )
    new_text = completion_path.read_text()
    completion_path.write_text(text)
    zfunc_fragment = "fpath+=~/.zfunc"
    assert zfunc_fragment in new_text
    assert "completion installed in" in result.stdout
    assert "Completion will take effect once you restart the terminal" in result.stdout
    install_source_path = Path.home() / ".zfunc/_tutorial001.py"
    assert install_source_path.is_file()
    install_content = install_source_path.read_text()
    install_source_path.unlink()
    assert "compdef _tutorial001py_completion tutorial001.py" in install_content


@pytest.mark.parametrize(*mod_params)
def test_completion_install_fish(fish_config_lock, mod):
    script_path = Path(mod.__file__)
    completion_path: Path = Path.home() / f".config/fish/completions/{script_path.name}.fish"
    result = subprocess.run(
        ["coverage", "run", mod.__file__, "--install-completion", "fish"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        env={
            **os.environ,
            "_TYPER_COMPLETE_TESTING": "True",
            "_TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION": "True",
        },
    )
    new_text = completion_path.read_text()
    completion_path.unlink()
    assert "complete --command tutorial001.py" in new_text
    assert "completion installed in" in result.stdout
    assert "Completion will take effect once you restart the terminal" in result.stdout


@pytest.mark.parametrize(*mod_params)
def test_completion_install_powershell(powershell_profile_lock, mod):
    app = typer.Typer()
    app.command()(mod.main)
    completion_path: Path = Path.home() / f".config/powershell/Microsoft.PowerShell_profile.ps1"
    completion_path_bytes = f"{completion_path}\n".encode("windows-1252")
    text = ""
    if completion_path.is_file():  # pragma: nocover
        text = completion_path.read_text()

    with mock.patch.object(
        shellingham, "detect_shell", return_value=("pwsh", "/usr/bin/pwsh")
    ):
        with mock.patch.object(
            subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                ["pwsh"], returncode=0, stdout=completion_path_bytes
            ),
        ):
            result = runner.invoke(app, ["--install-completion"])
    install_script = "Register-ArgumentCompleter -Native -CommandName mocked-typer-testing-app -ScriptBlock $scriptblock"
    parent: Path = completion_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    completion_path.write_text(install_script)
    new_text = completion_path.read_text()
    completion_path.write_text(text)
    assert install_script not in text
    assert install_script in new_text
    assert "completion installed in" in result.stdout
    assert "Completion will take effect once you restart the terminal" in result.stdout
