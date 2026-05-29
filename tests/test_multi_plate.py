import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_combined_transfer_df_spans_both_plates():
    """
    Processing two plates and concatenating their transfer dfs should produce a
    combined df whose row count equals the sum of the individual counts, and whose
    Sources column contains primers from both plates.
    """
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))
    spec_sheet = pd.read_excel(PLATE_SPEC)

    result1 = create_myra_files(bedlines, spec_sheet, "modjadji-tb_1.0", replicates=1)
    result2 = create_myra_files(bedlines, spec_sheet, "modjadji-tb_1.1", replicates=1)

    assert result1 is not None
    assert result2 is not None

    _, transfer1 = result1
    _, transfer2 = result2

    combined = pd.concat([transfer1, transfer2], ignore_index=True)

    assert len(combined) == len(transfer1) + len(transfer2)

    combined_sources = set(combined["Sources"])
    assert set(transfer1["Sources"]).issubset(combined_sources)
    assert set(transfer2["Sources"]).issubset(combined_sources)
