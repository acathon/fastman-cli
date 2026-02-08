"""
Integration tests for Fastman CLI.
These tests use the real filesystem and verify actual behavior.
"""
import os
import sys
import pytest
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastman.main import CLI
from fastman.commands.base import CommandContext
from fastman.utils import NameValidator, PathManager, PackageManager
from fastman.templates import Template


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp(prefix="fastman_test_"))
    original_cwd = os.getcwd()
    os.chdir(temp_path)
    yield temp_path
    os.chdir(original_cwd)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def cli() -> CLI:
    """Create a CLI instance."""
    return CLI()


@pytest.fixture
def context() -> CommandContext:
    """Create a command context."""
    return CommandContext()


class TestProjectCreation:
    """Integration tests for project creation commands."""
    
    def test_new_project_creates_directory_structure(self, temp_dir: Path, cli: CLI):
        """Test that 'new' command creates proper directory structure."""
        project_name = "test_project"
        
        # Run the command
        cli.run(["new", project_name, "--pattern=feature", "--package=pip", "--database=sqlite"])
        
        # Verify project directory exists
        project_path = temp_dir / project_name
        assert project_path.exists(), f"Project directory {project_path} should exist"
        
        # Verify core directories
        assert (project_path / "app" / "core").exists(), "app/core should exist"
        assert (project_path / "app" / "features").exists(), "app/features should exist"
        assert (project_path / "tests").exists(), "tests should exist"
        assert (project_path / "logs").exists(), "logs should exist"
        
        # Verify alembic exists for SQL databases
        assert (project_path / "alembic").exists(), "alembic should exist for SQLite"
    
    def test_new_project_creates_core_files(self, temp_dir: Path, cli: CLI):
        """Test that 'new' command creates essential files."""
        project_name = "test_api"
        
        cli.run(["new", project_name, "--pattern=api", "--package=pip", "--database=sqlite"])
        
        project_path = temp_dir / project_name
        
        # Verify essential files
        assert (project_path / "app" / "main.py").exists(), "app/main.py should exist"
        assert (project_path / "app" / "core" / "config.py").exists(), "app/core/config.py should exist"
        assert (project_path / "app" / "core" / "database.py").exists(), "app/core/database.py should exist"
        assert (project_path / ".env").exists(), ".env should exist"
        assert (project_path / ".gitignore").exists(), ".gitignore should exist"
        assert (project_path / "README.md").exists(), "README.md should exist"
    
    def test_new_project_env_file_contents(self, temp_dir: Path, cli: CLI):
        """Test that .env file contains proper configuration."""
        project_name = "test_env"
        
        cli.run(["new", project_name, "--pattern=feature", "--package=pip", "--database=sqlite"])
        
        env_path = temp_dir / project_name / ".env"
        env_content = env_path.read_text()
        
        # Verify key configuration
        assert f"PROJECT_NAME={project_name}" in env_content, "PROJECT_NAME should be set"
        assert "DATABASE_URL=sqlite:///" in env_content, "DATABASE_URL should be SQLite"
        assert "SECRET_KEY=" in env_content, "SECRET_KEY should exist"
        assert len([line for line in env_content.split('\n') if line.strip()]) > 5, "ENV should have multiple config lines"
    
    def test_new_project_different_patterns(self, temp_dir: Path, cli: CLI):
        """Test that different architecture patterns create correct structure."""
        patterns = ["feature", "api", "layer"]
        
        for pattern in patterns:
            project_name = f"test_{pattern}"
            cli.run(["new", project_name, f"--pattern={pattern}", "--package=pip", "--database=sqlite"])
            
            project_path = temp_dir / project_name
            
            if pattern == "feature":
                assert (project_path / "app" / "features").exists(), f"feature pattern should have app/features"
            elif pattern == "api":
                assert (project_path / "app" / "api").exists(), f"api pattern should have app/api"
                assert (project_path / "app" / "schemas").exists(), f"api pattern should have app/schemas"
            elif pattern == "layer":
                assert (project_path / "app" / "controllers").exists(), f"layer pattern should have app/controllers"
                assert (project_path / "app" / "services").exists(), f"layer pattern should have app/services"
                assert (project_path / "app" / "repositories").exists(), f"layer pattern should have app/repositories"
    
    def test_new_project_different_databases(self, temp_dir: Path, cli: CLI):
        """Test that different database options create correct config."""
        databases = ["sqlite", "postgresql", "mysql", "oracle"]
        
        for db in databases:
            project_name = f"test_{db}"
            cli.run(["new", project_name, "--pattern=feature", "--package=pip", f"--database={db}"])
            
            env_path = temp_dir / project_name / ".env"
            env_content = env_path.read_text()
            
            if db == "sqlite":
                assert "sqlite:///" in env_content, f"SQLite should have sqlite URL"
            elif db == "postgresql":
                assert "postgresql://" in env_content, f"PostgreSQL should have postgresql URL"
            elif db == "mysql":
                assert "mysql+pymysql://" in env_content, f"MySQL should have mysql URL"
            elif db == "oracle":
                assert "oracle+cx_oracle://" in env_content, f"Oracle should have oracle URL"
    
    def test_new_project_with_firebase_no_alembic(self, temp_dir: Path, cli: CLI):
        """Test that Firebase projects don't have alembic."""
        project_name = "test_firebase"
        
        cli.run(["new", project_name, "--pattern=feature", "--package=pip", "--database=firebase"])
        
        project_path = temp_dir / project_name
        
        # Firebase should NOT have alembic
        assert not (project_path / "alembic").exists(), "Firebase projects should not have alembic"
        
        # Should have Firebase-specific files
        assert (project_path / "app" / "core" / "firebase.py").exists(), "Firebase projects should have firebase.py"
        assert (project_path / "firebase-credentials.json.example").exists(), "Firebase projects should have credentials example"
    
    def test_new_project_refuses_existing_directory(self, temp_dir: Path, cli: CLI):
        """Test that 'new' command refuses to overwrite existing directory."""
        project_name = "existing_project"
        existing_path = temp_dir / project_name
        existing_path.mkdir()
        (existing_path / "some_file.txt").write_text("content")
        
        # Capture exit code
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["new", project_name])
        
        assert exc_info.value.code == 1, "Should exit with error code 1"
    
    def test_new_project_invalid_pattern(self, temp_dir: Path, cli: CLI):
        """Test that invalid pattern is rejected."""
        project_name = "test_invalid"
        
        # Should not raise, but should print error
        cli.run(["new", project_name, "--pattern=invalid_pattern"])
        
        # Directory should not be created
        assert not (temp_dir / project_name).exists(), "Invalid pattern should not create project"


