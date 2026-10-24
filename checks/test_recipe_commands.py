"""Offline protocol regression checks; run with python -m unittest discover -s checks.

Load only the integration's dependency-free catalogue, settings and command
builders. This does not replace the Home Assistant integration tests.
"""
import importlib
from pathlib import Path
import sys
import types
import unittest
from urllib.parse import parse_qsl

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "candy"
PACKAGE = "_candy_recipe_checks"
for name, path in [(PACKAGE, ROOT), (f"{PACKAGE}.client", ROOT / "client")]:
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    sys.modules[name] = module

settings = importlib.import_module(f"{PACKAGE}.wash_settings")
commands = importlib.import_module(f"{PACKAGE}.client.commands")
options = importlib.import_module(f"{PACKAGE}.program_options")
catalogue = importlib.import_module(f"{PACKAGE}.programs")


def command(data):
    return dict(parse_qsl(commands.washing_machine_start(**settings.wash_command_parameters(data))))


class RecipeCommandsTest(unittest.TestCase):
    def test_grouped_labels_preserve_all_recipe_commands(self):
        for label, name in options.WASH_OPTIONS.items():
            before, after = {}, {}
            settings.select_wash_program(before, name)
            settings.select_wash_program(after, options.resolve_wash_name(label))
            self.assertEqual(command(before), command(after), label)
            self.assertEqual(options.resolve_wash_name(name), name)
        self.assertEqual(len(options.WASH_OPTIONS), len(catalogue.WASHING_MACHINE_PROGRAMS))
        for label, name in options.DRY_OPTIONS.items():
            self.assertEqual(options.resolve_dry_name(label), name)
            self.assertEqual(options.resolve_dry_name(name), name)
        self.assertIsNone(options.resolve_wash_name("Other category - Trainers"))
        self.assertIsNone(options.resolve_dry_name(None))

    def test_trainers_after_hot_cotton_does_not_keep_previous_options(self):
        data = {}
        settings.select_wash_program(data, "Cottons")
        data.update(wm_temp=90, wm_spin=15, wm_soil=3, wm_steam=2, wm_rinse=3)
        settings.select_wash_program(data, "Trainers")
        self.assertEqual(command(data), {
            "Write": "1", "Pa": "0", "Sel": "93", "PrNm": "11", "StSt": "1",
            "TmpTgt": "20", "TmpDf": "20", "SpdTgt": "4", "SpdDef": "4",
            "Stm": "0", "RecipeId": "0", "CheckUpState": "0",
        })

    def test_downloadable_recipes_keep_their_distinct_selector(self):
        data = {}
        for name, selector, temp in [
            ("Trainers", "93", "20"), ("Backpacks", "87", "30"),
            ("Duvet & Quilts", "47", "30"), ("Technical Jackets", "92", "30"),
        ]:
            with self.subTest(name=name):
                settings.select_wash_program(data, name)
                payload = command(data)
                self.assertEqual(payload["PrNm"], "11")
                self.assertEqual(payload["Sel"], selector)
                self.assertEqual(payload["TmpTgt"], temp)
                self.assertEqual(payload["SpdTgt"], "4")

    def test_missing_defaults_do_not_invent_temperature_or_spin(self):
        data = {}
        settings.select_wash_program(data, "Trainers")
        settings.select_wash_program(data, "Perfect 20")
        payload = command(data)
        self.assertNotIn("TmpTgt", payload)
        self.assertNotIn("SpdTgt", payload)
        self.assertEqual(payload["Sel"], "0")

    def test_explicit_cold_and_no_spin_survive(self):
        data = {}
        settings.select_wash_program(data, "Trainers")
        data.update(wm_temp=0, wm_spin=0)
        self.assertEqual(command(data)["TmpTgt"], "0")
        self.assertEqual(command(data)["SpdTgt"], "0")

    def test_program_default_reuses_recipe_defaults(self):
        data = {}
        settings.select_wash_program(data, "Trainers")
        data.update(wm_temp=None, wm_spin=None)
        self.assertEqual(command(data)["TmpTgt"], "20")
        self.assertEqual(command(data)["SpdTgt"], "4")

    def test_extra_rinse_preserves_other_option_bits(self):
        data = {}
        settings.select_wash_program(data, "Baby Sanitizer")
        data["wm_rinse"] = 3
        self.assertEqual(command(data)["OptMsk"], "66")
        data["wm_rinse"] = 0
        self.assertEqual(command(data)["OptMsk"], "2")

    def test_catalogue_rinse_default_is_retained(self):
        data = {}
        settings.select_wash_program(data, "Shirts")
        self.assertEqual(data["wm_rinse"], 1)
        self.assertEqual(command(data)["OptMsk"], "16")

    def test_rapid_variants_keep_soil_identity(self):
        data = {}
        for name, soil in [("Rapid 44 min", "3"), ("Rapid 30 min", "2"), ("Rapid 14 min", None)]:
            settings.select_wash_program(data, name)
            payload = command(data)
            self.assertEqual(payload["PrNm"], "5")
            self.assertEqual(payload.get("SLevTgt"), soil)

    def test_all_recipes_replace_all_prior_overrides(self):
        self.assertEqual(len(catalogue.WASHING_MACHINE_PROGRAMS), 71)
        for recipe in catalogue.WASHING_MACHINE_PROGRAMS:
            with self.subTest(name=recipe.name):
                clean = {}
                settings.select_wash_program(clean, recipe.name)
                dirty = dict(wm_temp=90, wm_spin=15, wm_soil=3, wm_steam=2, wm_rinse=3)
                settings.select_wash_program(dirty, recipe.name)
                self.assertEqual(command(dirty), command(clean))

    def test_unknown_recipe_leaves_previous_selection_intact(self):
        data = {}
        settings.select_wash_program(data, "Trainers")
        previous = dict(data)
        with self.assertRaises(KeyError):
            settings.select_wash_program(data, "unknown recipe")
        self.assertEqual(data, previous)


if __name__ == "__main__":
    unittest.main()
