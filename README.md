# Bed2Myra

**Bed2Myra** is a command-line tool designed to automate the generation of input files for the **MYRA liquid handling robot**. 

It calculates the required transfer volumes based on primer weights and generates:
1.  **Sample Sheets**: Defining the source layout.
2.  **Transfer Sheets**: Instructions for the robot to move specific volumes from source wells to destination tubes.

## Features

- **Automated Mapping**: Matches primers from a BED file to their physical location in source plates using an Excel specification sheet.
- **Volume Calculation**: Automatically calculates transfer volumes based on primer weight (`pw` tag in BED file) and a user-defined multiplier.
- **Safety Checks**: Enforces volume limits (Min: 1µL, Max: 50µL) to ensure safe pipetting.
- **Replicate Support**: Easily generate instructions for multiple technical replicates (e.g., triplicates) in a single run.
- **Batch Processing**: Process multiple source plates in one command.

## Installation

This project is managed with [uv](https://github.com/astral-sh/uv).

### Local Development
Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd bed2myra
uv sync
```

## Usage

Run the tool using `uv run`:

```bash
uv run bed2myra -b <bed_file> -s <spec_sheet> -p <plate_names> [options]
```

### Arguments

| Short | Long | Required | Description | Default |
| :--- | :--- | :---: | :--- | :--- |
| `-b` | `--primer-bed` | **Yes** | Path to the primer BED file containing weights (`pw` tag). | - |
| `-s` | `--plate-spec` | **Yes** | Path to the Excel file (.xlsx) containing plate specifications. | - |
| `-p` | `--plate-names`| **Yes** | Name(s) of the source plate(s) to process. Supports multiple names. | - |
| `-m` | `--volume-multiplier` | No | Multiplier factor for the volume calculation. | `1.0` |
| `-r` | `--replicates` | No | Number of replicate destination tubes to create. | `1` |
| `-o` | `--output-dir` | No | Directory to save the generated CSV files. | `./output/` |
| | `--output-prefix` | No | Prefix for the output filenames. | `myra` |

### Example

Generate files for two plates (`plate_1` and `plate_2`) with **3 replicates** each, using a **1.5x** volume multiplier:

```bash
uv run bed2myra \
  -b data/primers.bed \
  -s data/plate_layout.xlsx \
  -p "plate_1" "plate_2" \
  -r 3 \
  -m 1.5 \
  -o ./myra_files/
```

## Input File Formats

### 1. Primer BED File
A standard BED-like file describing the primers. It must contain a weight tag (format `pw=<float>`) in the description/tags column to calculate volumes.

**Example:**
```text
NC_000962.3  528752  528772  primer_1_LEFT   1  +  ACCAACG...  pw=3.267
NC_000962.3  529173  529193  primer_1_RIGHT  1  -  CTTGTCG...  pw=3.267
```

### 2. Plate Specification (Excel)
An Excel file (`.xlsx`) defining where each primer is located in the source plates. Required columns:

- **Plate Name**: The identifier for the plate (matches `-p` argument).
- **Sequence Name**: The ID of the primer (must match the name column in the BED file).
- **Well Position**: The specific well (e.g., `A1`, `B2`).

| Plate Name | Well Position | Sequence Name |
| :--- | :--- | :--- |
| plate_1 | A1 | primer_1_LEFT |
| plate_1 | A2 | primer_1_RIGHT |

## Outputs

The tool generates two types of CSV files in the output directory:

1.  **Sample File** (`<prefix>_sample_<plate_name>.csv`):
    - Contains the source layout: `Well` (Position) and `Source Name` (Primer ID).
2.  **Transfer File** (`<prefix>_transfer_<plates>.csv`):
    - Instructions for the MYRA robot.
    - Columns: `Well` (Destination replicate ID), `Sources` (Primer ID), `Volume` (Calculated µL).
