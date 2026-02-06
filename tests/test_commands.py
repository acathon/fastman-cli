"""
Tests for commands.
"""
import pytest
from unittest.mock import patch, MagicMock, ANY
from fastman.commands.project import NewCommand
from fastman.commands.scaffold import MakeFeatureCommand
from fastman.commands.base import CommandContext

class TestNewCommand:
    @patch("fastman.commands.project.PathManager")
    @patch("fastman.commands.project.os.getcwd")
    @patch("fastman.commands.project.os.chdir")
    @patch("fastman.commands.project.subprocess.run")
    def test_new_command_feature(self, mock_run, mock_chdir, mock_getcwd, mock_pm):
        args = ["myproject", "--pattern=feature", "--package=uv", "--database=sqlite"]
        cmd = NewCommand(args)

        # Mock checks
        mock_pm.ensure_dir.return_value = MagicMock()
        mock_pm.write_file.return_value = True

        # Prevent actual file system checks
        with patch("pathlib.Path.exists", return_value=False):
             cmd.handle()

        # Verify directories created
        mock_pm.ensure_dir.assert_any_call(ANY) # Check that some dirs were created

        # Verify files written
        mock_pm.write_file.assert_any_call(ANY, ANY) # Check that files were written

    @patch("fastman.commands.project.Output")
    def test_new_command_invalid_name(self, mock_output):
        args = ["invalid/name"]
        cmd = NewCommand(args)
        with pytest.raises(ValueError):
            cmd.handle()


class TestMakeFeatureCommand:
    @patch("fastman.commands.scaffold.PathManager")
    @patch("fastman.commands.scaffold.Path.exists")
    def test_make_feature(self, mock_exists, mock_pm):
        args = ["user_profile", "--crud"]
        context = CommandContext()
        cmd = MakeFeatureCommand(args, context)

        # Mock filesystem
        def exists_side_effect(self):
            # features dir exists, but user_profile does not
            if str(self).endswith("features"):
                return True
            return False

        # We need to mock Path objects behaving like paths
        # This is tricky with simple mocks.
        # Let's just assume "app/features" exists and "app/features/user_profile" does not.

        with patch("pathlib.Path.exists", side_effect=[True, False]):
             cmd.handle()

        # Verify ensure_dir called for new feature
        mock_pm.ensure_dir.assert_called()

        # Verify 4 files written (models, schemas, service, router)
        assert mock_pm.write_file.call_count == 4
