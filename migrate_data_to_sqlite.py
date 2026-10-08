"""One-time import of data.json, auth.json, and legacy projects into SQLite."""

import argparse
import os

import app


def main():
    parser = argparse.ArgumentParser(
        description="Import existing JSON site data and admin auth into projects.sqlite3."
    )
    parser.add_argument(
        "--directory",
        default=app.BASE_DIR,
        help="Directory containing data.json and auth.json (default: script directory).",
    )
    args = parser.parse_args()

    directory = os.path.abspath(args.directory)
    app.BASE_DIR = directory
    app.DATA_FILE = os.path.join(directory, "data.json")
    app.AUTH_FILE = os.path.join(directory, "auth.json")
    app.PROJECT_DB_FILE = os.path.join(directory, "projects.sqlite3")

    app.migrate_json_to_sqlite()
    projects = app._get_projects()
    data = app._load_app_value("site_data") or {}
    auth = app._load_app_value("admin_auth") or {}

    print(f"SQLite database: {app.PROJECT_DB_FILE}")
    print(f"Imported site data: {'yes' if data else 'no (defaults will be used)'}")
    print(f"Imported admin auth: {'yes' if auth else 'no (credentials will be generated)'}")
    print(f"Projects available: {len(projects)}")
    print("Original JSON files were left unchanged as backups.")


if __name__ == "__main__":
    main()
