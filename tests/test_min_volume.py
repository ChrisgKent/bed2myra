import pytest
import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

# Define paths relative to the test file
TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_minimum_volume_enforcement():
    """
    Test that the volume in the transfer file is never less than MIN_VOLUME_UL,
    even if the calculated volume (weight * x) is smaller.
    """
    # Load BED file
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))

    # Load Spec Sheet
    spec_sheet = pd.read_excel(PLATE_SPEC)

    # Configuration: use a very small x factor to force volumes below MIN_VOLUME_UL
    plate_name = "modjadji-tb_1.0"
    x_factor = 0.01

    # Run the function and expect a ValueError
    with pytest.raises(ValueError, match="is less than MIN_VOLUME_UL"):
        create_myra_files(
            bedlines=bedlines,
            spec_sheet=spec_sheet,
            plate_name=plate_name,
            replicates=1,
            volume_multiplier=x_factor
        )
