from core.store.database import Database


class AppManager:
    def __init__(self, database: Database) -> None:
        self.database = database
