import logging
import pathlib
import re
from typing import Annotated, Optional

import pandas as pd
import typer
from primalbedtools.bedfiles import BedLine, BedLineParser
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

MIN_VOLUME_UL = 1.0
WARN_VOLUME_UL = 2.0
MAX_VOLUME_UL = 50.0
DEFAULT_WEIGHT_UL = 1

app = typer.Typer(name="bed2myra", pretty_exceptions_show_locals=False)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)


def log_missing_bedlines_in_spec_sheet(
    bedlines: list[BedLine], spec_sheet: pd.DataFrame
):
    bedline_names = {bl.primername for bl in bedlines}
    spec_names = set(spec_sheet["Sequence Name"].dropna().astype(str).unique().tolist())

    for primer_name in sorted(bedline_names - spec_names):
        logger.error(f"Primer in primer.bed not found in spec sheet: {primer_name}")
    for primer_name in sorted(spec_names - bedline_names):
        logger.error(f"Primer in spec sheet not found in primer.bed: {primer_name}")

    if bedline_names == spec_names:
        logger.info(
            f"{len(bedline_names)}/{len(spec_names)} primers in bed file found in spec sheet"
        )


def iter_plate_groups(plate_names: list[str], group_size: int):
    for idx in range(0, len(plate_names), group_size):
        yield plate_names[idx : idx + group_size]


def log_transfer_summary(transfer_df: pd.DataFrame, plates: list[str]):
    logger.info(
        f"Transfer ({', '.join(plates)}): "
        f"{len(transfer_df)} transfers | "
        f"{transfer_df['Sources'].nunique()} unique primers | "
        f"total volume {transfer_df['Volume'].sum():.2f} µL"
    )


