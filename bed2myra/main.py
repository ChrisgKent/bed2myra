import argparse
import pathlib

import pandas as pd
from primalbedtools.bedfiles import BedLine, BedLineParser

MIN_VOLUME_UL = 1.0
MAX_VOLUME_UL = 50.0
DEFAULT_WEIGHT_UL = 1


def cli():
    parser = argparse.ArgumentParser(
        description="Create MYRA sample and transfer plate files from primer BED file and plate specification."
    )
    parser.add_argument(
        "-b",
        "--primer-bed",
        required=True,
        type=pathlib.Path,
        help="Path to primer BED file with weights",
    )
    parser.add_argument(
        "-s",
        "--plate-spec",
        required=True,
        type=pathlib.Path,
        help="Path to Excel file with plate specifications",
    )
    parser.add_argument(
        "-p",
        "--plate-names",
        required=True,
        help="Name(s) of the plate(s) to process",
        nargs="+",
    )
    parser.add_argument(
        "-r",
        "--replicates",
        type=int,
        default=1,
        help="Number of replicates (default: 1)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("./output/"),
        help="Location to write files to",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="myra",
        help="Output file prefix",
    )

    parser.add_argument(
        "-m",
        "--volume-multiplier",
        type=float,
        default=1.0,
        help="Multiplier factor for the transferred volume (default: 1.0). Useful for making larger batches.",
    )

    args = parser.parse_args()
    return args


def create_myra_files(
    bedlines: list[BedLine],
    spec_sheet,
    plate_name,
    replicates: int,
    volume_multiplier: float = 1.0,
):
    plate_df = spec_sheet[spec_sheet["Plate Name"] == plate_name]
    if plate_df.empty:
        available_plates = spec_sheet["Plate Name"].unique().tolist()
        print(
            f"Can't find plate ({plate_name}). options are {', '.join(available_plates)}"
        )
        return

    # Filter the bedlines for primername in the plate
    wanted_bedlines = [
        bl for bl in bedlines if bl.primername in plate_df["Sequence Name"].values
    ]

    # Create the output DataFrame in the required format
    # Merge plate_df with bedlines to get concentration (weight) data
    output_df: pd.DataFrame = plate_df[["Well Position", "Sequence Name"]].copy()
    output_df = output_df.rename(
        columns={"Well Position": "Well", "Sequence Name": "Source Name"}
    )
    # Add empty Groups column
    output_df["Groups"] = ""
    output_df["Concentration"] = ""

    # Create the transfer plate DataFrame
    transfer_data = []
    for replicate in range(1, replicates + 1):
        for bl in wanted_bedlines:
            volume = (
                bl.weight if bl.weight is not None else DEFAULT_WEIGHT_UL
            ) * volume_multiplier

            if volume < MIN_VOLUME_UL:
                raise ValueError(
                    f"Calculated volume {volume} for primer {bl.primername} is less than "
                    f"MIN_VOLUME_UL ({MIN_VOLUME_UL}). Please increase weight or volume multiplier."
                )
            if volume > MAX_VOLUME_UL:
                raise ValueError(
                    f"Calculated volume {volume} for primer {bl.primername} is greater than "
                    f"MAX_VOLUME_UL ({MAX_VOLUME_UL}). Please decrease weight or volume multiplier."
                )

            transfer_data.append(
                {
                    "Well": replicate,
                    "Sources": bl.primername,
                    "Concentration": "",
                    "Volume": volume,
                }
            )
    transfer_df = pd.DataFrame(transfer_data)

    return output_df, transfer_df


def main():
    args = cli()

    # Load the BED file
    _, bedlines = BedLineParser.from_file(args.primer_bed)

    # Load in the spec sheet.
    spec_sheet = pd.read_excel(args.plate_spec)

    # Ensure output directory exists
    if not args.output_dir.exists():
        args.output_dir.mkdir(parents=True, exist_ok=True)

    # Create the MYRA files
    total_transfer_df = None
    for plate_name in args.plate_names:
        result = create_myra_files(
            bedlines,
            spec_sheet,
            plate_name,
            args.replicates,
            volume_multiplier=args.volume_multiplier,
        )

        if result is not None:
            sample_df, transfer_df = result

            if total_transfer_df is None:
                total_transfer_df = transfer_df
            else:
                total_transfer_df = pd.concat([total_transfer_df, transfer_df])

            # Write the sample sheet out
            sample_df.to_csv(
                args.output_dir / f"{args.output_prefix}_sample_{plate_name}.csv",
                index=False,
            )
            print(f"Successfully created sample MYRA file for plate '{plate_name}'")
        else:
            print("Failed to create MYRA files. Please check the plate name.")

    # Write the transfer plate out
    if total_transfer_df is not None:
        total_transfer_df.to_csv(
            args.output_dir
            / f"{args.output_prefix}_transfer_{'-'.join(args.plate_names)}.csv",
            index=False,
        )
        print(f"Successfully created transfer MYRA file for plates '{args.plate_names}'")


if __name__ == "__main__":
    main()
