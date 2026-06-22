from pathlib import Path

from typer.testing import CliRunner

from bed2myra.main import app

TEST_DIR = Path(__file__).parent
PRIMER_BED = TEST_DIR / "primer.bed"
PLATE_SPEC = TEST_DIR / "PlateSpecs.xlsx"

runner = CliRunner()


def test_nonexistent_primer_bed_gives_clean_error():
    result = runner.invoke(
        app,
        ["-b", "nonexistent.bed", "-s", str(PLATE_SPEC), "-p", "modjadji-tb_1.0"],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output
    assert "nonexistent.bed" in result.output


def test_nonexistent_plate_spec_gives_clean_error():
    result = runner.invoke(
        app,
        ["-b", str(PRIMER_BED), "-s", "nonexistent.xlsx", "-p", "modjadji-tb_1.0"],
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output
    assert "nonexistent.xlsx" in result.output


def test_output_dir_created_automatically(tmp_path):
    out = tmp_path / "nested" / "deep" / "output"
    result = runner.invoke(
        app,
        [
            "-b",
            str(PRIMER_BED),
            "-s",
            str(PLATE_SPEC),
            "-p",
            "modjadji-tb_1.0",
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    assert out.is_dir()
    csv_files = list(out.glob("*.csv"))
    assert len(csv_files) >= 1


def test_output_files_written_with_correct_names(tmp_path):
    result = runner.invoke(
        app,
        [
            "-b",
            str(PRIMER_BED),
            "-s",
            str(PLATE_SPEC),
            "-p",
            "modjadji-tb_1.0",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    sample = tmp_path / "myra_sample_modjadji-tb_1.0.csv"
    transfer = tmp_path / "myra_transfer_modjadji-tb_1.0.csv"
    assert sample.exists(), f"Expected {sample}, found {list(tmp_path.iterdir())}"
    assert transfer.exists(), f"Expected {transfer}, found {list(tmp_path.iterdir())}"


def test_output_prefix_with_slash_is_sanitized(tmp_path):
    result = runner.invoke(
        app,
        [
            "-b",
            str(PRIMER_BED),
            "-s",
            str(PLATE_SPEC),
            "-p",
            "modjadji-tb_1.0",
            "-o",
            str(tmp_path),
            "--output-prefix",
            "run/1",
        ],
    )
    assert result.exit_code == 0, result.output
    csv_files = list(tmp_path.glob("*.csv"))
    assert len(csv_files) >= 1
    for f in csv_files:
        assert "/" not in f.name.replace(str(tmp_path), "")


def test_logs_resolved_output_directory(tmp_path):
    result = runner.invoke(
        app,
        [
            "-b",
            str(PRIMER_BED),
            "-s",
            str(PLATE_SPEC),
            "-p",
            "modjadji-tb_1.0",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output


def test_pool_mode_writes_files(tmp_path):
    result = runner.invoke(
        app,
        [
            "-b",
            str(PRIMER_BED),
            "-s",
            str(PLATE_SPEC),
            "--pool",
            "1",
            "-o",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    csv_files = list(tmp_path.glob("*.csv"))
    assert len(csv_files) >= 1
    sample_files = [f for f in csv_files if "sample" in f.name]
    transfer_files = [f for f in csv_files if "transfer" in f.name]
    assert len(sample_files) >= 1
    assert len(transfer_files) >= 1
