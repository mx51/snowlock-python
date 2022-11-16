# snowlock-python

[![Github Actions](https://github.com/mx51/snowlock-python/actions/workflows/master.yml/badge.svg)](https://github.com/mx51/snowlock-python/actions/workflows/master.yml)
[![PyPI](https://img.shields.io/pypi/v/snowlock)](https://pypi.org/project/snowlock/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/mx51/snowlock-python/blob/master/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Lock management library for Snowflake.

## Requirements
---
Requires Python 3.6 or above.
## Usage
---
You can install snowlock from [PyPI](https://pypi.org/project/snowlock/):
```bash
pip install snowlock
```

To acquire a lock using a Snowflake table. The lock table will be created if it does not exist and will default to using a table called `LOCK`.
```py
import os
import snowflake.connector as sc

from snowlock.lock import lock

connection = sc.connect(
    account = os.getenv("SNOWFLAKE_ACCOUNT"),
    user = os.getenv("SNOWFLAKE_USER"),
    password = os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE"),
    database = os.getenv("SNOWFLAKE_DATABASE"),
    schema = os.getenv("SNOWFLAKE_SCHEMA"),
    **kwargs,
)

with lock(client="test", resource="test", conn=connection, table="LOCK") as session:
    ## Do something using the locked resource

```

## Code of Conduct
---
All contributors are expected to follow the [PyPA Code of Conduct](https://www.pypa.io/en/latest/code-of-conduct/).