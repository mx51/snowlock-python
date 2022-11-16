import contextlib
from typing import Iterator, Optional
from snowflake.connector import SnowflakeConnection, DictCursor
from snowflake.connector.cursor import SnowflakeCursor


@contextlib.contextmanager
def cursor(conn: SnowflakeConnection) -> Iterator[SnowflakeCursor]:
    """Initialize Snowflake cursor.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.

    Yields:
        Snowflake dictionary cursor generator.
    """
    try:
        dict_cursor = conn.cursor(DictCursor)
        yield dict_cursor
    finally:
        dict_cursor.close()


def execute_statement(conn: SnowflakeConnection, sql: str, **kwargs):
    """Pass statement to Snowflake to execute.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.
        sql (str): The Snowflake SQL statement to execute.
    """
    with cursor(conn) as cur:
        cur.execute(sql, **kwargs)


def execute_query(conn: SnowflakeConnection, sql: str, **kwargs) -> Optional[list]:
    """Pass SQL to Snowflake and return the result as a dictionary.

    Args:
        conn (sc.SnowflakeConnection): A Snowflake connection.
        sql: The Snowflake SQL to execute.
    Returns:
        A list of dictionaries representing the results of the query, or None if some error happened.
    """
    with cursor(conn) as cur:
        res = cur.execute(sql, **kwargs)
        if not res:
            return None
        return res.fetchall()
