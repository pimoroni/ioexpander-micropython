#!/usr/bin/env python

import argparse
import json
from pathlib import Path


def repo_url(repo_url):
    if "git@github.com:" not in repo_url and "https://github.com:" not in repo_url and len(repo_url.split("/")) != 2:
        raise argparse.ArgumentTypeError(f'"{repo_url}" is not a valid GitHub URL')
    repo_url = repo_url.replace("git@github.com:", "")
    repo_url = repo_url.replace("https://github.com:", "")
    repo_url = repo_url.replace("https://github.com/", "")
    return repo_url.removesuffix(".git")


def dep_require_name(dep_url):
    return dep_url.rstrip("/").split("/")[-1].removesuffix("-micropython")


def src_modules(root):
    modules = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        modules.append(str(path.relative_to(root)))
    return modules


def write_package_json(data, repo, version, root):
    data.update({"version": version, "urls": []})
    for relpath in src_modules(root):
        print(f"Adding {relpath} as github:{repo}/src/{relpath}")
        data["urls"].append([relpath, f"github:{repo}/src/{relpath}"])
    Path("package.json").write_text(json.dumps(data, indent=True) + "\n")


def write_manifest(data, version, root):
    lines = [f'metadata(version="{version}")', ""]
    requires = [f'require("{dep_require_name(url)}")' for url, _ver in data.get("deps", [])]
    if requires:
        lines.extend(requires)
        lines.append("")
    lines.extend(f'module("{relpath}", base_path="{root}")' for relpath in src_modules(root))
    Path("manifest.py").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repo", type=repo_url, required=True)
    parser.add_argument("-v", "--ver", required=True)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()

    root = Path(str(args.root).rstrip("/"))

    try:
        data = json.loads(Path("package.json").read_text())
        print("package.json found: updating!")
    except FileNotFoundError:
        data = {}
        print("package.json not found: creating!")

    write_package_json(data, args.repo, args.ver, root)
    write_manifest(data, args.ver, root)


if __name__ == "__main__":
    main()
