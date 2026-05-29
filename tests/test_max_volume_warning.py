import logging
import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files

TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_large_volume_warning(caplog):
    """
    Primers whose volume exceeds MAX_VOLUME_UL should trigger a WARNING and still
    be written to the transfer file (no exception raised).
    """
    from primalbedtools.bedfiles import BedLineParser

    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))
    spec_sheet = pd.read_excel(PLATE_SPEC)

    # multiplier=10 pushes primers with weight > 5 µL above MAX_VOLUME_UL (50 µL)
    with caplog.at_level(logging.WARNING, logger="bed2myra.main"):
        result = create_myra_files(
            bedlines=bedlines,
            spec_sheet=spec_sheet,
            plate_name="modjadji-tb_1.0",
            replicates=1,
            volume_multiplier=10.0,
        )

    assert result is not None, "Function should succeed despite large-volume warnings"

    warning_messages = [
        r.message for r in caplog.records if r.levelno == logging.WARNING
    ]
    assert any(
        "multiple tips" in m for m in warning_messages
    ), "Expected at least one large-volume warning for primers with volume > MAX_VOLUME_UL"

    _, transfer_df = result
    assert len(transfer_df) > 0, "Transfer df should still contain rows"
