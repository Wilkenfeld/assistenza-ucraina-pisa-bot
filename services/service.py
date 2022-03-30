from abc import abstractmethod, ABC

from telegram.ext import Handler

from db.db import DB


class Service(ABC):

    def __init__(self, db: DB = None, *args, **kwargs):
        self.db: DB = db

    # Called when registering the handlers
    # Returns a handler (or a list of handlers) to be registered
    @abstractmethod
    def register(self) -> Handler | [Handler]:
        pass
