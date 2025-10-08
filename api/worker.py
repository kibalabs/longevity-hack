import asyncio
import os

from core import logging
from core.queues.message_queue_processor import MessageQueueProcessor
from core.util.value_holder import RequestIdHolder

from longevity.app_message_processor import AppMessageProcessor
from longevity.create_agent_manager import create_app_manager

name = os.environ.get('NAME', 'yieldseeker-worker')
version = os.environ.get('VERSION', 'local')
environment = os.environ.get('ENV', 'dev')
isRunningDebugMode = environment == 'dev'

requestIdHolder = RequestIdHolder()
if isRunningDebugMode:
    logging.init_basic_logging()
else:
    logging.init_json_logging(name=name, version=version, environment=environment, requestIdHolder=requestIdHolder)
logging.init_external_loggers(loggerNames=['httpx'])


async def main() -> None:
    appManager = create_app_manager()
    messageProcessor = AppMessageProcessor(
        appManager=appManager,
        database=appManager.database,
    )
    workQueueProcessor = MessageQueueProcessor(
        queue=appManager.workQueue,
        messageProcessor=messageProcessor,
        requestIdHolder=requestIdHolder,
        notificationClients=[],
    )

    await appManager.workQueue.connect()
    await appManager.database.connect(poolSize=2)
    try:
        await workQueueProcessor.run()
    finally:
        await appManager.database.disconnect()
        await appManager.workQueue.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
