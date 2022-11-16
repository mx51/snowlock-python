import contextlib
from uuid import uuid4, UUID
from typing import Iterator
from logging import getLogger
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import ProgrammingError

from .utils import execute_query, execute_statement

MAX_RETRIES = 2
logger = getLogger(__name__)


@contextlib.contextmanager
def lock(
    client: str, resource: str, conn: SnowflakeConnection, table: str = "lock"
) -> Iterator[UUID]:
    """Creates a lock using a Snowflake table.

    Args:
        client (str): The client requesting the lock.
        resource (str): The resource to lock.
        conn (SnowflakeConnection): The Snowflake connection to use.
        table (str, optional): The table to use for locking, it will be created if it does not exist. Defaults to "lock".

    Yields:
        Iterator[UUID]: The session id of the lock.
    """
    session_id = uuid4()
    success = False
    retry_attempt = 0

    while retry_attempt < MAX_RETRIES:
        try:
            logger.info("Attempting to acquire lock on %s for %s", resource, client)
            execute_statement(
                conn=conn,
                sql=f"""
                    insert into {table} with l as (
                        select
                        '{client}' as client,
                        '{resource}' as resource,
                        '{session_id}' as session_id,
                        true as acquired,
                        current_timestamp() as acquired_ts
                    )
                    select * from l
                    where not exists (select * from {table} where l.resource = {table}.resource and {table}.acquired = true and l.client != {table}.client)
                """,
            )

            row = execute_query(
                conn=conn,
                sql=f"""
                    select 
                        client
                    from {table} 
                    where acquired=true
                    qualify row_number() over (partition by resource order by acquired_ts, session_id) = 1
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
                        delete 
                        from {table}
                        where session_id='{session_id}'
                        """,
                    )
                    return
            yield session_id
        except ProgrammingError as e:
            table_not_exists = (
                f"Object '{table.upper()}' does not exist or not authorized."
            )
            if not e.msg or not table_not_exists in e.msg:
                raise e

            logger.warning(e.msg)
            execute_statement(
                conn=conn,
                sql=f"""
                    create table {table} if not exists (
                        client varchar,
                        resource varchar,
                        session_id varchar,
                        acquired boolean,
                        acquired_ts timestamp_ltz,
                        primary key(client,resource)
                    )
                    data_retention_time_in_days=0
                    change_tracking=false
                """,
            )
            logger.info("Created lock table %s and retrying", table)
        else:
            success = True
        finally:
            if success:
                logger.info("Releasing locks for %s", session_id)
                execute_query(
                    conn=conn,
                    sql=f"""
                    update {table}
                    set acquired=false
                    where session_id='{session_id}'
                    """,
                )
                retry_attempt = MAX_RETRIES
