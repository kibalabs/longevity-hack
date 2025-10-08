from core.exceptions import KibaException
from core.queues.message_queue_processor import MessageProcessor
from core.queues.model import Message
from core.store.database import Database

from logenvity.app_manager import AppManager

# from logenvity.messages import ExampleMessageContent


class AppMessageProcessor(MessageProcessor):
    def __init__(self, appManager: AppManager, database: Database) -> None:
        self.appManager = appManager
        self.database = database

    async def process_message(self, message: Message) -> None:
        async with self.database.create_context_connection():
            # Example message processing pattern:
            # if message.command == ExampleMessageContent.get_command():
            #     exampleMessageContent = ExampleMessageContent.model_validate(message.content)
            #     await self.appManager.handle_example_message(data=exampleMessageContent.data)
            #     return

            # Handle unknown messages
            raise KibaException(message='Message was unhandled')
