import pandas as pd
from pathlib import Path
from bed2myra.main import create_myra_files
from primalbedtools.bedfiles import BedLineParser

# Define paths relative to the test file
TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"


def test_well_location_mapping():
    """
    Test that the location (Well Position) of each primer in the spec sheet
    is correctly passed into the 'Well' column of the sample plate output.
    """
    # Load BED file
    _, bedlines = BedLineParser.from_file(str(PRIMER_BED))

    # Load Spec Sheet
    spec_sheet = pd.read_excel(PLATE_SPEC)

    # Pick a plate name that exists in the spec sheet
    plate_name = "modjadji-tb_1.0"

    # Run the function
    result = create_myra_files(
        bedlines=bedlines, spec_sheet=spec_sheet, plate_name=plate_name, replicates=1
    )

    assert result is not None
    sample_df, _ = result

    # Get the ground truth from the spec sheet for this plate
    plate_df = spec_sheet[spec_sheet["Plate Name"] == plate_name]

    # Create a mapping of Sequence Name -> Well Position from the source spec sheet
    # Note: spec sheet has columns "Sequence Name" and "Well Position"
    expected_wells = dict(zip(plate_df["Sequence Name"], plate_df["Well Position"]))

    # Check each row in the sample_df
    # sample_df has renamed columns: "Well" (was Well Position) and "Source Name" (was Sequence Name)
    for _, row in sample_df.iterrows():
        primer_name = row["Source Name"]
        assigned_well = row["Well"]

        # Ensure the primer is actually expected
        assert primer_name in expected_wells, (
            f"Primer {primer_name} found in output but not in spec sheet for {plate_name}"
        )

        # Verify the well matches the original spec sheet well position
        expected_well = expected_wells[primer_name]
        assert assigned_well == expected_well, (
            f"Well mismatch for {primer_name}. Expected {expected_well}, got {assigned_well}"
        )

    # Also verify that we didn't miss any primers (count check)
    # Note: create_myra_files filters by bedlines, so only primers present in BOTH bedfile and spec sheet appear.
    # However, sample_df is derived directly from plate_df in the code:
    # output_df: pd.DataFrame = plate_df[["Well Position", "Sequence Name"]].copy()
    # So it should contain ALL entries from the plate spec, regardless of whether they are in the BED file?
    # Let's check the code implementation again.

    # Code:
    # output_df: pd.DataFrame = plate_df[["Well Position", "Sequence Name"]].copy()
    # It does NOT filter output_df by bedlines. It only filters the transfer_df (wanted_bedlines).
    # So sample_df should match the plate_df exactly in terms of rows.

    assert len(sample_df) == len(plate_df), (
        f"Sample DF row count ({len(sample_df)}) does not match Spec Sheet row count ({len(plate_df)}) for plate {plate_name}"
    )
