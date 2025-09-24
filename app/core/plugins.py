"""
Handles the discovery and registration of application plugins.

This module provides a PluginLoader class that scans a designated folder
for plugins, imports them, and executes their registration hooks.
"""
import importlib
import pkgutil
from pathlib import Path

class PluginLoader:
    """
    Discovers, loads, and registers plugins for the application.

    A plugin is a Python module located in the plugins folder that contains
    a `register_plugin` function.
    """
    def __init__(self, plugins_folder="app/plugins"):
        """
        Initialize the plugin loader.

        Args:
            plugins_folder (str, optional): The path to the plugins directory.
                                            Defaults to "app/plugins".
        """
        self.plugins_folder = Path(plugins_folder)
        self.plugins = []

    def discover_plugins(self):
        """
        Discover and import all valid plugin modules from the plugins folder.

        A module is considered a valid plugin if it can be imported and
        contains a `register_plugin` function.

        Returns:
            list: A list of the successfully imported plugin modules.
        """
        if not self.plugins_folder.exists():
            return []

        for _, module_name, _ in pkgutil.iter_modules([str(self.plugins_folder)]):
            full_module = f"app.plugins.{module_name}"
            try:
                module = importlib.import_module(full_module)
                if hasattr(module, "register_plugin"):
                    self.plugins.append(module)
            except Exception as e:
                print(f"⚠️ Erro ao carregar plugin {module_name}: {e}")
        return self.plugins

    def register_tabs(self, tab_manager):
        """
        Execute the registration method for each discovered plugin.

        This method calls the `register_plugin` function in each plugin
        module, passing the application's tab manager to it.

        Args:
            tab_manager: The application's tab manager instance, which
                         plugins can use to add new tabs.
        """
        for plugin in self.plugins:
            try:
                plugin.register_plugin(tab_manager)
            except Exception as e:
                print(f"⚠️ Erro ao registrar plugin {plugin}: {e}")
