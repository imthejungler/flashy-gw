import time
import uuid


class IDGenerator:
    @staticmethod
    def hex_uuid() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def str_uuid() -> str:
        return str(uuid.uuid4())


def time_ns() -> int:
    return time.time_ns()
