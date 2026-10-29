import pytest

from aedrova.desktop.new_project import NewProjectDialog, create_project_folder


def test_create_empty_project_and_never_overwrite(tmp_path):
    project = create_project_folder(tmp_path, "Team project")
    from pathlib import Path

    marker = Path(project) / "existing.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        create_project_folder(tmp_path, "Team project")
    assert marker.read_text() == "keep"


@pytest.mark.parametrize("name", ["", ".", "..", "../escape", "a/b", "a\\b", "CON", "x\x00"])
def test_reject_invalid_project_names(tmp_path, name):
    with pytest.raises(ValueError):
        create_project_folder(tmp_path, name)
    assert not list(tmp_path.iterdir())


def test_cancel_creates_nothing_and_confirm_returns_folder(qtbot, tmp_path):
    dialog = NewProjectDialog()
    qtbot.addWidget(dialog)
    dialog.location.setText(str(tmp_path))
    dialog.name.setText("Fresh project")
    dialog.reject()
    assert not list(tmp_path.iterdir())
    dialog.create_project()
    assert dialog.project_path == str(tmp_path / "Fresh project")
    assert (tmp_path / "Fresh project").is_dir()


def test_duplicate_project_keeps_dialog_open(qtbot, tmp_path):
    (tmp_path / "Existing").mkdir()
    dialog = NewProjectDialog()
    qtbot.addWidget(dialog)
    dialog.location.setText(str(tmp_path))
    dialog.name.setText("Existing")
    dialog.create_project()
    assert dialog.result() == 0
    assert not dialog.project_path
    assert "already exists" in dialog.status.text()
