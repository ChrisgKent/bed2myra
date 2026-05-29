import logging
import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_small_volume_warning(caplog):
    """
    Primers with weight between 1.0 and 2.0 µL (at x_factor=1.0) should trigger
    a WARNING but not raise an exception.
    """
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))
    spec_sheet = pd.read_excel(PLATE_SPEC)

    with caplog.at_level(logging.WARNING, logger="bed2myra.main"):
        result = create_myra_files(
            bedlines=bedlines,
            spec_sheet=spec_sheet,
            plate_name="modjadji-tb_1.0",
            replicates=1,
            volume_multiplier=1.0,
        )

    assert result is not None, "Function should succeed despite small-volume warnings"

    warning_messages = [
        r.message for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert any(
        "Small volume detected" in m for m in warning_messages
    ), "Expected at least one small-volume warning for primers with weight < 2 µL"
