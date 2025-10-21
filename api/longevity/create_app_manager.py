import os

from core.notifications.discord_client import DiscordClient
from core.queues.sqs import SqsMessageQueue
from core.requester import Requester
from core.store.database import Database

from longevity.app_manager import AppManager


async def create_database() -> Database:
    """Create a database connection instance."""
    database = Database(
        connectionString=Database.create_psql_connection_string(
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT'],
            name=os.environ['DB_NAME'],
            username=os.environ['DB_USERNAME'],
            password=os.environ['DB_PASSWORD'],
        )
    )
    await database.connect()
    return database


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
        accessKeySecret=os.environ['AWS_ACCESS_KEY_SECRET'],
        queueUrl=os.environ['AWS_SQS_WORK_QUEUE_URL'],
    )
    requester = Requester()
    adminNotificationClient = DiscordClient(
        requester=requester,
        webhookUrl=os.environ['DISCORD_WEBHOOK_URL'],
    )
    appManager = AppManager(
        database=database,
        requester=requester,
        workQueue=workQueue,
        adminNotificationClient=adminNotificationClient,
    )
    return appManager
