"""Script to extract environment variables."""

# !/usr/bin/env uv run
import argparse
import difflib
import logging
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Exclusion patterns for directories
EXCLUDE_DIRS = {
    "venv",
    ".venv",
    ".git",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".ruff_cache",
    "staticfiles",
    "node_modules",
    ".envs",
    "__pycache__",
}

# var_name, default_value from python files
PYTHON_ENV_PATTERNS = [
    (
        r'env(?:\.\w+)?\(\s*["\']([^"\']+)["\'](?:,\s*default=(?:get_random_secret_key\(\)|'
        r'get_random_string\(50, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789"\)|'
        r"[^,\)]+))?\s*\)"
    ),
    r'os\.getenv\(\s*["\']([^"\']+)["\'](?:,\s*([^,\)]+))?\s*\)',
    r'os\.environ\.get\(\s*["\']([^"\']+)["\'](?:,\s*([^,\)]+))?\s*\)',
    r'os\.environ\[\s*["\']([^"\']+)["\']\s*\]',
]

# var_name, default_value from compose files
COMPOSE_ENV_PATTERN = r"\$\{([^}:-]+)(?::-([^}]*))?\}"


def extract_comment(lines: list[str], line_index: int) -> str:
    """Pull comments from either the same line or right above to add context.

    Returns:
        str: comment relevant to the envvar line
    """
    # Check same line comments
    current_line = lines[line_index]
    if "#" in current_line:
        comment = current_line.split("#", 1)[1].strip()
        if comment:
            return comment

    # Check lines above
    comments_above = []
    # Start at the line above and continue up the lines until you find a line without a comment
    # or you hit the beginning of the file
    for i in range(line_index - 1, -1, -1):
        prev_line = lines[i].strip()
        if prev_line.startswith("#"):
            comments_above.insert(0, prev_line.lstrip("#").strip())
        else:
            break

    if comments_above:
        return " ".join(comments_above)
    return ""


def clean_comment(comment: str) -> str:
    """Remove heavily repeated special characters which are mostly useless in docs.

    Returns:
        str: a comment without special characters
    """
    if not comment:
        return ""
    comment = re.sub(r"[^a-zA-Z0-9\s]{2,}", " ", comment)
    comment = comment.strip(" #=-_*.")
    comment = re.sub(r"\s+", " ", comment)
    return comment.strip()


