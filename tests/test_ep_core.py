import unittest
import os
import ep_core as core

class TestEpCore(unittest.TestCase):
    def test_db_connection(self):
        """Validar que la función de conexión existe"""
        self.assertTrue(callable(core.get_db_connection))

    def test_integrity_check(self):
        """Validar chequeo de integridad del sistema"""
        self.assertIsNotNone(core.check_system_integrity())

    def test_db_file_exists(self):
        """Validar presencia física de la base de datos"""
        self.assertTrue(os.path.exists('database/elpasaje.db'), "Falta elpasaje.db")

    def test_core_imports(self):
        """Validar que ep_core carga dependencias críticas"""
        import pandas as pd
        self.assertIsNotNone(pd.__version__)

    def test_smoke_dependency(self):
        """Validar existencia de script de humo"""
        self.assertTrue(os.path.exists('scripts/smoke_check.py'))

if __name__ == '__main__':
    unittest.main()