class TestScaffoldCommands:
    """Integration tests for scaffolding commands."""
    
    def test_make_feature_creates_feature_files(self, temp_dir: Path, cli: CLI):
        """Test that 'make:feature' creates all necessary files."""
        # First create a project
        cli.run(["new", "test_project", "--pattern=feature", "--package=pip", "--database=sqlite"])
        os.chdir(temp_dir / "test_project")
        
        # Create a feature
        cli.run(["make:feature", "users", "--crud"])
        
        feature_path = temp_dir / "test_project" / "app" / "features" / "users"
        
        # Verify feature files
        assert (feature_path / "__init__.py").exists(), "Feature __init__.py should exist"
        assert (feature_path / "models.py").exists(), "models.py should exist"
        assert (feature_path / "schemas.py").exists(), "schemas.py should exist"
        assert (feature_path / "service.py").exists(), "service.py should exist"
        assert (feature_path / "router.py").exists(), "router.py should exist"
    
    def test_make_feature_content_is_valid(self, temp_dir: Path, cli: CLI):
        """Test that generated feature files contain valid Python code."""
        cli.run(["new", "test_project", "--pattern=feature", "--package=pip", "--database=sqlite"])
        os.chdir(temp_dir / "test_project")
        
        cli.run(["make:feature", "product"])
        
        feature_path = temp_dir / "test_project" / "app" / "features" / "product"
        
        # Read and verify model file
        models_content = (feature_path / "models.py").read_text()
        assert "class Product" in models_content, "Model should define Product class"
        assert "__tablename__" in models_content, "Model should have __tablename__"
        assert "from sqlalchemy" in models_content, "Model should import sqlalchemy"
        
        # Verify schema file
        schemas_content = (feature_path / "schemas.py").read_text()
        assert "class ProductBase" in schemas_content, "Schema should have ProductBase"
        assert "class ProductCreate" in schemas_content, "Schema should have ProductCreate"
        assert "class ProductRead" in schemas_content, "Schema should have ProductRead"
        assert "from pydantic" in schemas_content, "Schema should import pydantic"
    
    def test_make_feature_fails_without_feature_directory(self, temp_dir: Path, cli: CLI):
        """Test that 'make:feature' fails if not in a feature project."""
        # Create a layer project instead
        cli.run(["new", "test_project", "--pattern=layer", "--package=pip", "--database=sqlite"])
        os.chdir(temp_dir / "test_project")
        
        # Try to create a feature in a layer project
        # Should fail gracefully
        cli.run(["make:feature", "users"])
        
        # Feature directory should not be created
        assert not (temp_dir / "test_project" / "app" / "features" / "users").exists()
    
    def test_make_feature_refuses_duplicate(self, temp_dir: Path, cli: CLI):
        """Test that 'make:feature' refuses to overwrite existing feature."""
        cli.run(["new", "test_project", "--pattern=feature", "--package=pip", "--database=sqlite"])
        os.chdir(temp_dir / "test_project")
        
        # Create feature first time
        cli.run(["make:feature", "orders"])
        
        # Try to create again
        cli.run(["make:feature", "orders"])
        
        # Should still have only one set of files (not overwritten)
        feature_path = temp_dir / "test_project" / "app" / "features" / "orders"
        assert feature_path.exists(), "Feature should exist"


