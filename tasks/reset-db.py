import psycopg


def main() -> None:
    """Script entrypoint."""
    dsn_base = "postgres://localhost"
    neutral_db = "postgres"
    dev_db = "assets_tracking_dev"
    test_db = "assets_tracking_test"

    with psycopg.connect(f"{dsn_base}/{neutral_db}", autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("DROP DATABASE IF EXISTS assets_tracking_dev;")
        cur.execute("DROP DATABASE IF EXISTS assets_tracking_test;")

        cur.execute("CREATE DATABASE assets_tracking_dev OWNER assets_tracking_owner;")
        cur.execute("CREATE DATABASE assets_tracking_test OWNER assets_tracking_owner;")

    for db in [dev_db, test_db]:
        with psycopg.connect(f"{dsn_base}/{db}") as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")


if __name__ == "__main__":
    main()
