"""
Tests for utility classes.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastman.utils import NameValidator, PackageManager, PathManager

class TestNameValidator:
    def test_validate_identifier_valid(self):
        assert NameValidator.validate_identifier("valid_name") == "valid_name"
        assert NameValidator.validate_identifier("ValidName123") == "ValidName123"

    def test_validate_identifier_invalid(self):
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("123invalid")
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("invalid-name")
        with pytest.raises(ValueError):
            NameValidator.validate_identifier("invalid name")

    def test_validate_path_component(self):
        assert NameValidator.validate_path_component("valid") == "valid"
        with pytest.raises(ValueError):
            NameValidator.validate_path_component("../invalid")
        with pytest.raises(ValueError):
            NameValidator.validate_path_component("in/valid")

    def test_to_snake_case(self):
        assert NameValidator.to_snake_case("CamelCase") == "camel_case"
        assert NameValidator.to_snake_case("camelCase") == "camel_case"
        assert NameValidator.to_snake_case("Simple") == "simple"
        assert NameValidator.to_snake_case("HTTPResponse") == "http_response"

    def test_to_pascal_case(self):
        assert NameValidator.to_pascal_case("snake_case") == "SnakeCase"
        assert NameValidator.to_pascal_case("simple") == "Simple"
        assert NameValidator.to_pascal_case("http_response") == "HttpResponse"


class TestPackageManager:
    @patch("pathlib.Path.cwd")
    def test_detect_uv(self, mock_cwd):
        mock_path = MagicMock()
        mock_cwd.return_value = mock_path

        # Mock uv.lock existing
        def exists_side_effect(name):
            return name == "uv.lock"

        # We need to handle (cwd / "uv.lock").exists()
        # mock_path / "uv.lock" returns a new mock, on which we call .exists()

        # A simpler way to mock path joins
        mock_file = MagicMock()
        mock_file.exists.side_effect = [True] # uv.lock exists

        mock_path.__truediv__.return_value = mock_file

        # Ideally we want to control which file exists based on name
        # But Path / string logic is hard to mock perfectly with just one MagicMock
        # So let's rely on patching Path object construction or use fs mock like pyfakefs
        # But for now, let's use a side_effect on __truediv__

        def div_side_effect(other):
            m = MagicMock()
            if other == "uv.lock":
                m.exists.return_value = True
            else:
                m.exists.return_value = False
            return m

        mock_path.__truediv__.side_effect = div_side_effect

        manager, cmd = PackageManager.detect()
        assert manager == "uv"
        assert cmd == ["uv", "run"]

    @patch("pathlib.Path.cwd")
    def test_detect_poetry(self, mock_cwd):
        mock_path = MagicMock()
        mock_cwd.return_value = mock_path

        def div_side_effect(other):
            m = MagicMock()
            if other == "poetry.lock":
                m.exists.return_value = True
            else:
                m.exists.return_value = False
            return m

        mock_path.__truediv__.side_effect = div_side_effect

        manager, cmd = PackageManager.detect()
        assert manager == "poetry"
        assert cmd == ["poetry", "run"]

    @patch("pathlib.Path.cwd")
    @patch("shutil.which")
    def test_detect_uv_with_toml_only(self, mock_which, mock_cwd):
        # Case where uv is installed, pyproject.toml exists, but NO lock files
        mock_which.return_value = "/usr/bin/uv"
        mock_path = MagicMock()
        mock_cwd.return_value = mock_path

        def div_side_effect(other):
            m = MagicMock()
            if other == "pyproject.toml":
                m.exists.return_value = True
            else:
                m.exists.return_value = False # No lock files
            return m

        mock_path.__truediv__.side_effect = div_side_effect

        manager, cmd = PackageManager.detect()
        assert manager == "uv"

    @patch("pathlib.Path.cwd")
    def test_detect_pip(self, mock_cwd):
        mock_path = MagicMock()
        mock_cwd.return_value = mock_path

        # Nothing exists
        mock_path.__truediv__.return_value.exists.return_value = False

        manager, cmd = PackageManager.detect()
        assert manager == "pip"
        assert cmd == []