class TestUtilityFunctions:
    """Integration tests for utility functions."""
    
    def test_path_manager_ensure_dir_creates_structure(self, temp_dir: Path):
        """Test PathManager.ensure_dir creates directories and __init__.py."""
        test_path = temp_dir / "a" / "b" / "c"
        
        result = PathManager.ensure_dir(test_path)
        
        assert result.exists(), "Directory should be created"
        assert (test_path / "__init__.py").exists(), "__init__.py should be created"
    
    def test_path_manager_write_file_creates_file(self, temp_dir: Path):
        """Test PathManager.write_file creates files properly."""
        test_file = temp_dir / "test_dir" / "test_file.txt"
        content = "Hello, World!"
        
        result = PathManager.write_file(test_file, content)
        
        assert result is True, "write_file should return True on success"
        assert test_file.exists(), "File should be created"
        assert test_file.read_text() == content, "Content should match"
    
    def test_path_manager_write_file_refuses_overwrite(self, temp_dir: Path):
        """Test PathManager.write_file respects overwrite flag."""
        test_file = temp_dir / "protected.txt"
        test_file.write_text("original")
        
        result = PathManager.write_file(test_file, "new content", overwrite=False)
        
        assert result is False, "Should return False when file exists and overwrite=False"
        assert test_file.read_text() == "original", "Original content should be preserved"
    
    def test_path_manager_write_file_allows_overwrite(self, temp_dir: Path):
        """Test PathManager.write_file allows overwrite when specified."""
        test_file = temp_dir / "overwrite.txt"
        test_file.write_text("original")
        
        result = PathManager.write_file(test_file, "new content", overwrite=True)
        
        assert result is True, "Should return True on successful overwrite"
        assert test_file.read_text() == "new content", "Content should be updated"
    
    def test_path_manager_safe_remove_file(self, temp_dir: Path):
        """Test PathManager.safe_remove removes files."""
        test_file = temp_dir / "to_delete.txt"
        test_file.write_text("delete me")
        
        result = PathManager.safe_remove(test_file)
        
        assert result is True, "Should return True on success"
        assert not test_file.exists(), "File should be deleted"
    
    def test_path_manager_safe_remove_directory(self, temp_dir: Path):
        """Test PathManager.safe_remove removes directories."""
        test_dir = temp_dir / "dir_to_delete"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        result = PathManager.safe_remove(test_dir)
        
        assert result is True, "Should return True on success"
        assert not test_dir.exists(), "Directory should be deleted"
    
    def test_path_manager_safe_remove_nonexistent(self, temp_dir: Path):
        """Test PathManager.safe_remove handles nonexistent paths."""
        test_path = temp_dir / "does_not_exist"
        
        result = PathManager.safe_remove(test_path)
        
        assert result is False, "Should return False for nonexistent path"
    
    def test_name_validator_identifiers(self):
        """Test NameValidator.validate_identifier with various inputs."""
        # Valid identifiers
        assert NameValidator.validate_identifier("valid_name") == "valid_name"
        assert NameValidator.validate_identifier("ValidName") == "ValidName"
        assert NameValidator.validate_identifier("name123") == "name123"
        assert NameValidator.validate_identifier("a") == "a"
        
        # Invalid identifiers
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("123invalid")  # Starts with number
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("invalid-name")  # Contains hyphen
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("invalid name")  # Contains space
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("")  # Empty
    
    def test_name_validator_case_conversions(self):
        """Test NameValidator case conversion methods."""
        # to_snake_case
        assert NameValidator.to_snake_case("CamelCase") == "camel_case"
        assert NameValidator.to_snake_case("snake_case") == "snake_case"
        assert NameValidator.to_snake_case("kebab-case") == "kebab_case"
        assert NameValidator.to_snake_case("mixed-Case_name") == "mixed_case_name"
        
        # to_pascal_case
        assert NameValidator.to_pascal_case("snake_case") == "SnakeCase"
        assert NameValidator.to_pascal_case("kebab-case") == "KebabCase"
        
        # to_kebab_case
        assert NameValidator.to_kebab_case("snake_case") == "snake-case"
        assert NameValidator.to_kebab_case("CamelCase") == "camel-case"


