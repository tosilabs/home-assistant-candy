"""Check that an unchanged Ready panel is never treated as successful Start."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/candy"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


start = load_module("start_status", ROOT / "start_status.py")
response = load_module("write_response", ROOT / "client/write_response.py")


class StartStatusTest(unittest.TestCase):
    def status(self, state="IDLE", error=None):
        return SimpleNamespace(machine_state=SimpleNamespace(name=state), error=error,
                               temp=40, spin_speed=1000, remote_control=True)

    def test_photo_ready_40_1000_is_not_confirmation(self):
        status = self.status()
        self.assertEqual(start.start_outcome(status, True), "not_confirmed")
        snapshot = start.status_snapshot(status)
        self.assertEqual(snapshot["temperature"], 40)
        self.assertEqual(snapshot["spin_rpm"], 1000)

    def test_stale_running_status_is_not_confirmation(self):
        self.assertEqual(start.start_outcome(self.status("RUNNING"), False), "status_unavailable")

    def test_running_is_not_proof_of_recipe_identity(self):
        self.assertEqual(start.start_outcome(self.status("RUNNING"), True), "running_recipe_unverified")

    def test_error_and_pending_selection_are_not_success(self):
        self.assertEqual(start.start_outcome(self.status("RUNNING", 3), True), "device_error")
        self.assertEqual(start.start_outcome(self.status("ERROR"), True), "device_error")
        self.assertEqual(start.start_outcome(self.status("DELAYED_START_SELECTION"), True), "not_confirmed")

    def test_programmed_delay_is_activity_without_recipe_confirmation(self):
        self.assertEqual(start.start_outcome(self.status("DELAYED_START_PROGRAMMED"), True), "scheduled_recipe_unverified")

    def test_diagnostics_exclude_connection_secrets(self):
        status = self.status()
        status.encryption_key = "private"
        status.device_ip = "192.0.2.1"
        snapshot = start.status_snapshot(status)
        self.assertNotIn("encryption_key", snapshot)
        self.assertNotIn("device_ip", snapshot)

    def test_http200_bad_request_variants_are_rejected(self):
        for text in ['{"response":"BAD REQUEST"}', '{"response":"BAD_REQUEST"}', 'BAD-REQUEST',
                     '{"accepted":false}', '{"success":false}', '{"status":"NACK"}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                response.validate_write_response(text)

    def test_empty_or_unknown_acknowledgment_still_requires_status_check(self):
        for text in ["", "OK", '{"response":"OK"}', "unrecognized"]:
            response.validate_write_response(text)
        self.assertEqual(start.start_outcome(self.status(), True), "not_confirmed")
