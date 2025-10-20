from core.exceptions import KibaException
from core.queues.message_queue_processor import MessageProcessor
from core.queues.model import Message
from core.store.database import Database

from longevity.app_manager import AppManager
from longevity.messages import AnalyzeGenomeMessageContent


class AppMessageProcessor(MessageProcessor):
    def __init__(self, appManager: AppManager, database: Database) -> None:
        self.appManager = appManager
        self.database = database

    async def process_message(self, message: Message) -> None:
        async with self.database.create_context_connection():
            if message.command == AnalyzeGenomeMessageContent.get_command():
                analyzeGenomeMessageContent = AnalyzeGenomeMessageContent.model_validate(message.content)
                await self.appManager.run_genome_analysis(
                    genomeAnalysisId=analyzeGenomeMessageContent.genomeAnalysisId,
                    inputFilePath=analyzeGenomeMessageContent.filePath,
                )
                return
            # Handle unknown messages
            raise KibaException(message='Message was unhandled')
