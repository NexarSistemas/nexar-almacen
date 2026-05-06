import importlib
import os
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from licensing.planes import get_modules_for_tier


REPO_ROOT = Path(__file__).resolve().parents[1]


class LicenseIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        os.environ["ALMACEN_DB_PATH"] = os.path.join(self.tmpdir.name, "almacen-test.db")
        os.environ["XDG_DATA_HOME"] = self.tmpdir.name
        os.environ["SECRET_KEY"] = "test-secret"

        import database
        import licensing.permisos as permisos

        self.db = importlib.reload(database)
        self.permisos = importlib.reload(permisos)
        self.db.init_db()

    def _sync_license(self, **overrides):
        payload = {
            "license_key": "NXR-TEST-0001",
            "plan_original": "BASICA",
            "plan_efectivo": "BASICA",
            "plan": "BASICA",
            "tier": "BASICA",
            "estado": "activa",
            "fallback_aplicado": False,
            "plan_base_permanente": True,
            "expira": "",
        }
        payload.update(overrides)
        self.db.sync_license_from_remote(payload)
        return self.db.get_license_info()

    def test_basica_activa_devuelve_permisos_basica(self):
        info = self._sync_license()
        self.assertEqual(info["tier"], "BASICA")
        self.assertEqual(self.permisos.get_modulos_activos(), get_modules_for_tier("BASICA"))

    def test_pro_activa_devuelve_permisos_pro(self):
        info = self._sync_license(
            plan_original="PRO",
            plan_efectivo="PRO",
            plan="PRO",
            tier="PRO",
            plan_base_permanente=False,
            expira=(date.today() + timedelta(days=15)).isoformat(),
        )
        self.assertEqual(info["tier"], "PRO")
        self.assertEqual(self.permisos.get_modulos_activos(), get_modules_for_tier("PRO"))

    def test_mensual_full_activa_devuelve_permisos_full(self):
        info = self._sync_license(
            plan_original="MENSUAL_FULL",
            plan_efectivo="MENSUAL_FULL",
            plan="MENSUAL_FULL",
            tier="MENSUAL_FULL",
            plan_base_permanente=False,
            expira=(date.today() + timedelta(days=15)).isoformat(),
        )
        self.assertEqual(info["tier"], "MENSUAL_FULL")
        self.assertEqual(self.permisos.get_modulos_activos(), get_modules_for_tier("MENSUAL_FULL"))

    def test_pro_vencida_con_base_permanente_devuelve_basica(self):
        info = self._sync_license(
            plan_original="PRO",
            plan_efectivo="PRO",
            plan="PRO",
            tier="PRO",
            plan_base_permanente=True,
            expira=(date.today() - timedelta(days=2)).isoformat(),
        )
        self.assertEqual(info["plan_original"], "PRO")
        self.assertEqual(info["tier"], "BASICA")
        self.assertTrue(info["fallback_aplicado"])
        self.assertEqual(self.permisos.get_modulos_activos(), get_modules_for_tier("BASICA"))

    def test_pro_vencida_sin_base_permanente_no_devuelve_plan_gratis(self):
        info = self._sync_license(
            plan_original="PRO",
            plan_efectivo="PRO",
            plan="PRO",
            tier="PRO",
            plan_base_permanente=False,
            expira=(date.today() - timedelta(days=2)).isoformat(),
        )
        self.assertEqual(info["plan_original"], "PRO")
        self.assertEqual(info["tier"], "SIN_PLAN")
        self.assertFalse(info["fallback_aplicado"])
        self.assertEqual(self.permisos.get_modulos_activos(), set())

    def test_mensual_full_vencida_con_base_permanente_devuelve_basica(self):
        info = self._sync_license(
            plan_original="MENSUAL_FULL",
            plan_efectivo="MENSUAL_FULL",
            plan="MENSUAL_FULL",
            tier="MENSUAL_FULL",
            plan_base_permanente=True,
            expira=(date.today() - timedelta(days=2)).isoformat(),
        )
        self.assertEqual(info["plan_original"], "MENSUAL_FULL")
        self.assertEqual(info["tier"], "BASICA")
        self.assertTrue(info["fallback_aplicado"])
        self.assertEqual(self.permisos.get_modulos_activos(), get_modules_for_tier("BASICA"))

    def test_mensual_full_vencida_sin_base_permanente_no_devuelve_plan_gratis(self):
        info = self._sync_license(
            plan_original="MENSUAL_FULL",
            plan_efectivo="MENSUAL_FULL",
            plan="MENSUAL_FULL",
            tier="MENSUAL_FULL",
            plan_base_permanente=False,
            expira=(date.today() - timedelta(days=2)).isoformat(),
        )
        self.assertEqual(info["plan_original"], "MENSUAL_FULL")
        self.assertEqual(info["tier"], "SIN_PLAN")
        self.assertFalse(info["fallback_aplicado"])
        self.assertEqual(self.permisos.get_modulos_activos(), set())

    def test_templates_no_exponen_demo_como_plan_comercial(self):
        licencia_template = (REPO_ROOT / "templates" / "licencia.html").read_text(encoding="utf-8")
        self.assertNotIn('<option value="DEMO">', licencia_template)
        self.assertIn('<option value="BASICA"', licencia_template)
        self.assertIn('<option value="PRO">PRO</option>', licencia_template)
        self.assertIn('<option value="MENSUAL_FULL">FULL</option>', licencia_template)

    def test_full_se_muestra_como_full_y_debug_expone_resolucion(self):
        import app as app_module

        app_module = importlib.reload(app_module)
        self.assertEqual(app_module._plan_label("MENSUAL_FULL"), "FULL")

        fake_license = {
            "tier": "BASICA",
            "plan": "PRO",
            "plan_original": "PRO",
            "plan_efectivo": "BASICA",
            "effective_plan": "BASICA",
            "estado": "vencida_con_fallback_basica",
            "fallback_aplicado": True,
            "plan_base_permanente": True,
            "expirada": True,
            "license_key": "NXR-TEST-0001",
        }
        fake_debug = {"final_source": "db_tier", "last_error": "", "sdk_modules": []}

        with app_module.app.test_request_context("/debug/licencia"):
            from flask import session

            session["user"] = {"rol": "admin"}
            with mock.patch.object(app_module.db, "get_license_info", return_value=fake_license), \
                 mock.patch.object(app_module.db, "get_license_modules_from_db", return_value=[]), \
                 mock.patch.object(app_module, "get_modulos_activos", return_value={"core"}), \
                 mock.patch.object(app_module, "get_modulos_debug_info", return_value=fake_debug), \
                 mock.patch.object(app_module, "get_supabase_debug_state", return_value={"configured": False}), \
                 mock.patch.object(app_module, "cargar_licencia", return_value={"license_key": "NXR-TEST-0001"}):
                data = app_module.debug_licencia().get_json()

        self.assertEqual(data["plan_original"], "PRO")
        self.assertEqual(data["plan_efectivo"], "BASICA")
        self.assertEqual(data["estado"], "vencida_con_fallback_basica")
        self.assertTrue(data["fallback_aplicado"])


if __name__ == "__main__":
    unittest.main()
