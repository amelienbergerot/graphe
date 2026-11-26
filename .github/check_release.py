"""T-0067: fail the release when the tag, pyproject.toml's version and the plugin's version differ.

Usage, from the repository root: python .github/check_release.py v0.1.0
"""

import json
import sys
import tomllib
from pathlib import Path

tag = sys.argv[1]
package = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
plugin = json.loads(Path(".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
if not (tag == f"v{package}" and plugin == package):
    sys.exit(f"the tag {tag}, pyproject.toml's version {package} and plugin.json's version {plugin} differ")
print(f"{tag}: pyproject.toml and plugin.json agree")
