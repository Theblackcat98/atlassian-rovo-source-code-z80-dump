from rich.console import Console

from rovodev import USER_EMAIL
from rovodev.common.dynamic_config import DynamicConfiguration

dynamic_configuration = None
if USER_EMAIL:
    dynamic_configuration = DynamicConfiguration(USER_EMAIL)
    if dynamic_configuration.config().banned:
        Console().print(f"[magenta]User {USER_EMAIL} is banned, exiting...[/magenta]")
        exit(0)
