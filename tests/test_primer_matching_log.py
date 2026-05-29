import logging
import pandas as pd
from types import SimpleNamespace
from bed2myra.main import log_missing_bedlines_in_spec_sheet, create_myra_files


def _make_bedlines(*names):
    return [SimpleNamespace(primername=n) for n in names]


def _make_spec(names):
    return pd.DataFrame({"Sequence Name": list(names)})


# --- log_missing_bedlines_in_spec_sheet ---


def test_confirmation_log_when_sets_match(caplog):
    """INFO confirmation is logged when primer.bed and spec sheet names are identical."""
    bedlines = _make_bedlines("primer_A", "primer_B")
    spec_sheet = _make_spec(["primer_A", "primer_B"])

    with caplog.at_level(logging.INFO, logger="bed2myra.main"):
        log_missing_bedlines_in_spec_sheet(bedlines, spec_sheet)

    messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    assert any("2/2" in m and "bed file" in m for m in messages)


def test_error_logged_for_bed_primer_missing_from_spec(caplog):
    """ERROR is logged for a primer present in primer.bed but absent from the spec sheet."""
    bedlines = _make_bedlines("primer_A", "primer_EXTRA")
    spec_sheet = _make_spec(["primer_A"])

    with caplog.at_level(logging.ERROR, logger="bed2myra.main"):
        log_missing_bedlines_in_spec_sheet(bedlines, spec_sheet)

    errors = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("primer_EXTRA" in m and "not found in spec sheet" in m for m in errors)
    assert not any(
        "Confirmed" in r.message for r in caplog.records if r.levelno == logging.INFO
    )


def test_error_logged_for_spec_primer_missing_from_bed(caplog):
    """ERROR is logged for a primer present in the spec sheet but absent from primer.bed."""
    bedlines = _make_bedlines("primer_A")
    spec_sheet = _make_spec(["primer_A", "primer_EXTRA"])

    with caplog.at_level(logging.ERROR, logger="bed2myra.main"):
        log_missing_bedlines_in_spec_sheet(bedlines, spec_sheet)

    errors = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("primer_EXTRA" in m and "not found in primer.bed" in m for m in errors)


# --- create_myra_files: per-plate missing primer check ---


def test_error_logged_for_plate_primer_not_in_bedlines(caplog):
    """
    ERROR is logged for each primer listed in the plate spec that is absent from bedlines.
    The function still returns a result for the primers that do match.
    """
    bedlines = [SimpleNamespace(primername="primer_A", weight=2.0)]
    spec_sheet = pd.DataFrame(
        {
            "Plate Name": ["plate_1", "plate_1"],
            "Well Position": ["A01", "A02"],
            "Sequence Name": ["primer_A", "primer_MISSING"],
        }
    )

    with caplog.at_level(logging.ERROR, logger="bed2myra.main"):
        result = create_myra_files(
            bedlines=bedlines,
            spec_sheet=spec_sheet,
            plate_name="plate_1",
            replicates=1,
        )

    assert result is not None
    errors = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("primer_MISSING" in m for m in errors)
