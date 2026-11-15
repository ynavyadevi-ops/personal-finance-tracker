"""Pydantic schemas for data portability, statement imports, exports, and backup verification."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StatementMapping(BaseModel):
    """Configurable column name mapping for CSV/Excel statement imports."""

    date_column: str = Field(default="Date", description="Column containing transaction date.")
    amount_column: str = Field(
        default="Amount", description="Column containing transaction amount."
    )
    description_column: str = Field(
        default="Description", description="Column containing transaction description or payee."
    )
    category_column: str | None = Field(
        default="Category", description="Optional column containing category name."
    )
    type_column: str | None = Field(
        default="Type", description="Optional column containing transaction type (INCOME/EXPENSE)."
    )


class StatementRowPreview(BaseModel):
    """Parsed and validated row representation for user preview prior to commit."""

    row_number: int
    raw_data: dict[str, Any]
    parsed_date: date | None = None
    parsed_amount: Decimal | None = None
    parsed_description: str | None = None
    parsed_category: str | None = None
    parsed_type: str | None = None  # INCOME or EXPENSE
    is_duplicate: bool = False
    validation_errors: list[str] = []


class ImportPreviewResponse(BaseModel):
    """Aggregate preview report showing parsing summary, duplicates, and errors."""

    total_rows: int
    valid_rows: int
    duplicate_rows: int
    invalid_rows: int
    previews: list[StatementRowPreview]


class ImportCommitRow(BaseModel):
    """Validated row payload for batch import commitment."""

    parsed_date: date
    parsed_amount: Decimal
    parsed_description: str
    parsed_category_id: str | None = None
    parsed_type: str = "EXPENSE"


class ImportCommitRequest(BaseModel):
    """Request to commit previewed rows into the financial ledger."""

    account_id: str
    rows: list[ImportCommitRow]


class ImportCommitResponse(BaseModel):
    """Summary of committed statement import."""

    imported_count: int
    skipped_duplicates_count: int


class BackupValidationResponse(BaseModel):
    """Dry-run validation response for a user data backup snapshot."""

    model_config = ConfigDict(from_attributes=True)

    is_valid: bool
    version: str
    tables_found: list[str]
    total_records: int
    validation_messages: list[str] = []