def extract_from_python(content: str, file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract environment variables from Python files.

    Returns:
        dict: python environment variables
    """
    vars_found: dict[str, dict[str, Any]] = {}
    lines = content.splitlines()
    for i, line in enumerate(lines):
        for pattern in PYTHON_ENV_PATTERNS:
            # finditer so that we have loop over the matches as dicts
            # (match.group(1) is the var name, match.group(2) is the default value)
            matches = re.finditer(pattern, line)
            for match in matches:
                var_name = match.group(1)
                default_value = match.group(2) if len(match.groups()) > 1 else None
                comment = clean_comment(extract_comment(lines, i))

                if var_name not in vars_found:
                    vars_found[var_name] = {"default": default_value, "desc": comment, "file": {str(file_path)}}
                # update comment if there wasnt one in previous findings of the var
                elif comment and not vars_found[var_name]["desc"]:
                    vars_found[var_name]["desc"] = comment
    return vars_found


def extract_from_compose(content: str, file_path: Path) -> dict[str, dict[str, Any]]:
    """Extract environment variables from Compose files.

    Returns:
        dict: compose environment variables
    """
    vars_found: dict[str, dict[str, Any]] = {}
    lines = content.splitlines()
    for i, line in enumerate(lines):
        matches = re.finditer(COMPOSE_ENV_PATTERN, line)
        for match in matches:
            var_name = match.group(1)
            default_value = match.group(2) if len(match.groups()) > 1 else None
            comment = clean_comment(extract_comment(lines, i))

            if var_name not in vars_found:
                vars_found[var_name] = {"default": default_value, "desc": comment, "file": {str(file_path)}}
            elif comment and not vars_found[var_name]["desc"]:
                vars_found[var_name]["desc"] = comment
    return vars_found


def infer_environment(file_path: Path) -> str:
    """Infer the environment from the file path.

    Returns:
        str: the type of environment
    """
    path_str = str(file_path)
    if "production" in path_str:
        return "Production"
    if "local" in path_str:
        return "Local"
    if "test" in path_str:
        return "Test"
    if "settings/base" in path_str or "shared" in path_str or "common" in path_str or path_str == "compose.yml":
        return "Common"
    return "Unknown"


def get_service(file_path: Path) -> str:
    """Determine the service name based on the file path.

    Returns:
        str: the name of the service/app
    """
    path_parts = Path(file_path).parts
    if "config" in path_parts:
        return "Django"
    if "translator" in path_parts:
        return "Translator"
    if "scheduler" in path_parts:
        return "Scheduler"
    if "compose" in path_parts or Path(file_path).name.startswith("compose"):
        return "Compose"
    return "Other"


def parse_existing_docs(output_path: Path) -> dict[str, str]:
    """Parse existing documentation to preserve manual descriptions.

    Returns:
        dict: a dictionary with existing descriptions
    """
    manual_descs: dict[str, str] = {}
    if not output_path.exists():
        return manual_descs

    content = output_path.read_text(encoding="utf-8")
    rows = re.findall(r"\| `([^`]+)` \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+ \| ([^|]*)\|", content)
    for var, desc in rows:
        clean_desc = clean_comment(desc.strip())
        if clean_desc and clean_desc not in {"-", "Manually added description"}:
            manual_descs[var] = clean_desc
    return manual_descs


def find_env_vars(root_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:  # noqa: C901
    """Scan the project directory for environment variables.

    Returns:
        dict: a dictionary with all the environment variables
    """
    all_vars: dict[tuple[str, str], dict[str, Any]] = {}

    for path in root_dir.rglob("*"):
        if any(exclude in path.parts for exclude in EXCLUDE_DIRS):
            continue

        rel_path = path.relative_to(root_dir)

        if path.suffix == ".py":
            try:
                content = path.read_text()
                vars_found = extract_from_python(content, rel_path)
                for var, info in vars_found.items():
                    service = get_service(rel_path)
                    key = (var, service)
                    if key not in all_vars:
                        all_vars[key] = {
                            "envs": set(),
                            "default": info["default"],
                            "desc": info["desc"],
                            "file": set(),
                        }
                    all_vars[key]["envs"].add(infer_environment(rel_path))
                    all_vars[key]["file"].update(info["file"])
                    if info["desc"] and not all_vars[key]["desc"]:
                        all_vars[key]["desc"] = info["desc"]
            except Exception:
                logger.exception("Error reading %s", path)

        elif path.suffix in {".yml", ".yaml"} and "compose" in path.name:
            try:
                content = path.read_text()
                vars_found = extract_from_compose(content, rel_path)
                for var, info in vars_found.items():
                    key = (var, "Compose")
                    if key not in all_vars:
                        all_vars[key] = {
                            "envs": set(),
                            "default": info["default"],
                            "desc": info["desc"],
                            "file": set(),
                        }
                    all_vars[key]["envs"].add(infer_environment(rel_path))
                    all_vars[key]["file"].update(info["file"])
                    if info["desc"] and not all_vars[key]["desc"]:
                        all_vars[key]["desc"] = info["desc"]
            except Exception:
                logger.exception("Error reading %s", path)

    return all_vars


def sort_by_service_and_name(item: tuple[tuple[str, str], dict[str, Any]]) -> tuple[str, str]:
    """Sort by Service Name first, then Variable Name.

    Returns:
        tuple: of the service name and variable name
    """
    (var_name, service), _metadata = item
    return service, var_name


def generate_markdown_content(all_vars: dict[tuple[str, str], dict[str, Any]], manual_descs: dict[str, str]) -> str:
    """Generate the markdown content for the environment variables documentation.

    Returns:
        str: the markdown content
    """
    sorted_vars = sorted(all_vars.items(), key=sort_by_service_and_name)

    lines = [
        "# Environment Variables Reference",
        "",
        "To update, run `make update-env-docs`.",
        "",
        "| Variable | Service | Environments | Default | file | Description |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for (var_name, service), data in sorted_vars:
        if "Common" in data["envs"]:
            envs = "Common"
        elif len(data["envs"]) > 1:
            envs = "Multiple"
        else:
            envs = ", ".join(sorted(data["envs"]))

        # Grab the default value or fall back to "-"
        default = data["default"] if data["default"] else "-"
        # Used to create a link to the file
        file = ", ".join(f"[{f}](file://{f})" for f in sorted(data["file"]))

        # Use manual description if available, otherwise use code comments
        description = manual_descs.get(var_name, data["desc"])
        if not description:
            description = "-"

        lines.append(f"| `{var_name}` | {service} | {envs} | {default} | {file} | {description} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    """Main function to parse arguments and orchestrate the extraction."""
    parser = argparse.ArgumentParser(description="Extract environment variables from SCRAM project.")
    parser.add_argument("--check", action="store_true", help="Check if documentation is up to date.")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    output_path = root_dir / "docs/environment_variables.md"

    manual_descs = parse_existing_docs(output_path)
    all_vars = find_env_vars(root_dir)
    new_content = generate_markdown_content(all_vars, manual_descs)

    if args.check:
        if output_path.exists():
            current_content = output_path.read_text()
            if current_content == new_content:
                logger.info("Documentation is up to date.")
                return
            logger.info("Documentation is out of date:\n")
            diff = difflib.unified_diff(
                current_content.splitlines(),
                new_content.splitlines(),
                fromfile="docs/environment_variables.md (Current)",
                tofile="docs/environment_variables.md (Generated)",
                lineterm="",
            )
            logger.warning("\n".join(diff))
            sys.exit(1)
        else:
            logger.warning("Documentation file docs/environment_variables.md does not exist!")
            sys.exit(1)
    elif output_path.exists() and output_path.read_text() == new_content:
        logger.info("Documentation is already up to date. No changes made.")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(new_content)
        logger.info("Updated docs/environment_variables.md")


if __name__ == "__main__":
    main()
