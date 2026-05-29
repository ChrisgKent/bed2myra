import pandas as pd
import pytest
from types import SimpleNamespace
from bed2myra.main import create_myra_files, DEFAULT_WEIGHT_UL


def test_default_weight_used_when_weight_is_none():
    """
    A primer with weight=None should use DEFAULT_WEIGHT_UL for its transfer volume.
    """
    bedlines = [SimpleNamespace(primername="primer_A", weight=None)]
    spec_sheet = pd.DataFrame(
        {
            "Plate Name": ["plate_1"],
            "Well Position": ["A01"],
            "Sequence Name": ["primer_A"],
        }
    )

    result = create_myra_files(
        bedlines=bedlines,
        spec_sheet=spec_sheet,
        plate_name="plate_1",
        replicates=1,
        volume_multiplier=1.0,
    )

    assert result is not None
    _, transfer_df = result
    assert len(transfer_df) == 1
    assert transfer_df.iloc[0]["Volume"] == pytest.approx(DEFAULT_WEIGHT_UL * 1.0)


def test_default_weight_respects_volume_multiplier():
    """DEFAULT_WEIGHT_UL is scaled by volume_multiplier like any other weight."""
    bedlines = [SimpleNamespace(primername="primer_A", weight=None)]
    spec_sheet = pd.DataFrame(
        {
            "Plate Name": ["plate_1"],
            "Well Position": ["A01"],
            "Sequence Name": ["primer_A"],
        }
    )

    result = create_myra_files(
        bedlines=bedlines,
        spec_sheet=spec_sheet,
        plate_name="plate_1",
        replicates=1,
        volume_multiplier=3.0,
    )

    assert result is not None
    _, transfer_df = result
    assert transfer_df.iloc[0]["Volume"] == pytest.approx(DEFAULT_WEIGHT_UL * 3.0)
