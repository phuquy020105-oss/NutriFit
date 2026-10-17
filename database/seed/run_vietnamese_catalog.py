"""Future authorized import into a disposable MySQL test DB; NOT an application migration."""
import argparse
from pathlib import Path
import re
import runpy
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, help="Existing disposable DB, name ending _test")
    parser.add_argument("--login-path", required=True, help="mysql_config_editor profile; no password argument")
    parser.add_argument("--mysql", default="mysql.exe", help="Path to the official MySQL 8+ batch client")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,58}_test", args.database):
        parser.error("Database must be ASCII, at most 64 characters, and end with _test")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", args.login_path):
        parser.error("Login path must contain only ASCII letters, digits, underscore or hyphen")
    seed = Path(__file__).resolve().parent
    # run_path avoids generating __pycache__; validation is read-only and must pass first.
    validator = runpy.run_path(str(seed / "validate_vietnamese_catalog.py"))
    validator["validate"]()
    sql = "\n".join((seed / filename).read_text(encoding="utf-8") for filename in (
        "vietnamese_foods.sql", "vietnamese_recipes.sql", "vietnamese_recipe_ingredients.sql"))
    command = [args.mysql, "--no-defaults", "--login-path=" + args.login_path,
               "--database=" + args.database, "--batch", "--raw", "--default-character-set=utf8mb4",
               "--skip-force", "--skip-reconnect", "--local-infile=0", "--binary-mode"]
    print(f"Import target: {args.database}; three files, one client session/transaction.", flush=True)
    result = subprocess.run(command, input=sql.encode("utf-8"), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False, check=False)
    sys.stdout.write(result.stdout.decode("utf-8", errors="replace"))
    sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
    if result.returncode:
        print("IMPORT FAILED. Before COMMIT, disconnection rolls back InnoDB row changes. "
              "If connection/output failed around COMMIT, verify outcome before retrying. "
              "No cleanup or retry was attempted.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"IMPORT STOPPED: {error}", file=sys.stderr)
        raise SystemExit(1)
