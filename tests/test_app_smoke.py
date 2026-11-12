import importlib.util
import os
import pathlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication


class FreshInstallAppTests(unittest.TestCase):
    def test_first_launch_and_metrics_explorer(self):
        source = pathlib.Path(__file__).resolve().parents[1]
        modules = [
            'OpenRouter_Translate_Viewer.py',
            'archive_metrics_explorer.py',
            'openrouter_db_import.py',
            'openrouter_recovery.py',
            'openrouter_translate_worker.py',
            'openrouter_schema.py',
        ]
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            for name in modules:
                shutil.copy2(source / name, root / name)
            sys.path.insert(0, str(root))
            try:
                spec = importlib.util.spec_from_file_location(
                    'oras_fresh_install_app', root / 'OpenRouter_Translate_Viewer.py'
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                app = QApplication.instance() or QApplication([])
                window = module.Window()
                self.assertEqual(window.windowTitle(), 'OPENROUTER ARCHIVE STUDIO')
                self.assertTrue(module.DB.is_file())
                self.assertEqual(window.table.rowCount(), 0)
                window.show_metrics()
                self.assertIsNotNone(window.metrics_window)
                window.metrics_window.close()
                window.close()
                with closing(sqlite3.connect(module.DB)) as conn:
                    self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                    self.assertEqual(conn.execute('SELECT COUNT(*) FROM generations').fetchone()[0], 0)
                app.processEvents()
            finally:
                if str(root) in sys.path:
                    sys.path.remove(str(root))


if __name__ == '__main__':
    unittest.main()
