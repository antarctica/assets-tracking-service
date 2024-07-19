import os

from pytest_postgresql import factories

"""
Used to setup a PostgreSQL database for testing via pytest-postgresql.

In local development, it's assumed a local postgres instance is available, and so the default 'proc' factory is used.

In CI, it's assumed a remote service providing a postgres instance is available, and so the 'noproc' factory is used.

These factories are defined here for creating a fixture based on the relevant factory name by using:

```
from pytest_postgresql import factories

from tests.utils.postgresql import (  # noqa: F401
    postgresql_proc_factory,
    postgresql_noproc_factory,
    factory_name as postgresql_factory_name,
)

foo = factories.postgresql(postgresql_factory_name)
```

When used in a test (or other fixture), this fixture (`foo` in this example) provides a psycopg.Connection to a
temporary database.
"""

postgresql_proc_factory = factories.postgresql_proc()
postgresql_noproc_factory = factories.postgresql_noproc(
    host=os.environ.get("POSTGRES_HOST"),
    user=os.environ.get("POSTGRES_USER"),
    password=os.environ.get("POSTGRES_PASSWORD"),
    dbname="test",  # pytest-postgresql default
)
factory_name = "postgresql_proc_factory" if "CI" not in os.environ else "postgresql_noproc_factory"
