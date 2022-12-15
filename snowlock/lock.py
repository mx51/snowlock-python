import contextlib
from uuid import uuid4
from typing import Iterator
from logging import getLogger
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import ProgrammingError

from .utils import execute_query, execute_statement

MAX_RETRIES = 2
logger = getLogger(__name__)


@contextlib.contextmanager
def lock(
    client: str,
    resource: str,
    conn: SnowflakeConnection,
    table: str = "lock",
    session_lock: bool = False,
) -> Iterator[str]:
    """Creates a lock using a Snowflake table.

    Args:
        client (str): The client requesting the lock.
        resource (str): The resource to lock.
        conn (SnowflakeConnection): The Snowflake connection to use.
        table (str, optional): The table to use for locking, it will be created if it does not exist. Defaults to "lock".
        session_lock (bool, optional): Whether to prevent different sessions of the same client acquiring the lock. Defaults to False.

    Yields:
        Iterator[str]: The session id of the lock.
    """
    session_id = str(uuid4())
    lock_acquired = False
    retry_attempt = 0

    while retry_attempt < MAX_RETRIES:
        try:
            logger.info("Attempting to acquire lock on %s for %s", resource, client)
            execute_statement(
                conn=conn,
                sql=f"""
                    merge into {table} using (
                        select
                        '{client}' as client,
                        '{resource}' as resource,
                        '{session_id}' as session_id,
                        {session_lock} as session_locked
                    ) as s on s.resource = lock.resource
                    when not matched then insert (client, resource, acquired, session_id, session_locked) values (s.client, s.resource, true, s.session_id, s.session_locked)
                    when matched and lock.acquired=false or (lock.client = s.client and s.session_locked = false) then update set
                        lock.client=s.client,
                        lock.acquired=true,
                        lock.session_id=s.session_id,
                        lock.session_locked=s.session_locked;
                """,
            )

            row = execute_query(
                conn=conn,
                sql=f"""
                    select 
                        client,
                        session_id
                    from {table}
                    where resource='{resource}'
                """,
            )

            if row:
                in_use_client = row[0].get("CLIENT")
                if in_use_client != client:
                    raise ResourceLockedException(
                        f"{resource} is in use by {in_use_client}, could not acquire lock for {client}"
                    )

                if session_lock and row[0].get("SESSION_ID") != session_id:
                    raise ResourceLockedException(
                        f"{resource} is in use by another session of {client}, could not acquire lock"
                    )

            lock_acquired = True
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
                        acquired boolean,
                        session_id varchar,
                        session_locked boolean,
                        primary key(client,resource)
                    )
                    data_retention_time_in_days=0
                    change_tracking=false
                """,
            )
            logger.info("Created lock table %s and retrying", table)
        finally:
            if lock_acquired:
                logger.info("Releasing lock for %s", resource)
                execute_query(
                    conn=conn,
                    sql=f"""
                    update {table}
                    set acquired=false
                    where resource='{resource}'
                    """,
                )
                retry_attempt = MAX_RETRIES


class ResourceLockedException(Exception):
    """Exception raised when a resource is locked."""
