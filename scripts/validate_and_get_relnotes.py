"""Validates that module version matches one in release and extracts release's changelog."""
import json
import os
import re
import sys


def _get_module_version(module):
    with open(os.path.join(module, "version.py"), "r") as f:
        tmp_dict = {}
        exec(f.read(), tmp_dict)
        return tmp_dict["__version__"]


def _get_relnotes(module, version, separator="\n"):
    with open("RELEASE.md", "r") as f:
        output = []
        version_regex = r"##\s*[vV]?" + version.replace(".", r"\.")
        found = False
        for line in f:
            if not found:
                if re.match(version_regex, line):
                    found = True
                continue
            if line.startswith("##"):
                break
            stripped = line.rstrip()
            if stripped:
                output.append(stripped)
    if not found:
        raise ValueError(f"Release notes for version {version} not found in README.md!")
    return separator.join(output)


def _main():
    event = json.loads(os.environ["EVENT"])

    try:
        tag = event["release"]["tag_name"]
    except KeyError:
        print("Invalid github event payload:")
        print(json.dumps(event, indent=2))
        return 1

    module, version = tag.rsplit("-", 1)

    version_from_file = _get_module_version(module)
    if version_from_file != version:
        print(f"ERROR: Version mismatch. Expected: {version}, in version.py: {version_from_file}")
        return 1

    release_notes = _get_relnotes(module, version, r"\n")
    if not release_notes:
        raise ValueError(f"Release notes for version {version} are empty!")

    print(f"changelog={release_notes}")

    return 0


if __name__ == '__main__':
    sys.exit(_main())
