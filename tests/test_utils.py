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

    def test_validate_identifier_rejects_keywords(self):
        for reserved in ["class", "import", "async", "def", "return", "True", "None"]:
            with pytest.raises(ValueError, match="reserved word"):
                NameValidator.validate_identifier(reserved)

    def test_validate_identifier_rejects_builtins(self):
        # `type` and `match` are soft keywords in 3.12+, so use pure builtins here.
        for builtin in ["list", "dict", "id", "open", "len", "print"]:
            with pytest.raises(ValueError, match="shadows a Python builtin"):
                NameValidator.validate_identifier(builtin)

    def test_validate_path_component(self):
        assert NameValidator.validate_path_component("valid") == "valid"
        with pytest.raises(ValueError):
            NameValidator.validate_path_component("../invalid")
        with pytest.raises(ValueError):
            NameValidator.validate_path_component("in/valid")

    def test_validate_path_component_rejects_keywords(self):
        with pytest.raises(ValueError, match="reserved word"):
            NameValidator.validate_path_component("class")
        with pytest.raises(ValueError, match="shadows a Python builtin"):
            NameValidator.validate_path_component("list")

    def test_to_snake_case(self):
        assert NameValidator.to_snake_case("CamelCase") == "camel_case"
        assert NameValidator.to_snake_case("camelCase") == "camel_case"
        assert NameValidator.to_snake_case("Simple") == "simple"
        assert NameValidator.to_snake_case("HTTPResponse") == "http_response"

    def test_to_pascal_case(self):
        assert NameValidator.to_pascal_case("snake_case") == "SnakeCase"
        assert NameValidator.to_pascal_case("simple") == "Simple"
        assert NameValidator.to_pascal_case("http_response") == "HttpResponse"

    def test_pluralize_regular(self):
        assert NameValidator.pluralize("user") == "users"
        assert NameValidator.pluralize("order") == "orders"
        assert NameValidator.pluralize("product") == "products"

    def test_pluralize_sibilant_endings(self):
        # The cases that the naive `+s` rule got wrong.
        assert NameValidator.pluralize("bus") == "buses"
        assert NameValidator.pluralize("box") == "boxes"
        assert NameValidator.pluralize("address") == "addresses"
        assert NameValidator.pluralize("dish") == "dishes"
        assert NameValidator.pluralize("batch") == "batches"
        assert NameValidator.pluralize("quiz") == "quizes"  # naive; acceptable

    def test_pluralize_y_endings(self):
        assert NameValidator.pluralize("category") == "categories"
        assert NameValidator.pluralize("party") == "parties"
        # Vowel + y just adds -s
        assert NameValidator.pluralize("day") == "days"
        assert NameValidator.pluralize("key") == "keys"

    def test_pluralize_irregular(self):
        assert NameValidator.pluralize("person") == "people"
        assert NameValidator.pluralize("child") == "children"
        assert NameValidator.pluralize("sheep") == "sheep"
        assert NameValidator.pluralize("fish") == "fish"

    def test_pluralize_latin_greek_endings(self):
        # Words common in DB schemas — naive rule would mangle these.
        assert NameValidator.pluralize("analysis") == "analyses"
        assert NameValidator.pluralize("diagnosis") == "diagnoses"
        assert NameValidator.pluralize("thesis") == "theses"

    def test_pluralize_mass_nouns_unchanged(self):
        assert NameValidator.pluralize("data") == "data"
        assert NameValidator.pluralize("equipment") == "equipment"

    def test_pluralize_preserves_empty(self):
        assert NameValidator.pluralize("") == ""


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
    @patch("shutil.which")
    def test_detect_pip(self, mock_which, mock_cwd):
        mock_which.return_value = None  # uv not installed on the system
        mock_path = MagicMock()
        mock_cwd.return_value = mock_path

        # Nothing exists
        mock_path.__truediv__.return_value.exists.return_value = False

        manager, cmd = PackageManager.detect()
        assert manager == "pip"
        assert cmd == []
