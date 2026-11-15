"""Integration tests for Data Portability: Statement CSV/XLSX import, export, and backup validation."""

import io
from decimal import Decimal

import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.db.models import AccountType, Category, CategoryType, FinancialAccount


def test_statement_csv_import_preview_and_commit(client: TestClient, db_session: Session) -> None:
    """Verify uploading a CSV statement, previewing parsed rows with duplicate detection, and batch committing."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Import Test Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    cat = Category(
        user_id="default-user-id",
        name="Groceries Import",
        category_type=CategoryType.EXPENSE,
    )
    db_session.add_all([acc, cat])
    db_session.flush()

    # Create CSV content
    csv_data = (
        "Date,Amount,Description,Category,Type\n"
        "2026-11-01,150.00,Supermarket,Groceries,EXPENSE\n"
        "2026-11-02,500.00,Freelance Project,Consulting,INCOME\n"
    )

    files = {"file": ("statement.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    form_data = {
        "account_id": acc.id,
        "date_column": "Date",
        "amount_column": "Amount",
        "description_column": "Description",
        "category_column": "Category",
        "type_column": "Type",
    }

    # 1. Preview statement import
    preview_res = client.post("/api/v1/data/import/preview", data=form_data, files=files)
    assert preview_res.status_code == 200
    preview_data = preview_res.json()["data"]
    assert preview_data["total_rows"] == 2
    assert preview_data["valid_rows"] == 2
    assert preview_data["duplicate_rows"] == 0
    assert len(preview_data["previews"]) == 2

    # 2. Batch commit import
    commit_payload = {
        "account_id": acc.id,
        "rows": [
            {
                "parsed_date": "2026-11-01",
                "parsed_amount": "150.00",
                "parsed_description": "Supermarket",
                "parsed_category_id": cat.id,
                "parsed_type": "EXPENSE",
            },
            {
                "parsed_date": "2026-11-02",
                "parsed_amount": "500.00",
                "parsed_description": "Freelance Project",
                "parsed_category_id": None,
                "parsed_type": "INCOME",
            },
        ],
    }
    commit_res = client.post("/api/v1/data/import/commit", json=commit_payload)
    assert commit_res.status_code == 201
    assert commit_res.json()["data"]["imported_count"] == 2

    # 3. Preview again with the same file -> duplicate should be detected!
    files2 = {"file": ("statement.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    preview_dup_res = client.post("/api/v1/data/import/preview", data=form_data, files=files2)
    assert preview_dup_res.status_code == 200
    dup_data = preview_dup_res.json()["data"]
    assert dup_data["duplicate_rows"] > 0


def test_statement_xlsx_import_preview(client: TestClient, db_session: Session) -> None:
    """Verify uploading an Excel (.xlsx) statement spreadsheet produces valid preview."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Excel Bank Checking",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("2000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Generate in-memory Excel file
    df = pd.DataFrame(
        [
            {"Date": "2026-11-10", "Amount": "350.00", "Description": "Coffee Shop"},
            {"Date": "2026-11-12", "Amount": "1200.00", "Description": "Electricity Bill"},
        ]
    )
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_buf.seek(0)

    files = {
        "file": (
            "bank_statement.xlsx",
            excel_buf,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    form_data = {
        "account_id": acc.id,
        "date_column": "Date",
        "amount_column": "Amount",
        "description_column": "Description",
    }
    res = client.post("/api/v1/data/import/preview", data=form_data, files=files)
    assert res.status_code == 200
    assert res.json()["data"]["total_rows"] == 2
    assert res.json()["data"]["valid_rows"] == 2


def test_export_transactions_csv_and_formula_injection_defense(
    client: TestClient, db_session: Session
) -> None:
    """Verify CSV export mitigates formula injection by escaping dangerous characters (=, +, -, @)."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="Security Account",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("5000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    # Create transaction with potentially malicious formula string
    client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "99.00",
            "description": "=SUM(A1:A10)",
            "notes": "@HYPERLINK('http://attacker.dev')",
        },
    )

    csv_res = client.get("/api/v1/data/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text

    # Verify formula injection mitigation: cells starting with = or @ should be prefixed with '
    assert "'=SUM(A1:A10)" in csv_text
    assert "'@HYPERLINK" in csv_text


def test_export_transactions_xlsx(client: TestClient, db_session: Session) -> None:
    """Verify XLSX binary workbook export is generated and readable."""
    acc = FinancialAccount(
        user_id="default-user-id",
        name="XLSX Export Bank",
        account_type=AccountType.CHECKING,
        currency="INR",
        opening_balance=Decimal("1000.00"),
    )
    db_session.add(acc)
    db_session.flush()

    client.post(
        "/api/v1/transactions",
        json={
            "account_id": acc.id,
            "transaction_type": "EXPENSE",
            "amount": "45.00",
            "description": "Taxi ride",
        },
    )

    xlsx_res = client.get("/api/v1/data/export/xlsx")
    assert xlsx_res.status_code == 200
    assert "spreadsheetml" in xlsx_res.headers["content-type"]
    assert len(xlsx_res.content) > 0


def test_backup_export_and_dry_run_validation(client: TestClient) -> None:
    """Verify generating user-scoped JSON backup snapshot and running dry-run validation."""
    # 1. Export backup snapshot
    backup_res = client.get("/api/v1/data/backup")
    assert backup_res.status_code == 200
    backup_envelope = backup_res.json()["data"]

    assert backup_envelope["schema_version"] == "1.0.0"
    assert "exported_at" in backup_envelope
    assert "user" in backup_envelope
    assert "password" not in str(backup_envelope["user"])
    assert "hashed_password" not in str(backup_envelope["user"])

    data = backup_envelope["data"]
    assert "financial_accounts" in data
    assert "transactions" in data
    assert "budgets" in data
    assert "savings_goals" in data
    assert "loans" in data
    assert "investment_holdings" in data
    assert "recurring_rules" in data

    # 2. Dry-run validate backup
    val_res = client.post("/api/v1/data/backup/validate", json=backup_envelope)
    assert val_res.status_code == 200
    val_data = val_res.json()["data"]
    assert val_data["is_valid"] is True
    assert val_data["version"] == "1.0.0"
    assert len(val_data["tables_found"]) >= 7
    assert "Dry-run validation successful" in str(val_data["validation_messages"])
