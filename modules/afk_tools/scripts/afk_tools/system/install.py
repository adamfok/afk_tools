import sys

def reload_modules():
    """Removes all afk_tools modules from sys.modules so they are freshly imported."""
    print("afk_tools: Reloading modules...")
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("afk_tools")]
    for mod in modules_to_remove:
        del sys.modules[mod]

def run():
    print("afk_tools: Installing...")
    reload_modules()
    print("afk_tools: Installed!")