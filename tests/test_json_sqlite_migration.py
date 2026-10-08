import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import app as site


class JsonSqliteMigrationTests(unittest.TestCase):
    def test_data_and_auth_json_are_imported_without_being_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            data_path = os.path.join(directory, "data.json")
            auth_path = os.path.join(directory, "auth.json")
            db_path = os.path.join(directory, "projects.sqlite3")
            with open(data_path, "w", encoding="utf-8") as stream:
                json.dump({"theme": "modern", "projects": []}, stream)
            with open(auth_path, "w", encoding="utf-8") as stream:
                json.dump({"username": "operator", "password_hash": "hash"}, stream)

            with patch.object(site, "DATA_FILE", data_path), patch.object(
                site, "AUTH_FILE", auth_path
            ), patch.object(site, "PROJECT_DB_FILE", db_path):
                site.migrate_json_to_sqlite()
                self.assertEqual(site._load_app_value("site_data")["theme"], "modern")
                self.assertEqual(
                    site._load_app_value("admin_auth")["username"], "operator"
                )

            self.assertTrue(os.path.isfile(data_path))
            self.assertTrue(os.path.isfile(auth_path))
            connection = sqlite3.connect(db_path)
            keys = {
                row[0] for row in connection.execute("SELECT key FROM app_data")
            }
            connection.close()
            self.assertEqual(keys, {"site_data", "admin_auth"})


if __name__ == "__main__":
    unittest.main()
