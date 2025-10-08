import os

from core.queues.sqs import SqsMessageQueue
from core.store.database import Database

from longevity.app_manager import AppManager


def create_app_manager() -> AppManager:
    database = Database(
        connectionString=Database.create_psql_connection_string(
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT'],
            name=os.environ['DB_NAME'],
            username=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD'],
        )
    )

    workQueue = SqsMessageQueue(
        region=os.environ['AWS_REGION'],
        accessKeyId=os.environ['AWS_ACCESS_KEY_ID'],
        accessKeySecret=os.environ['AWS_SECRET_ACCESS_KEY'],
        queueUrl=os.environ['SQS_QUEUE_URL'],
    )
    appManager = AppManager(
        database=database,
        workQueue=workQueue,
    )
    return appManager
