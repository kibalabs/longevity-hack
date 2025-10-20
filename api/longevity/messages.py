from core.queues.model import MessageContent


class AnalyzeGenomeMessageContent(MessageContent):
    _COMMAND = 'ANALYZE_GENOME'
    genomeAnalysisId: str
    filePath: str
