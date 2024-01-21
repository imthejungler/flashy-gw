import uuid


class IDGenerator:
    @staticmethod
    def uuid(prefix: str = "") -> str:
        return f"{prefix}{uuid.uuid4().hex}"
