"""
Tests for commands.
"""
import sys

import pytest
from unittest.mock import patch, MagicMock, ANY

from fastman.commands.base import CommandContext, COMMAND_REGISTRY
from fastman.commands.certificate import build_merged_ca_bundle, get_certificate_files
from fastman.commands.project import NewCommand
from fastman.commands.scaffold import MakeFeatureCommand

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


class TestCertificateCommand:
    def test_get_certificate_files_excludes_merged_bundle(self, tmp_path):
        certs_dir = tmp_path / "certs"
        certs_dir.mkdir()
        (certs_dir / "corp.pem").write_text("CERT")
        (certs_dir / "ca-bundle-merged.pem").write_text("MERGED")

        cert_files = get_certificate_files(certs_dir)

        assert cert_files == [certs_dir / "corp.pem"]

    def test_build_merged_ca_bundle(self, tmp_path):
        certs_dir = tmp_path / "certs"
        certs_dir.mkdir()
        (certs_dir / "corp.pem").write_text(
            "-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n",
            encoding="utf-8",
        )
        base_bundle = tmp_path / "cacert.pem"
        base_bundle.write_text("BASE CERT\n", encoding="utf-8")

        fake_certifi = MagicMock()
        fake_certifi.where.return_value = str(base_bundle)

        with patch.dict(sys.modules, {"certifi": fake_certifi}):
            with patch("fastman.commands.certificate._ensure_certifi", return_value=True):
                bundle_path = build_merged_ca_bundle(certs_dir)

        assert bundle_path is not None
        assert bundle_path == certs_dir / "ca-bundle-merged.pem"
        merged = bundle_path.read_text(encoding="utf-8")
        assert "BASE CERT" in merged
        assert "BEGIN CERTIFICATE" in merged

    def test_install_cert_registered(self):
        assert "install:cert" in COMMAND_REGISTRY
