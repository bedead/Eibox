from enum import Enum

from pydantic import BaseModel


class Status(Enum):
    RUNNING = 0
    STOPED = 1
    PAUSED = 2


class GmailToolKitManager(BaseModel):
    status: Status = Status.STOPED

    def start(self) -> None:
        self.status = Status.RUNNING

    def stop(self) -> None:
        self.status = Status.STOPED

    def pause(self) -> None:
        self.status = Status.PAUSED

    def is_running(self) -> bool:
        return self.status == Status.RUNNING
