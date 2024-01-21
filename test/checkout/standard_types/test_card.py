import pytest

from checkout.standard_types import card


@pytest.mark.parametrize(
    "pan, bin_len, expected_masked_pan",
    [("6666660000004444", 6, "666666******4444"),
     ("666666000004444", 6, "666666*****4444"),
     ("6666660000000004444", 6, "666666*********4444"), ])
def test_should_mask_the_pan_leaving_six_and_four_numbers_in_the_card_when_the_bin_is_six_digits(
        pan: str, bin_len: int, expected_masked_pan: str
) -> None:
    masked_pan = card.PAN.mask(pan=pan)
    assert masked_pan == expected_masked_pan


@pytest.mark.parametrize(
    "pan, bin_len, expected_masked_pan",
    [("8888888800004444", 8, "88888888****4444"),
     ("888888880004444", 8, "88888888***4444"),
     ("8888888800000004444", 8, "88888888*******4444"), ])
def test_should_mask_the_pan_leaving_eight_and_four_numbers_in_the_card_when_the_bin_is_eight_digits(
        pan: str, bin_len: int, expected_masked_pan: str
) -> None:
    masked_pan = card.PAN.mask(pan=pan, bin_len=bin_len)
    assert masked_pan == expected_masked_pan