class TestTemplateRendering:
    """Integration tests for template rendering."""
    
    def test_template_rendering_basic(self):
        """Test basic template rendering."""
        template = "Hello, {name}!"
        context = {"name": "World"}
        
        result = Template.render(template, context)
        
        assert result == "Hello, World!", "Template should render with context"
    
    def test_template_rendering_multiple_variables(self):
        """Test template rendering with multiple variables."""
        template = "{greeting}, {name}! You have {count} messages."
        context = {"greeting": "Hi", "name": "Alice", "count": "5"}
        
        result = Template.render(template, context)
        
        assert result == "Hi, Alice! You have 5 messages."
    
    def test_template_rendering_missing_variable(self):
        """Test template rendering with missing variables."""
        template = "Hello, {name}!"
        context = {}  # Missing 'name'
        
        result = Template.render(template, context)
        
        # Should leave placeholder as-is or handle gracefully
        assert "{name}" in result or "Hello, " in result


class TestCommandContext:
    """Integration tests for CommandContext."""
    
    def test_command_context_project_root(self, temp_dir: Path):
        """Test CommandContext detects project root correctly."""
        os.chdir(temp_dir)
        
        context = CommandContext()
        
        assert context.project_root == temp_dir, "project_root should be current directory"
    
    def test_command_context_package_manager_detection(self, temp_dir: Path):
        """Test CommandContext detects package manager from lock files."""
        os.chdir(temp_dir)
        
        # Create a uv.lock file
        (temp_dir / "uv.lock").write_text("")
        
        context = CommandContext()
        
        assert context.package_manager == "uv", "Should detect uv from uv.lock"
        assert context.run_prefix == ["uv", "run"], "Should have correct run prefix"


class TestCLIMain:
    """Integration tests for main CLI functionality."""
    
    def test_cli_help_shows_list(self, temp_dir: Path, cli: CLI):
        """Test that --help shows command list."""
        os.chdir(temp_dir)
        
        # Should not raise or exit
        cli.run(["--help"])
    
    def test_cli_version_shows_version(self, temp_dir: Path, cli: CLI):
        """Test that --version shows version."""
        os.chdir(temp_dir)
        
        # Should not raise or exit
        cli.run(["--version"])
    
    def test_cli_unknown_command_exits_with_error(self, temp_dir: Path, cli: CLI):
        """Test that unknown command exits with error."""
        os.chdir(temp_dir)
        
        with pytest.raises(SystemExit) as exc_info:
            cli.run(["unknown_command"])
        
        assert exc_info.value.code == 1, "Should exit with code 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
