from pathlib import Path

from meshshield.data.public_datasets import load_ieee_cis, load_paysim


def test_paysim_loader_streams_labeled_transactions(tmp_path: Path) -> None:
    csv_path = tmp_path / "paysim.csv"
    csv_path.write_text(
        "step,type,amount,nameOrig,nameDest,isFraud\n1,TRANSFER,15,a,b,1\n",
        encoding="utf-8",
    )
    rows = list(load_paysim(csv_path))
    assert len(rows) == 1
    assert rows[0].label == 1
    assert rows[0].account_id == "a"


def test_ieee_loader_joins_identity_when_available(tmp_path: Path) -> None:
    transactions = tmp_path / "transactions.csv"
    identity = tmp_path / "identity.csv"
    transactions.write_text(
        "TransactionID,TransactionDT,TransactionAmt,ProductCD,isFraud,card1\n7,60,10.5,W,0,100\n",
        encoding="utf-8",
    )
    identity.write_text("TransactionID,DeviceInfo,DeviceType\n7,phone-x,mobile\n", encoding="utf-8")
    row = next(load_ieee_cis(transactions, identity))
    assert row.device_id == "phone-x"
    assert row.label == 0