def log_grand_total(transfer_df: pd.DataFrame):
    logger.info(
        f"Grand total: "
        f"{len(transfer_df)} transfers | "
        f"{transfer_df['Sources'].nunique()} unique primers | "
        f"total volume {transfer_df['Volume'].sum():.2f} µL"
    )


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
        logger.error(
            f"Cannot find plate '{plate_name}'. Options are: "
            f"{', '.join(available_plates)}"
        )
        return

    bedline_names = {bl.primername for bl in bedlines}
    plate_primer_names = (
        plate_df["Sequence Name"].dropna().astype(str).unique().tolist()
    )
    for primer_name in plate_primer_names:
        if primer_name not in bedline_names:
            logger.error(
                f"Primer in spec sheet plate not found in primer.bed: {primer_name}"
            )

    # Filter the bedlines for primername in the plate
    wanted_bedlines = [
        bl for bl in bedlines if bl.primername in plate_df["Sequence Name"].values
    ]

    # Create the output DataFrame in the required format
    output_df: pd.DataFrame = plate_df[["Well Position", "Sequence Name"]].copy()
    output_df = output_df.rename(
        columns={"Well Position": "Well", "Sequence Name": "Source Name"}
    )
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
                msg = (
                    f"Calculated volume {volume} for primer {bl.primername} is less than "
                    f"MIN_VOLUME_UL ({MIN_VOLUME_UL}). Please increase weight or volume multiplier."
                )
                logger.critical(msg)
                raise ValueError(msg)

            if volume < WARN_VOLUME_UL:
                logger.warning(
                    f"Small volume detected for primer {bl.primername} ({volume} µL). "
                    "This can lead to larger pipetting errors."
                )

            if volume > MAX_VOLUME_UL:
                logger.warning(
                    f"Large volume detected for primer {bl.primername} ({volume} µL). "
                    "This exceeds MAX_VOLUME_UL and will require multiple tips to complete the transfer."
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


@app.command(no_args_is_help=True)
def main(
    primer_bed: Annotated[
        pathlib.Path,
        typer.Option(
            "-b",
            "--primer-bed",
            help="Path to primer BED file with weights",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    plate_spec: Annotated[
        pathlib.Path,
        typer.Option(
            "-s",
            "--plate-spec",
            help="Path to Excel file with plate specifications",
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    plate_names: Annotated[
        Optional[list[str]],
        typer.Option(
            "-p",
            "--plate-names",
            help="Name(s) of the plate(s) to process. Required if --pool is not set. Mutually exclusive with --pool.",
        ),
    ] = None,
    pool: Annotated[
        Optional[int],
        typer.Option(
            "--pool",
            help="Pool number to process (uses all primers in that pool). Required if --plate-names is not set. Mutually exclusive with --plate-names.",
        ),
    ] = None,
    n_plate: Annotated[
        int,
        typer.Option("--n-plate", help="Number of plates to group per transfer run"),
    ] = 2,
    replicates: Annotated[
        int, typer.Option("-r", "--replicates", help="Number of replicates")
    ] = 1,
    output_dir: Annotated[
        pathlib.Path,
        typer.Option(
            "-o",
            "--output-dir",
            help="Location to write files to",
            file_okay=False,
            resolve_path=True,
        ),
    ] = pathlib.Path("./output/"),
    output_prefix: Annotated[
        str, typer.Option("--output-prefix", help="Output file prefix")
    ] = "myra",
    volume_multiplier: Annotated[
        float,
        typer.Option(
            "-x",
            "--volume-multiplier",
            help="Multiplier factor for the transferred volume. Useful for making larger batches.",
        ),
    ] = 1.0,
):
    if pool is not None and plate_names:
        typer.echo("Error: Use either --pool or --plate-names, not both.", err=True)
        raise typer.Exit(1)
    if pool is None and not plate_names:
        typer.echo("Error: One of --plate-names or --pool is required.", err=True)
        raise typer.Exit(1)
    if n_plate < 1:
        typer.echo("Error: --n-plate must be >= 1", err=True)
        raise typer.Exit(1)

    output_prefix = sanitize_filename(output_prefix)

    # Load the BED file and spec sheet
    _, bedlines = BedLineParser.from_file(primer_bed)
    spec_sheet = pd.read_excel(plate_spec)

    # Ensure output directory exists
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(
            f"Permission denied: cannot create output directory '{output_dir}'. "
            "Check that you have write access to the parent directory."
        )
        raise typer.Exit(1)
    except OSError as e:
        logger.error(f"Cannot create output directory '{output_dir}': {e}")
        raise typer.Exit(1)

    logger.info(f"Output directory: {output_dir}")

    if pool is not None:
        pool_bedlines = [bl for bl in bedlines if bl.pool == pool]
        if not pool_bedlines:
            logger.error(f"No primers found in primer.bed for pool {pool}")
            raise typer.Exit(1)

        pool_primer_names = {bl.primername for bl in pool_bedlines}
        spec_sheet_pool = spec_sheet[
            spec_sheet["Sequence Name"].isin(pool_primer_names)
        ]
        pool_plate_names = spec_sheet_pool["Plate Name"].dropna().unique().tolist()

        log_missing_bedlines_in_spec_sheet(pool_bedlines, spec_sheet_pool)
        if not pool_plate_names:
            logger.error(f"No plates found in spec sheet for pool {pool} primers.")
            raise typer.Exit(1)

        grand_total_df = None
        for plate_group in iter_plate_groups(pool_plate_names, n_plate):
            total_transfer_df = None
            for plate_name in plate_group:
                result = create_myra_files(
                    pool_bedlines,
                    spec_sheet_pool,
                    plate_name,
                    replicates,
                    volume_multiplier=volume_multiplier,
                )
                if result is not None:
                    sample_df, transfer_df = result
                    if total_transfer_df is None:
                        total_transfer_df = transfer_df
                    else:
                        total_transfer_df = pd.concat([total_transfer_df, transfer_df])

                    sample_path = (
                        output_dir
                        / f"{output_prefix}_sample_{sanitize_filename(plate_name)}.csv"
                    )
                    try:
                        sample_df.to_csv(sample_path, index=False)
                    except (PermissionError, OSError) as e:
                        logger.error(f"Failed to write '{sample_path}': {e}")
                        raise typer.Exit(1)
                    logger.info(
                        f"Successfully created sample MYRA file for plate '{plate_name}'"
                    )
                else:
                    logger.error(
                        "Failed to create MYRA files. Please check the plate name."
                    )

            if total_transfer_df is not None:
                transfer_path = (
                    output_dir
                    / f"{output_prefix}_transfer_{'-'.join(sanitize_filename(p) for p in plate_group)}.csv"
                )
                try:
                    total_transfer_df.to_csv(transfer_path, index=False)
                except (PermissionError, OSError) as e:
                    logger.error(f"Failed to write '{transfer_path}': {e}")
                    raise typer.Exit(1)
                logger.info(
                    f"Successfully created transfer MYRA file for plates '{', '.join(plate_group)}'"
                )
                log_transfer_summary(total_transfer_df, plate_group)
                grand_total_df = (
                    total_transfer_df
                    if grand_total_df is None
                    else pd.concat([grand_total_df, total_transfer_df])
                )

        if grand_total_df is not None:
            log_grand_total(grand_total_df)
    else:
        log_missing_bedlines_in_spec_sheet(bedlines, spec_sheet)
        total_transfer_df = None
        for plate_name in plate_names:
            result = create_myra_files(
                bedlines,
                spec_sheet,
                plate_name,
                replicates,
                volume_multiplier=volume_multiplier,
            )

            if result is not None:
                sample_df, transfer_df = result
                if total_transfer_df is None:
                    total_transfer_df = transfer_df
                else:
                    total_transfer_df = pd.concat([total_transfer_df, transfer_df])

                sample_path = (
                    output_dir
                    / f"{output_prefix}_sample_{sanitize_filename(plate_name)}.csv"
                )
                try:
                    sample_df.to_csv(sample_path, index=False)
                except (PermissionError, OSError) as e:
                    logger.error(f"Failed to write '{sample_path}': {e}")
                    raise typer.Exit(1)
                logger.info(
                    f"Successfully created sample MYRA file for plate '{plate_name}'"
                )
            else:
                logger.error(
                    "Failed to create MYRA files. Please check the plate name."
                )

        if total_transfer_df is not None:
            transfer_path = (
                output_dir
                / f"{output_prefix}_transfer_{'-'.join(sanitize_filename(p) for p in plate_names)}.csv"
            )
            try:
                total_transfer_df.to_csv(transfer_path, index=False)
            except (PermissionError, OSError) as e:
                logger.error(f"Failed to write '{transfer_path}': {e}")
                raise typer.Exit(1)
            logger.info(
                f"Successfully created transfer MYRA file for plates '{', '.join(plate_names)}'"
            )
            log_transfer_summary(total_transfer_df, plate_names)
            log_grand_total(total_transfer_df)


if __name__ == "__main__":
    app()
