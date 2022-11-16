import contextlib
from uuid import uuid4, UUID
from typing import Iterator
from logging import getLogger
from snowflake.connector import SnowflakeConnection

from .utils import execute_query, execute_statement

logger = getLogger(__name__)


@contextlib.contextmanager
def lock(
    client: str, resource: str, conn: SnowflakeConnection, table: str = "LOCK"
) -> Iterator[UUID]:
    """Creates a lock using a Snowflake table.

    Args:
        client (str): The client requesting the lock.
        resource (str): The resource to lock.
        conn (SnowflakeConnection): The Snowflake connection to use.
        table (str, optional): The table to use for locking, it will be created if it does not exist. Defaults to "LOCK".

    Yields:
        Iterator[str]: The session id of the lock.
    """
    session_id = uuid4()
    try:
        execute_statement(
            conn=conn,
            sql=f"""
                CREATE TABLE "{table}" IF NOT EXISTS (
                    "CLIENT" VARCHAR(1000),
                    "RESOURCE" VARCHAR(1000),
                    "SESSION_ID" VARCHAR(1000),
                    "ACQUIRED" BOOLEAN,
                    "ACQUIRED_TS" TIMESTAMP_LTZ(9),
                    PRIMARY KEY("CLIENT","RESOURCE")
                )
                DATA_RETENTION_TIME_IN_DAYS=0
                CHANGE_TRACKING=FALSE
            """,
        )

        logger.info("attempting to acquire lock on %s for %s", resource, client)
        execute_statement(
            conn=conn,
            sql=f"""
                INSERT INTO {table} WITH L AS (
                    SELECT
                    '{client}' AS CLIENT,
                    '{resource}' AS RESOURCE,
                    '{session_id}' AS SESSION_ID,
                    'TRUE' AS ACQUIRED,
                    CURRENT_TIMESTAMP() AS ACQUIRED_TS
                )
                SELECT * FROM L
                WHERE NOT EXISTS (SELECT * FROM {table} WHERE L.RESOURCE = {table}.RESOURCE AND {table}.ACQUIRED = 'TRUE' AND L.CLIENT != {table}.CLIENT)
            """,
        )

        row = execute_query(
            conn=conn,
            sql=f"""
                SELECT 
                    CLIENT
                FROM {table} 
                WHERE ACQUIRED='TRUE'
                QUALIFY ROW_NUMBER() OVER (PARTITION BY RESOURCE ORDER BY ACQUIRED_TS, SESSION_ID) = 1
            """,
        )

        if row:
            in_use_client = row[0].get("CLIENT")

            if in_use_client != client:
                logger.warning(
                    "%s is in use by %s, could not acquire lock for %s",
                    resource,
                    in_use_client,
                    client,
                )
                execute_statement(
                    conn=conn,
                    sql=f"""
                    DELETE 
                    FROM {table}
                    WHERE SESSION_ID='{session_id}'
                    """,
                )
                return
        yield session_id
    finally:
        logger.info("releasing locks for %s", session_id)
        execute_query(
            conn=conn,
            sql=f"""
            UPDATE {table}
            SET ACQUIRED='FALSE'
            WHERE SESSION_ID='{session_id}'
            """,
        )
