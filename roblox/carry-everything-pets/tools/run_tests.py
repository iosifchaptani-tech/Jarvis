"""Runs every test of the pet system.

    python tools/run_tests.py

Needs the `luau` command line tool (https://github.com/luau-lang/luau/releases).
Set LUAU=/path/to/luau if it is not on the PATH.
Optional: LUAU_LSP=/path/to/luau-lsp and ROBLOX_DEFS=/path/to/globalTypes.None.d.luau
also type-check every script against the Roblox API.

  1. tests/test_logic.luau   odds, Equip Best, multiplier, save cleaning, formations, text
  2. tests/test_data.luau    config and models: no missing pets, odds = 100 %, valid parts
  3. tests/test_server.luau  the real PetService in a fake Roblox: hatching, coins, equip,
                             delete, limits, saving, loading errors, game passes, commands
  4. the .rbxmx files are valid XML and hold every script
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "src/ReplicatedStorage/PetShared"
SYSTEM = ROOT / "src/ServerScriptService/PetSystem"
TESTS = ROOT / "tests"


def find_tool(env: str, name: str) -> str | None:
    return os.environ.get(env) or shutil.which(name)


def run(cmd: list[str], cwd: Path = ROOT) -> bool:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    return result.returncode == 0


def preset_names() -> list[str]:
    source = (SHARED / "PetBuilder.luau").read_text(encoding="utf-8")
    block = source.split("local PRESETS = {", 1)[1].split("\n}\n", 1)[0]
    return re.findall(r"^\t(\w+) = \{", block, flags=re.M)


def bundle(test_file: str, modules: dict[str, Path], extra: str = "") -> Path:
    parts = [(TESTS / "server_mocks.luau").read_text(encoding="utf-8")]
    for name, path in modules.items():
        parts.append(f"loaders[{name!r}] = function(script, require)\n{path.read_text(encoding='utf-8')}\nend\n")
    parts.append(extra)
    parts.append((TESTS / test_file).read_text(encoding="utf-8"))
    handle = tempfile.NamedTemporaryFile("w", suffix=".luau", delete=False, encoding="utf-8")
    handle.write("\n".join(parts))
    handle.close()
    return Path(handle.name)


def check_rbxmx() -> bool:
    ok = True
    expected = {
        "PetShared.rbxmx": {"PetConfig", "PetModels", "PetBuilder", "PetLogic"},
        "PetSystem.rbxmx": {"PetServer", "PetService", "EggStands"},
        "PetClient.rbxmx": {"PetClient", "PetRenderer", "PetUI", "HatchCutscene", "UIKit"},
    }
    for file_name, names in expected.items():
        path = ROOT / "build" / file_name
        if not path.exists():
            print(f"missing build/{file_name} (run python tools/build.py)")
            ok = False
            continue
        tree = ET.parse(path)
        found = {el.text for el in tree.iter("string") if el.get("name") == "Name"}
        missing = names - found
        if missing:
            print(f"build/{file_name} is missing {sorted(missing)}")
            ok = False
    print("rbxmx files: ok" if ok else "rbxmx files: FAILED")
    return ok


def main() -> int:
    luau = find_tool("LUAU", "luau")
    if not luau:
        print("Install the luau command line tool or set LUAU=/path/to/luau")
        return 1
    results = []

    print("== logic ==")
    results.append(run([luau, "tests/test_logic.luau"]))

    print("== config and models ==")
    names = ", ".join(f'"{n}"' for n in preset_names())
    data_bundle = bundle(
        "test_data.luau",
        {"PetConfig": SHARED / "PetConfig.luau", "PetLogic": SHARED / "PetLogic.luau", "PetModels": SHARED / "PetModels.luau"},
        f"local PRESET_NAMES = {{ {names} }}\n",
    )
    results.append(run([luau, str(data_bundle)]))

    print("== server (fake Roblox) ==")
    server_bundle = bundle(
        "test_server.luau",
        {
            "PetConfig": SHARED / "PetConfig.luau",
            "PetLogic": SHARED / "PetLogic.luau",
            "PetModels": SHARED / "PetModels.luau",
            "PetService": SYSTEM / "PetService.luau",
        },
        "math.randomseed(7)\n",
    )
    results.append(run([luau, str(server_bundle)]))

    print("== build files ==")
    results.append(check_rbxmx())

    lsp = find_tool("LUAU_LSP", "luau-lsp")
    defs = os.environ.get("ROBLOX_DEFS")
    if lsp and defs:
        print("== Roblox type check ==")
        subprocess.run([sys.executable, str(ROOT / "tools/build.py")], cwd=ROOT, capture_output=True)
        results.append(
            run([lsp, "analyze", "--platform=roblox", f"--defs={defs}", "--sourcemap=sourcemap.json", "--formatter=gnu", "src"])
        )

    if all(results):
        print("ALL TESTS PASSED")
        return 0
    print("SOME TESTS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
