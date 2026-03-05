"""The Django project for Security Catch and Release Automation Manager (SCRAM)."""

__version__ = "1.1.1"
__version_info__ = tuple(int(num) if num.isdigit() else num for num in __version__.replace("-", ".", 1).split("."))  # noqa: RUF067
