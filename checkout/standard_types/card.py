import enum

PCI_TLL_CARD_DATA_TTL_IN_SECONDS = 60 * 60 * 24 * 365 * 2  # 2 years in seconds
_LAST_DIGITS: int = 4


class Franchise(enum.Enum):
    VISA = "VISA"
    MASTER_CARD = "VISA"


class PAN:
    @staticmethod
    def mask(pan: str, bin_len: int = 6) -> str:
        return pan[:bin_len] + "*" * (len(pan) - bin_len - _LAST_DIGITS) + pan[-_LAST_DIGITS:]
