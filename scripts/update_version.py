import toml
import sys
from pathlib import Path


def update_version():
    # Import version from const.py in the modules folder
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ai_rom_batch_renamer.modules.const import VERSION

    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    data = toml.load(pyproject_path)

    # Update version
    data["tool"]["poetry"]["version"] = VERSION

    # Write back
    with open(pyproject_path, "w") as f:
        toml.dump(data, f)

    print(f"Updated version to {VERSION}")


if __name__ == "__main__":
    update_version()
