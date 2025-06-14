from nemo.constants import KNOWN_MODELS

from ..ui.components import Choice, user_menu_panel_sync

AVAILABLE_MODELS = [model.split(":", 1)[-1] for model in KNOWN_MODELS]


def handle_models_command(current_model: str) -> str:
    """Handle the /models command."""
    selected_model = user_menu_panel_sync(
        title="Select a supported large language model:",
        choices=[Choice(name=model, value=model) for model in AVAILABLE_MODELS],
        selection=AVAILABLE_MODELS.index(current_model) if current_model in AVAILABLE_MODELS else None,
        border_color="none",
        title_color="none",
    )
    # If the user pressed ESC, selected_model will be None
    if selected_model is None:
        return current_model
    return selected_model
