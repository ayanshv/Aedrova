"""Work the agent writes under 'Documents/<folder>' lands at the project root, not nested."""

from aedrova.agents.checkout import git, hoist_misplaced_project, original_folder, prepare


def snapshot(tmp_path, files=None):
    source = tmp_path / "Documents" / "Test Calc"
    source.mkdir(parents=True)
    for name, text in (files or {}).items():
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return source, prepare(source, tmp_path / "copies")


def test_the_copy_remembers_which_folder_it_came_from(tmp_path):
    source, project = snapshot(tmp_path)
    assert original_folder(project) == source


def test_files_written_under_the_folders_own_path_move_to_the_root(tmp_path):
    source, project = snapshot(tmp_path)
    nested = project / "Documents" / "Test Calc"
    nested.mkdir(parents=True)
    (nested / "calculator.py").write_text("print('hi')\n")
    (nested / "sub").mkdir()
    (nested / "sub" / "README.md").write_text("# Calc\n")
    assert hoist_misplaced_project(project) == "Documents/Test Calc"
    assert (project / "calculator.py").read_text() == "print('hi')\n"
    assert (project / "sub" / "README.md").is_file()
    assert not (project / "Documents").exists()
    status = git(project, "status", "--short")
    assert "calculator.py" in status and "Documents" not in status


def test_a_short_form_of_the_path_is_also_repaired(tmp_path):
    source, project = snapshot(tmp_path)
    (project / "Test Calc").mkdir()
    (project / "Test Calc" / "app.py").write_text("x = 1\n")
    assert hoist_misplaced_project(project) == "Test Calc"
    assert (project / "app.py").is_file() and not (project / "Test Calc").exists()


def test_a_real_folder_with_that_name_in_the_project_is_left_alone(tmp_path):
    source, project = snapshot(tmp_path, {"Test Calc/keep.txt": "mine\n"})
    (project / "Test Calc" / "added.py").write_text("y = 2\n")
    assert hoist_misplaced_project(project) is None
    assert (project / "Test Calc" / "keep.txt").is_file()
    assert (project / "Test Calc" / "added.py").is_file()


def test_nothing_in_the_project_is_overwritten(tmp_path):
    source, project = snapshot(tmp_path, {"calculator.py": "original\n"})
    nested = project / "Documents" / "Test Calc"
    nested.mkdir(parents=True)
    (nested / "calculator.py").write_text("replacement\n")
    (nested / "extra.py").write_text("extra\n")
    hoist_misplaced_project(project)
    assert (project / "calculator.py").read_text() == "original\n"
    assert (project / "extra.py").read_text() == "extra\n"


def test_a_project_without_that_nesting_is_untouched(tmp_path):
    source, project = snapshot(tmp_path, {"main.py": "ok\n"})
    assert hoist_misplaced_project(project) is None
    assert (project / "main.py").is_file()
