"""Define tests for our extract env vars script."""

from pathlib import Path

from scripts.extract_env_vars import (
    clean_comment,
    extract_comment,
    extract_from_compose,
    extract_from_python,
    get_service,
    infer_environment,
)


def test_extract_comment() -> None:
    """Test extracting comments from adjacent or identical lines."""
    lines = ["    # A useful comment", "    VAR = os.getenv('FOO') # Same line comment", "    VAR2 = os.getenv('BAR')"]

    assert extract_comment(lines, 1) == "Same line comment"
    assert not extract_comment(lines, 2)
    assert extract_comment(lines, 0) == "A useful comment"


def test_clean_comment() -> None:
    """Test cleaning up special characters and excess whitespace from comments."""
    assert clean_comment("   # -- My comment **  ") == "My comment"
    assert not clean_comment("")
    assert not clean_comment(None)


def test_extract_from_python() -> None:
    """Test extracting environment variables from Python source code strings."""
    content = """
    # This is standard
    os.getenv("STANDARD_VAR")

    os.getenv('DEFAULT_VAR', 'my_default') # Has default

    os.environ.get("ENV_VAR", "env_def")

    os.environ["STRICT_VAR"]

    env.str("DJANGO_VAR", default="django_def")
    """

    dummy_path = Path("dummy.py")
    result = extract_from_python(content, dummy_path)

    assert "STANDARD_VAR" in result
    assert result["STANDARD_VAR"]["default"] is None
    assert result["STANDARD_VAR"]["desc"] == "This is standard"

    assert "DEFAULT_VAR" in result
    assert result["DEFAULT_VAR"]["default"] == "'my_default'"
    assert result["DEFAULT_VAR"]["desc"] == "Has default"

    assert "ENV_VAR" in result
    assert result["ENV_VAR"]["default"] == '"env_def"'

    assert "STRICT_VAR" in result

    assert "DJANGO_VAR" in result
    assert result["DJANGO_VAR"]["default"] is None


def test_extract_from_compose() -> None:
    """Test extracting environment variables and defaults from Compose YAML strings."""
    content = """
    services:
      app:
        environment:
          - SIMPLE_VAR=${SIMPLE_VAR} # Simple description
          - DEFAULT_VAR=${DEFAULT_VAR:-fallback_value}
    """

    dummy_path = Path("compose.yml")
    result = extract_from_compose(content, dummy_path)

    assert "SIMPLE_VAR" in result
    assert result["SIMPLE_VAR"]["default"] is None
    assert result["SIMPLE_VAR"]["desc"] == "Simple description"

    assert "DEFAULT_VAR" in result
    assert result["DEFAULT_VAR"]["default"] == "fallback_value"


def test_infer_environment() -> None:
    """Test inferring the environment label based on specific file paths."""
    assert infer_environment(Path("config/settings/production.py")) == "Production"
    assert infer_environment(Path("config/settings/local.py")) == "Local"
    assert infer_environment(Path("tests/test_something.py")) == "Test"
    assert infer_environment(Path("config/settings/base.py")) == "Common"
    assert infer_environment(Path("translator/shared.py")) == "Common"
    assert infer_environment(Path("compose.yml")) == "Common"
    assert infer_environment(Path("random_file.py")) == "Unknown"


def test_get_service() -> None:
    """Test identifying the service name based on directory structure or file name."""
    assert get_service(Path("config/settings.py")) == "Django"
    assert get_service(Path("translator/app.py")) == "Translator"
    assert get_service(Path("scheduler/tasks.py")) == "Scheduler"
    assert get_service(Path("compose.override.yml")) == "Compose"
    assert get_service(Path("scripts/extract_env_vars.py")) == "Other"
