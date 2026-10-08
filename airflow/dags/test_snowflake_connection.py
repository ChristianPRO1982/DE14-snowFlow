import pendulum

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import dag, task


CONN_ID = "snowflake_nyc_taxi"


@dag(
    dag_id="test_snowflake_connection",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
)
def test_snowflake_connection():

    @task
    def check_connection() -> None:
        hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

        result = hook.get_first(
            """
            SELECT
                CURRENT_USER(),
                CURRENT_ROLE(),
                CURRENT_WAREHOUSE(),
                CURRENT_DATABASE(),
                CURRENT_SCHEMA()
            """
        )

        print(result)

    check_connection()


test_snowflake_connection()
