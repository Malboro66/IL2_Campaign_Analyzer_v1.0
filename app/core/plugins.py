# app/core/plugins.py
import importlib
import pkgutil
from pathlib import Path

class PluginLoader:
    def __init__(self, plugins_folder="app/plugins"):
        self.plugins_folder = Path(plugins_folder)
        self.plugins = []

    def discover_plugins(self):
        """Descobre e importa módulos de plugin"""
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
        """Executa o método de registro de cada plugin"""
        for plugin in self.plugins:
            try:
                plugin.register_plugin(tab_manager)
            except Exception as e:
                print(f"⚠️ Erro ao registrar plugin {plugin}: {e}")
