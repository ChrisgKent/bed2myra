import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

# Define paths relative to the test file
TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_replicates_functionality():
    """
    Test that the replicates parameter correctly creates identical output tubes
    in different wells in the transfer file.
    """
    # Load BED file
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))

    # Load Spec Sheet
    spec_sheet = pd.read_excel(PLATE_SPEC)

    # Configuration for the test
    plate_name = "modjadji-tb_1.0"
    replicates = 3
    x_factor = 1.0

    # Run the function
    result = create_myra_files(
        bedlines=bedlines,
        spec_sheet=spec_sheet,
        plate_name=plate_name,
        replicates=replicates,
        x=x_factor,
    )

    assert result is not None
    _, transfer_df = result

    # Identify unique primers that should be in the transfer file
    plate_df = spec_sheet[spec_sheet["Plate Name"] == plate_name]
    expected_primer_names = [
        bl.primername
        for bl in bedlines
        if bl.primername in plate_df["Sequence Name"].values
    ]
    num_unique_primers = len(expected_primer_names)

    # 1. Check total number of rows in transfer_df
    # Each primer should be repeated 'replicates' times
    expected_total_rows = num_unique_primers * replicates
    assert len(transfer_df) == expected_total_rows, (
        f"Expected {expected_total_rows} rows, got {len(transfer_df)}"
    )

    # 2. Check that we have the correct wells (1, 2, 3)
    unique_wells = sorted(transfer_df["Well"].unique())
    assert unique_wells == [1, 2, 3], f"Expected wells [1, 2, 3], got {unique_wells}"

    # 3. Check that each well contains the same set of primers
    well_1_primers = sorted(transfer_df[transfer_df["Well"] == 1]["Sources"].tolist())
    well_2_primers = sorted(transfer_df[transfer_df["Well"] == 2]["Sources"].tolist())
    well_3_primers = sorted(transfer_df[transfer_df["Well"] == 3]["Sources"].tolist())

    assert well_1_primers == well_2_primers == well_3_primers, (
        "Primers in replicates are not identical"
    )
    assert len(well_1_primers) == num_unique_primers

    # 4. Check that volumes are identical across replicates for the same primer
    for primer in expected_primer_names:
        volumes = transfer_df[transfer_df["Sources"] == primer]["Volume"].tolist()
        assert len(volumes) == replicates
        assert all(v == volumes[0] for v in volumes), (
            f"Volumes for primer {primer} differ across replicates"
        )
