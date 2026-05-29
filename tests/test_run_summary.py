import logging
import pandas as pd
from bed2myra.main import log_transfer_summary, log_grand_total


def _make_transfer_df(rows):
    return pd.DataFrame(rows, columns=["Well", "Sources", "Concentration", "Volume"])


def test_transfer_summary_logs_correct_values(caplog):
    df = _make_transfer_df(
        [
            (1, "primer_A", "", 2.5),
            (1, "primer_B", "", 3.0),
            (1, "primer_C", "", 1.5),
        ]
    )
    with caplog.at_level(logging.INFO, logger="bed2myra.main"):
        log_transfer_summary(df, ["plate_1"])

    messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    assert any("plate_1" in m for m in messages)
    assert any("3 unique primers" in m for m in messages)
    assert any("7.00" in m for m in messages)


def test_grand_total_logs_combined_values(caplog):
    df = _make_transfer_df(
        [
            (1, "primer_A", "", 2.5),
            (1, "primer_B", "", 3.0),
            (1, "primer_A", "", 2.5),
            (1, "primer_C", "", 1.5),
        ]
    )
    with caplog.at_level(logging.INFO, logger="bed2myra.main"):
        log_grand_total(df)

    messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    assert any("Grand total" in m for m in messages)
    assert any("4 transfers" in m for m in messages)
    assert any("3 unique primers" in m for m in messages)
    assert any("9.50" in m for m in messages)
