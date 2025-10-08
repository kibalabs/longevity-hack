from core.queues.sqs import SqsMessageQueue
from core.store.database import Database


class AppManager:
    def __init__(self, database: Database, workQueue: SqsMessageQueue) -> None:
        self.database = database
        self.workQueue = workQueue
