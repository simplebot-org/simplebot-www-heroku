import os
import subprocess
from tempfile import TemporaryDirectory

import psycopg2


def set_key(keydata: str) -> None:
    with TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "private-key.asc")
        with open(path, "w") as keyfile:
            keyfile.write(keydata)
        subprocess.run(["simplebot", "-a", os.environ["ADDR"], "import", tempdir])


def get_key() -> str:
    with TemporaryDirectory() as tempdir:
        subprocess.run(["simplebot", "-a", os.environ["ADDR"], "export", "-k", tempdir])
        for name in os.listdir(tempdir):
            if "private" in name:
                with open(os.path.join(tempdir, name)) as keyfile:
                    return keyfile.read()
    raise ValueError("invalid key data")


if __name__ == "__main__":
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE config (key varchar(250) PRIMARY KEY, value varchar);"
                )
                cur.execute(
                    "INSERT INTO config (key, value) VALUES (%s, %s)",
                    ("private_key", get_key()),
                )
    except Exception:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT value FROM config WHERE key = %s;", ("private_key",)
                )
                set_key(cur.fetchone()[0])
    finally:
        conn.close()
