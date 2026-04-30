import os
import sys
from PySide6.QtCore import QSettings


def _create_settings() -> QSettings:
    if getattr(sys, "frozen", False):
        # Portable mode: store settings.ini next to exe
        ini_path = os.path.join(os.path.dirname(sys.executable), "settings.ini")
        return QSettings(ini_path, QSettings.Format.IniFormat)
    # Dev mode: use registry/ini defaults
    return QSettings("TinyPNGTool", "TinyPNGCompressor")


class SettingsManager:
    def __init__(self):
        self._settings = _create_settings()

    @property
    def api_key(self) -> str:
        return self._settings.value("api/key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._settings.setValue("api/key", value)

    @property
    def output_dir(self) -> str:
        return self._settings.value("output/dir", "")

    @output_dir.setter
    def output_dir(self, value: str):
        self._settings.setValue("output/dir", value)

    @property
    def default_mode(self) -> str:
        return self._settings.value("mode/default", "api")

    @default_mode.setter
    def default_mode(self, value: str):
        self._settings.setValue("mode/default", value)

    @property
    def concurrency(self) -> int:
        val = self._settings.value("api/concurrency", 5)
        return int(val) if val else 5

    @concurrency.setter
    def concurrency(self, value: int):
        self._settings.setValue("api/concurrency", value)

    @property
    def web_browser_path(self) -> str:
        return self._settings.value("web/browser_path", "")

    @web_browser_path.setter
    def web_browser_path(self, value: str):
        self._settings.setValue("web/browser_path", value)
