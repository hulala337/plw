from pathlib import Path
from workbench.release import required_files

def test_release_inputs_exist():
    root = Path(__file__).resolve().parents[1]
    assert all(path.is_file() for path in required_files(root))
