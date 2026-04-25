import pytest
from unittest.mock import patch, MagicMock

from fastman.console import Output, Style, Icons

class TestOutput:

    @patch("fastman.console.HAS_RICH", True)
    @patch("fastman.console.console")
    @patch("fastman.console.logger.info")
    def test_success_with_rich(self, mock_logger, mock_console):
        Output.success("Rich success message", icon=True, prefix="[PRE]")

        # Verify console print was called correctly
        mock_console.print.assert_called_once_with(f"[success]{Icons.SUCCESS} [/success][PRE] Rich success message")

        # Verify logger was called
        mock_logger.assert_called_once_with("Rich success message")

    @patch("fastman.console.HAS_RICH", False)
    @patch("fastman.console.logger.info")
    def test_success_without_rich(self, mock_logger, capsys):
        Output.success("Normal success message", icon=True, prefix="[PRE]")

        # Verify stdout
        captured = capsys.readouterr()
        expected_out = f"{Style.BRIGHT_GREEN}{Icons.SUCCESS} {Style.RESET}[PRE] Normal success message\n"
        assert captured.out == expected_out

        # Verify logger
        mock_logger.assert_called_once_with("Normal success message")

    @patch("fastman.console.HAS_RICH", False)
    @patch("fastman.console.logger.info")
    @patch("builtins.print", side_effect=[UnicodeEncodeError("ascii", "", 0, 1, "mock"), None])
    def test_success_without_rich_unicode_fallback(self, mock_print, mock_logger, capsys):
        # We patch print with a side_effect that raises UnicodeEncodeError on the first call,
        # then succeeds on the second (fallback) call.
        # But wait, capsys won't capture patched print if we do it this way easily, so let's verify mock_print calls.
        Output.success("Unicode fallback message", icon=True, prefix="[PRE]")

        # Verify fallback print logic
        assert mock_print.call_count == 2
        mock_print.assert_any_call(f"{Style.GREEN}[OK]{Style.RESET} [PRE] Unicode fallback message")

        # Verify logger
        mock_logger.assert_called_once_with("Unicode fallback message")

    @patch("fastman.console.HAS_RICH", False)
    @patch("fastman.console.logger.info")
    def test_success_no_icon_no_prefix(self, mock_logger, capsys):
        Output.success("Plain message", icon=False, prefix="")

        captured = capsys.readouterr()
        expected_out = f"{Style.BRIGHT_GREEN}{Style.RESET}Plain message\n"
        assert captured.out == expected_out
        mock_logger.assert_called_once_with("Plain message")
