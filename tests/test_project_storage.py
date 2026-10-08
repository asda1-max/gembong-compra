import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app as site


class ProjectStorageTests(unittest.TestCase):
    def test_legacy_json_projects_migrate_once_to_sqlite(self):
        legacy_projects = [{
            "name": "Legacy Project",
            "description": "Migrated project",
            "tech_stack": ["Python"],
        }]
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "projects.sqlite3")
            with patch.object(site, "PROJECT_DB_FILE", db_path), patch.object(
                site, "load_data", return_value={"projects": legacy_projects}
            ):
                projects = site._get_projects()
                self.assertEqual(projects[0]["name"], "Legacy Project")
                self.assertEqual(projects[0]["type"], "Software")
                self.assertEqual(projects[0]["banner"], "")

                connection = sqlite3.connect(db_path)
                count = connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
                marker = connection.execute(
                    "SELECT value FROM app_meta WHERE key = 'projects_migrated'"
                ).fetchone()[0]
                connection.close()
                self.assertEqual(count, 1)
                self.assertEqual(marker, "1")


if __name__ == "__main__":
    unittest.main()
