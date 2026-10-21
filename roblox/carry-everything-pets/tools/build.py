"""Builds the Roblox Studio files for the pet system.

    python tools/build.py

Reads src/ (same layout as default.project.json, Rojo style) and writes:
  build/PetShared.rbxmx   -> right-click ReplicatedStorage > Insert from File...
  build/PetSystem.rbxmx   -> right-click ServerScriptService > Insert from File...
  build/PetClient.rbxmx   -> right-click StarterPlayer > StarterPlayerScripts > Insert from File...
  sourcemap.json          -> for luau-lsp type checking (not needed in Studio)

File rules (like Rojo): a folder becomes a Folder; X.server.luau a Script; X.client.luau a
LocalScript; X.luau a ModuleScript; a folder with init.client.luau becomes that LocalScript
with the other files as its children.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BUILD = ROOT / "build"

# (folder in src, service in the game, output file)
TARGETS = [
    ("ReplicatedStorage/PetShared", ["ReplicatedStorage"], "PetShared.rbxmx"),
    ("ServerScriptService/PetSystem", ["ServerScriptService"], "PetSystem.rbxmx"),
    ("StarterPlayerScripts/PetClient", ["StarterPlayer", "StarterPlayerScripts"], "PetClient.rbxmx"),
]

SERVICE_CLASS = {
    "ReplicatedStorage": "ReplicatedStorage",
    "ServerScriptService": "ServerScriptService",
    "StarterPlayer": "StarterPlayer",
    "StarterPlayerScripts": "StarterPlayerScripts",
}


def script_class(path: Path) -> tuple[str, str]:
    """Returns (instance name, class name) for a .luau file."""
    name = path.name
    if name.endswith(".server.luau"):
        return name[: -len(".server.luau")], "Script"
    if name.endswith(".client.luau"):
        return name[: -len(".client.luau")], "LocalScript"
    return name[: -len(".luau")], "ModuleScript"


def node_for(path: Path) -> dict:
    """Instance tree node: {name, className, file (or None), children}."""
    if path.is_file():
        name, cls = script_class(path)
        return {"name": name, "className": cls, "file": path, "children": []}
    init = None
    for candidate in ("init.client.luau", "init.server.luau", "init.luau"):
        if (path / candidate).exists():
            init = path / candidate
    children = []
    for child in sorted(path.iterdir()):
        if child == init or child.name.startswith("."):
            continue
        if child.is_dir() or child.suffix == ".luau":
            children.append(node_for(child))
    if init:
        _, cls = script_class(init)
        return {"name": path.name, "className": cls, "file": init, "children": children}
    return {"name": path.name, "className": "Folder", "file": None, "children": children}


def referent(seed: str) -> str:
    return "RBX" + hashlib.md5(seed.encode()).hexdigest().upper()


def cdata(text: str) -> str:
    return "<![CDATA[" + text.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def item_xml(node: dict, depth: int, seed: str) -> str:
    pad = "\t" * depth
    lines = [f'{pad}<Item class="{node["className"]}" referent="{referent(seed + "/" + node["name"])}">']
    lines.append(f"{pad}\t<Properties>")
    lines.append(f'{pad}\t\t<string name="Name">{escape(node["name"])}</string>')
    if node["file"] is not None:
        source = node["file"].read_text(encoding="utf-8")
        lines.append(f'{pad}\t\t<ProtectedString name="Source">{cdata(source)}</ProtectedString>')
    lines.append(f"{pad}\t</Properties>")
    for child in node["children"]:
        lines.append(item_xml(child, depth + 1, seed + "/" + node["name"]))
    lines.append(f"{pad}</Item>")
    return "\n".join(lines)


def rbxmx(node: dict) -> str:
    header = (
        '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">'
    )
    return header + "\n" + item_xml(node, 1, "pets") + "\n</roblox>\n"


def sourcemap_node(node: dict) -> dict:
    out = {"name": node["name"], "className": node["className"]}
    if node["file"] is not None:
        out["filePaths"] = [node["file"].relative_to(ROOT).as_posix()]
    if node["children"]:
        out["children"] = [sourcemap_node(c) for c in node["children"]]
    return out


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    services: dict[str, dict] = {}
    for folder, service_path, out_name in TARGETS:
        node = node_for(SRC / folder)
        (BUILD / out_name).write_text(rbxmx(node), encoding="utf-8", newline="\n")
        print(f"wrote build/{out_name}")
        # sourcemap: nest under the service path
        parent_children = services
        parent = None
        for service in service_path:
            if service not in parent_children:
                parent_children[service] = {"name": service, "className": SERVICE_CLASS[service], "_children": {}}
            parent = parent_children[service]
            parent_children = parent["_children"]
        parent_children[node["name"]] = {"_node": node}

    def flatten(entry: dict) -> dict:
        if "_node" in entry:
            return sourcemap_node(entry["_node"])
        result = {"name": entry["name"], "className": entry["className"]}
        kids = [flatten(v) for v in entry["_children"].values()]
        if kids:
            result["children"] = kids
        return result

    sourcemap = {"name": "Game", "className": "DataModel", "children": [flatten(v) for v in services.values()]}
    (ROOT / "sourcemap.json").write_text(json.dumps(sourcemap, indent=1), encoding="utf-8")
    print("wrote sourcemap.json")


if __name__ == "__main__":
    main()
