from airflow import DAG                          # The DAG object
from airflow.operators.bash import BashOperator   # Runs shell commands
from datetime import datetime, timedelta          # For scheduling


# Path to your project (Just so Airflow knows where the scripts are)

PROJECT_DIR = "/Users/nickwyrwas/Desktop/PulseBoard"
VENV_PYTHON = f"{PROJECT_DIR}/venv/bin/python"
VENV_DBT = f"{PROJECT_DIR}/venv/bin/dbt"


default_args = {
    "owner": "nick",
    "retries": 1,

    # Timedelta is used to represent duration. So if something fails within Airflow we wait 5 minutes then retry.
    "retry_delay": timedelta(minutes=5),
}

# Context manager in Python
    # the with keyword is used when working with something that needs to be 
    # properly set up and torn down.
with DAG(
    "pulseBoard_pipeline",              # DAG name (shows up in Airflow UI)
    default_args=default_args,
    description="PulseBoard data pipeline",
    schedule="@hourly",
    start_date=datetime(2026, 3, 24),   # when to start scheduling
    catchup=False,                       # don't backfill past runs
) as dag:
    
    fetch_hn_stories = BashOperator(
        task_id="fetch_hn_stories",
        bash_command=f"{VENV_PYTHON} {PROJECT_DIR}/ingest/hn_fetcher.py",
    )

    
    fetch_news_articles = BashOperator(
        task_id="fetch_news_articles",
        bash_command=f"{VENV_PYTHON} {PROJECT_DIR}/ingest/news_fetcher.py",
    )

    
    run_dbt_models = BashOperator(
        task_id="run_dbt_models",
        bash_command=f"{VENV_DBT} run --project-dir {PROJECT_DIR}/pulseBoard",
    )

    # Set the order: each task waits for the previous one
    # Operator overloading
        # with airflow it means this task must run before the next task
        # if one fails the whole chain stops

        # >> - rightshift bitwise operator
    fetch_hn_stories >> fetch_news_articles >> run_dbt_models