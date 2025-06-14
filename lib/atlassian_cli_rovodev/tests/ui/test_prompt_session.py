from rovodev.commands.run import command
from rovodev.ui.prompt_session import FilteredFileHistory


class TestFilteredFileHistory:

    def test_slash_commands_always_in_history(self, tmp_path):
        """Test that slash commands are always in the history."""
        history_file = tmp_path / "history"
        history = FilteredFileHistory(history_file)
        history_strings = history.load_history_strings()
        assert "/help" in history_strings
        assert "/exit" in history_strings
        assert "/usage" in history_strings
