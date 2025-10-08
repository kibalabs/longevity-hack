from core.store.database import Database


class ResourceBuilderV1:
    def __init__(self, database: Database) -> None:
        self.database = database

    # @cached(ttl=(60 * 60))  # type: ignore[misc]
    # async def _get_user(self, userId: str) -> resources.User:  # type: ignore[misc]
    #     async with self.database.create_transaction() as connection:
    #         user = await schema.UsersRepository.get_one(
    #             database=self.database,
    #             connection=connection,
    #             fieldFilters=[UUIDFieldFilter(fieldName=schema.UsersTable.c.userId.key, eq=userId)],
    #         )
    #     return resources.User(
    #         userId=user.userId,
    #         createdDate=user.createdDate,
    #         username=user.username,
    #         name=user.name,
    #     )

    # async def build_user(self, user: User) -> resources.User:
    #     return resources.User(
    #         userId=user.userId,
    #         createdDate=user.createdDate,
    #         username=user.username,
    #         name=user.name,
    #     )
