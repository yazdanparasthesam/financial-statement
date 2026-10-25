import io

import pytest

from app.infra.ingestion import IngestionError, parse_trial_balance


@pytest.mark.unit
def test_parse_csv():
    content = b"code,name,debit,credit\n1101,Cash,100.5,0\n4101,Sales,0,100.50\n"
    rows = parse_trial_balance("tb.csv", content)
    assert rows == [
        {"code": "1101", "name": "Cash", "debit": 100.5, "credit": 0.0},
        {"code": "4101", "name": "Sales", "debit": 0.0, "credit": 100.5},
    ]


@pytest.mark.unit
def test_parse_csv_alternate_headers_and_separators():
    content = b"Account Code,Description,Deb,Cred\n1101,Cash,1000,0\n"
    rows = parse_trial_balance("tb.csv", content)
    assert rows[0]["debit"] == 1000.0


@pytest.mark.unit
def test_missing_columns_error_is_helpful():
    with pytest.raises(IngestionError) as e:
        parse_trial_balance("tb.csv", b"code,name,debit\n1101,Cash,5\n")
    assert "credit" in str(e.value)


@pytest.mark.unit
def test_unsupported_extension():
    with pytest.raises(IngestionError, match="Unsupported"):
        parse_trial_balance("tb.docx", b"whatever")


@pytest.mark.unit
def test_empty_file():
    with pytest.raises(IngestionError):
        parse_trial_balance("tb.csv", b"code,name,debit,credit\n")


@pytest.mark.unit
def test_parse_xlsx_roundtrip():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["code", "name", "debit", "credit"])
    ws.append(["1101", "Cash", 500, 0])
    buf = io.BytesIO()
    wb.save(buf)
    rows = parse_trial_balance("tb.xlsx", buf.getvalue())
    assert rows == [{"code": "1101", "name": "Cash", "debit": 500.0, "credit": 0.0}]
