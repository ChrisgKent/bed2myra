import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_invalid_plate_returns_none():
    """create_myra_files returns None when the requested plate name is not in the spec sheet."""
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))
    spec_sheet = pd.read_excel(PLATE_SPEC)

    result = create_myra_files(
        bedlines=bedlines,
        spec_sheet=spec_sheet,
        plate_name="this_plate_does_not_exist",
        replicates=1,
    )

    assert result is None
