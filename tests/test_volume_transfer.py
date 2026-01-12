import pytest
import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files, DEFAULT_WEIGHT_UL
from primalbedtools.bedfiles import BedLineParser

# Define paths relative to the test file
TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_volume_transfer_and_presence():
    """
    Test that the correct volume is moved across and all primers
    present in the bedfile and spec sheet are transferred.
    """
    # Load BED file
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))

    # Load Spec Sheet
    spec_sheet = pd.read_excel(PLATE_SPEC)

    # Pick a plate name that exists in the spec sheet
    plate_name = "modjadji-tb_1.0"

    # Define 'x' factor for volume
    x_factor = 2.0
    replicates = 1

    # Run the function
    result = create_myra_files(
        bedlines=bedlines,
        spec_sheet=spec_sheet,
        plate_name=plate_name,
        replicates=replicates,
        volume_multiplier=x_factor
    )

    assert result is not None
    sample_df, transfer_df = result

    # Filter bedlines to get those expected in this plate
    # We need to know which primers are actually in "modjadji-tb_1.0" according to the spec sheet
    plate_df = spec_sheet[spec_sheet["Plate Name"] == plate_name]
    expected_primers = set(plate_df["Sequence Name"].values)

    # Filter bedlines that are in the expected primers
    bed_primers_map = {bl.primername: bl for bl in bedlines}

    # Intersection of primers in BED and primers in Plate Spec
    # These are the ones that SHOULD be in the transfer_df
    expected_transfer_primers = [p for p in expected_primers if p in bed_primers_map]

    # Check if all expected primers are in transfer_df
    transferred_sources = transfer_df["Sources"].tolist()

    # 1. Ensure all primers present in bedfile and spec sheet are transferred
    assert len(transferred_sources) == len(expected_transfer_primers) * replicates

    for primer in expected_transfer_primers:
        assert primer in transferred_sources, (
            f"Primer {primer} should be transferred but is missing."
        )

    # 2. Ensure correct volume is moved across
    # Volume should be bedline.weight * x_factor
    for _, row in transfer_df.iterrows():
        primer_name = row["Sources"]
        transferred_volume = row["Volume"]

        # Find the original bedline
        original_bedline = bed_primers_map[primer_name]
        expected_weight = (
            original_bedline.weight
            if original_bedline.weight is not None
            else DEFAULT_WEIGHT_UL
        )
        expected_volume = expected_weight * x_factor

        # Use approx for float comparison
        assert transferred_volume == pytest.approx(expected_volume), (
            f"Volume mismatch for {primer_name}. Expected {expected_volume}, got {transferred_volume}"
        )
