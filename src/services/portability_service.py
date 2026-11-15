"""Data portability services: Statement CSV/XLSX import, filtered export, and user backup validation."""

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError, ValidationError
from src.core.logging import logger
from src.core.money import to_decimal
from src.db.models import (
    Budget,
    Category,
    FinancialAccount,
    InvestmentHolding,
    InvestmentTransaction,
    LoanDebt,
    RecurringRule,
    SavingsGoal,
    Transaction,
    User,
)
from src.db.models.transaction import TransactionType
from src.repositories.account_repo import AccountRepository
from src.schemas.portability import (
    BackupValidationResponse,
    ImportCommitRequest,
    ImportCommitResponse,
    ImportPreviewResponse,
    StatementMapping,
    StatementRowPreview,
)
from src.services.transaction_service import TransactionService

# Constants for file ingestion limits
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ROW_COUNT = 1000

# Formula injection trigger characters (RFC 4180 / CSV injection prevention)
DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_formula_injection(value: Any) -> Any:
    """Escape values that could trigger spreadsheet formula execution."""
    if isinstance(value, str):
        if value.startswith(DANGEROUS_FORMULA_PREFIXES):
            return f"'{value}"
    return value


class StatementImportService:
    """Parses and validates bank/credit card statements from CSV and XLSX buffers."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.tx_service = TransactionService(session)

    def parse_statement_file(
        self,
        file_bytes: bytes,
        filename: str,
        mapping: StatementMapping,
        user_id: str,
        account_id: str,
    ) -> ImportPreviewResponse:
        """Parse file buffer, validate rows, check for duplicates against the ledger, and generate a preview."""
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        account = self.account_repo.get_by_id(account_id=account_id, user_id=user_id)
        if not account:
            raise NotFoundError(f"Account with ID '{account_id}' was not found for this user.")

        filename_lower = filename.lower()
        try:
            if filename_lower.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
            elif filename_lower.endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
            else:
                raise ValidationError("Unsupported statement file format. Must be CSV or XLSX.")
        except Exception as e:
            logger.error(f"Failed to parse statement file '{filename}': {e}")
            raise ValidationError(f"Could not parse uploaded statement file: {e}") from e

        if len(df) > MAX_ROW_COUNT:
            raise ValidationError(
                f"Statement contains {len(df)} rows, which exceeds the limit of {MAX_ROW_COUNT}."
            )

        # Validate required mapped columns exist in dataset
        available_cols = [c.strip() for c in df.columns]
        req_cols = [mapping.date_column, mapping.amount_column, mapping.description_column]
        missing_cols = [c for c in req_cols if c not in available_cols]
        if missing_cols:
            raise ValidationError(
                f"Required column(s) {missing_cols} missing from uploaded statement. "
                f"Found columns: {available_cols}"
            )

        previews: list[StatementRowPreview] = []
        valid_count = 0
        duplicate_count = 0
        invalid_count = 0

        # Query existing transactions for duplicate detection
        existing_txs_stmt = select(
            Transaction.transaction_date, Transaction.amount, Transaction.description
        ).where(
            Transaction.user_id == user_id,
        )
        existing_records = set(self.session.execute(existing_txs_stmt).all())

        for idx, row in df.iterrows():
            row_num = int(idx) + 1  # 1-based index
            errors: list[str] = []
            parsed_date: date | None = None
            parsed_amount: Decimal | None = None
            parsed_desc: str | None = None
            parsed_category: str | None = None
            parsed_type: str = "EXPENSE"

            # 1. Parse Date
            raw_date = str(row.get(mapping.date_column, "")).strip()
            if not raw_date:
                errors.append(f"Missing date in column '{mapping.date_column}'.")
            else:
                try:
                    dt = pd.to_datetime(raw_date)
                    parsed_date = dt.date()
                except Exception:
                    errors.append(f"Invalid date format: '{raw_date}'.")

            # 2. Parse Amount
            raw_amount = str(row.get(mapping.amount_column, "")).strip()
            # Clean common formatting like currency symbols, commas, spaces
            cleaned_amount = re.sub(r"[^\d.-]", "", raw_amount)
            if not cleaned_amount:
                errors.append(f"Missing or invalid amount in column '{mapping.amount_column}'.")
            else:
                try:
                    dec_val = Decimal(cleaned_amount)
                    parsed_amount = to_decimal(abs(dec_val))
                    if dec_val > Decimal("0.00"):
                        parsed_type = "INCOME"
                    elif dec_val < Decimal("0.00"):
                        parsed_type = "EXPENSE"
                except InvalidOperation:
                    errors.append(f"Unparseable numeric amount: '{raw_amount}'.")

            # 3. Parse Description
            raw_desc = str(row.get(mapping.description_column, "")).strip()
            if not raw_desc:
                errors.append(f"Missing description in column '{mapping.description_column}'.")
            else:
                parsed_desc = raw_desc[:255]

            # 4. Optional Category
            if mapping.category_column and mapping.category_column in row:
                cat_val = str(row.get(mapping.category_column, "")).strip()
                if cat_val:
                    parsed_category = cat_val

            # 5. Optional Explicit Type
            if mapping.type_column and mapping.type_column in row:
                t_val = str(row.get(mapping.type_column, "")).strip().upper()
                if "INCOME" in t_val or "CREDIT" in t_val or "DEPOSIT" in t_val:
                    parsed_type = "INCOME"
                elif "EXPENSE" in t_val or "DEBIT" in t_val or "PAYMENT" in t_val:
                    parsed_type = "EXPENSE"

            # 6. Duplicate detection
            is_dup = False
            if not errors and parsed_date and parsed_amount and parsed_desc:
                check_tuple = (parsed_date, parsed_amount, parsed_desc)
                if check_tuple in existing_records:
                    is_dup = True

            if errors:
                invalid_count += 1
            elif is_dup:
                duplicate_count += 1
            else:
                valid_count += 1

            raw_dict = {str(k): str(v) for k, v in row.items()}
            previews.append(
                StatementRowPreview(
                    row_number=row_num,
                    raw_data=raw_dict,
                    parsed_date=parsed_date,
                    parsed_amount=parsed_amount,
                    parsed_description=parsed_desc,
                    parsed_category=parsed_category,
                    parsed_type=parsed_type,
                    is_duplicate=is_dup,
                    validation_errors=errors,
                )
            )

        return ImportPreviewResponse(
            total_rows=len(df),
            valid_rows=valid_count,
            duplicate_rows=duplicate_count,
            invalid_rows=invalid_count,
            previews=previews,
        )

    def commit_statement_import(
        self, user_id: str, payload: ImportCommitRequest
    ) -> ImportCommitResponse:
        """Atomically commit previewed non-duplicate rows through TransactionService."""
        account = self.account_repo.get_by_id(account_id=payload.account_id, user_id=user_id)
        if not account:
            raise NotFoundError(
                f"Account with ID '{payload.account_id}' was not found for this user."
            )

        imported_count = 0
        skipped_count = 0

        # Run inside a single atomic unit of work
        for row in payload.rows:
            tx_type = (
                TransactionType.INCOME if row.parsed_type == "INCOME" else TransactionType.EXPENSE
            )
            from src.schemas.transaction import TransactionCreate

            tx_payload = TransactionCreate(
                account_id=payload.account_id,
                category_id=row.parsed_category_id,
                transaction_type=tx_type,
                amount=row.parsed_amount,
                description=row.parsed_description,
                transaction_date=row.parsed_date,
                currency=account.currency,
                notes="Imported via statement file",
                tags="statement_import",
            )
            self.tx_service.record_transaction(user_id=user_id, payload=tx_payload)
            imported_count += 1

        logger.info(f"Committed statement import: {imported_count} rows for user {user_id}")
        return ImportCommitResponse(
            imported_count=imported_count,
            skipped_duplicates_count=skipped_count,
        )


class DataExportService:
    """Generates sanitized, user-scoped CSV and XLSX exports of financial transactions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_export_rows(
        self,
        user_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch transactions with line items and format into clean export dictionary records."""
        query = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        )

        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)

        transactions = self.session.execute(query).scalars().all()

        rows: list[dict[str, Any]] = []
        for tx in transactions:
            for entry in tx.entries:
                if account_id and entry.account_id != account_id:
                    continue
                if category_id and entry.category_id != category_id:
                    continue

                account_name = entry.account.name if entry.account else ""
                category_name = entry.category.name if entry.category else "Uncategorized"

                # Protect against spreadsheet formula injection
                clean_desc = sanitize_formula_injection(tx.description)
                clean_notes = sanitize_formula_injection(tx.notes or "")
                clean_tags = sanitize_formula_injection(tx.tags or "")

                rows.append(
                    {
                        "Transaction ID": tx.id,
                        "Date": tx.transaction_date.isoformat(),
                        "Type": tx.transaction_type.value,
                        "Description": clean_desc,
                        "Account": sanitize_formula_injection(account_name),
                        "Category": sanitize_formula_injection(category_name),
                        "Entry Direction": entry.entry_type.value,
                        "Amount": f"{entry.amount:.2f}",
                        "Currency": entry.currency,
                        "Notes": clean_notes,
                        "Tags": clean_tags,
                    }
                )

        return rows

    def export_csv(
        self,
        user_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> str:
        """Generate RFC 4180 compliant CSV stream with formula injection mitigation."""
        rows = self.get_export_rows(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            category_id=category_id,
        )

        fieldnames = [
            "Transaction ID",
            "Date",
            "Type",
            "Description",
            "Account",
            "Category",
            "Entry Direction",
            "Amount",
            "Currency",
            "Notes",
            "Tags",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

        return output.getvalue()

    def export_xlsx(
        self,
        user_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        account_id: str | None = None,
        category_id: str | None = None,
    ) -> bytes:
        """Generate Excel XLSX spreadsheet workbook with formula protection."""
        rows = self.get_export_rows(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            category_id=category_id,
        )

        df = pd.DataFrame(rows)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Transactions")

        return output.getvalue()


class BackupService:
    """Provides user-scoped JSON snapshot backups and schema dry-run validation."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def generate_backup(self, user_id: str) -> dict[str, Any]:
        """Compile a full user-scoped JSON backup snapshot across all 11 domain models."""
        user = self.session.get(User, user_id)
        if not user:
            raise NotFoundError(f"User '{user_id}' was not found.")

        # 1. Accounts
        accounts = (
            self.session.execute(
                select(FinancialAccount).where(FinancialAccount.user_id == user_id)
            )
            .scalars()
            .all()
        )
        accounts_data = [
            {
                "id": a.id,
                "name": a.name,
                "account_type": a.account_type.value,
                "institution_name": a.institution_name,
                "currency": a.currency,
                "opening_balance": f"{a.opening_balance:.2f}",
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat(),
            }
            for a in accounts
        ]

        # 2. Categories
        categories = (
            self.session.execute(select(Category).where(Category.user_id == user_id))
            .scalars()
            .all()
        )
        categories_data = [
            {
                "id": c.id,
                "name": c.name,
                "category_type": c.category_type.value,
                "parent_id": c.parent_id,
                "icon": c.icon,
                "color": c.color,
                "is_default": c.is_default,
            }
            for c in categories
        ]

        # 3. Transactions & Entries
        transactions = (
            self.session.execute(select(Transaction).where(Transaction.user_id == user_id))
            .scalars()
            .all()
        )
        transactions_data = [
            {
                "id": tx.id,
                "transaction_date": tx.transaction_date.isoformat(),
                "transaction_type": tx.transaction_type.value,
                "description": tx.description,
                "amount": f"{tx.amount:.2f}",
                "currency": tx.currency,
                "notes": tx.notes,
                "tags": tx.tags,
                "recurring_rule_id": tx.recurring_rule_id,
                "entries": [
                    {
                        "id": e.id,
                        "account_id": e.account_id,
                        "category_id": e.category_id,
                        "entry_type": e.entry_type.value,
                        "amount": f"{e.amount:.2f}",
                        "currency": e.currency,
                        "notes": e.notes,
                    }
                    for e in tx.entries
                ],
            }
            for tx in transactions
        ]

        # 4. Budgets
        budgets = (
            self.session.execute(select(Budget).where(Budget.user_id == user_id)).scalars().all()
        )
        budgets_data = [
            {
                "id": b.id,
                "category_id": b.category_id,
                "month": b.month,
                "year": b.year,
                "amount": f"{b.amount:.2f}",
                "rollover_enabled": b.rollover_enabled,
                "notes": b.notes,
            }
            for b in budgets
        ]

        # 5. Savings Goals
        goals = (
            self.session.execute(select(SavingsGoal).where(SavingsGoal.user_id == user_id))
            .scalars()
            .all()
        )
        goals_data = [
            {
                "id": g.id,
                "name": g.name,
                "target_amount": f"{g.target_amount:.2f}",
                "current_amount": f"{g.current_amount:.2f}",
                "currency": g.currency,
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "is_achieved": g.is_achieved,
                "notes": g.notes,
            }
            for g in goals
        ]

        # 6. Loans & Schedules
        loans = (
            self.session.execute(select(LoanDebt).where(LoanDebt.user_id == user_id))
            .scalars()
            .all()
        )
        loans_data = [
            {
                "id": loan.id,
                "account_id": loan.account_id,
                "lender_name": loan.lender_name,
                "principal_amount": f"{loan.principal_amount:.2f}",
                "remaining_balance": f"{loan.remaining_balance:.2f}",
                "interest_rate": f"{loan.interest_rate:.2f}",
                "interest_type": loan.interest_type.value,
                "term_months": loan.term_months,
                "minimum_monthly_payment": f"{loan.minimum_monthly_payment:.2f}",
                "start_date": loan.start_date.isoformat(),
                "due_date": loan.due_date.isoformat() if loan.due_date else None,
                "is_settled": loan.is_settled,
                "notes": loan.notes,
                "payment_schedules": [
                    {
                        "id": s.id,
                        "payment_number": s.payment_number,
                        "due_date": s.due_date.isoformat(),
                        "principal_component": f"{s.principal_component:.2f}",
                        "interest_component": f"{s.interest_component:.2f}",
                        "total_payment": f"{s.total_payment:.2f}",
                        "remaining_balance": f"{s.remaining_balance:.2f}",
                        "is_paid": s.is_paid,
                        "paid_date": s.paid_date.isoformat() if s.paid_date else None,
                    }
                    for s in loan.payment_schedules
                ],
            }
            for loan in loans
        ]

        # 7. Investment Holdings & Transactions
        holdings = (
            self.session.execute(
                select(InvestmentHolding).where(InvestmentHolding.user_id == user_id)
            )
            .scalars()
            .all()
        )
        holdings_data = [
            {
                "id": h.id,
                "account_id": h.account_id,
                "asset_id": h.asset_id,
                "quantity": f"{h.quantity:.4f}",
                "cost_basis_per_unit": f"{h.cost_basis_per_unit:.2f}",
                "total_cost": f"{h.total_cost:.2f}",
                "currency": h.currency,
            }
            for h in holdings
        ]

        inv_txs = (
            self.session.execute(
                select(InvestmentTransaction).where(InvestmentTransaction.user_id == user_id)
            )
            .scalars()
            .all()
        )
        inv_txs_data = [
            {
                "id": it.id,
                "account_id": it.account_id,
                "asset_id": it.asset_id,
                "transaction_type": it.transaction_type.value,
                "transaction_date": it.transaction_date.isoformat(),
                "quantity": f"{it.quantity:.4f}",
                "price_per_unit": f"{it.price_per_unit:.2f}",
                "total_amount": f"{it.total_amount:.2f}",
                "fees": f"{it.fees:.2f}",
                "currency": it.currency,
                "notes": it.notes,
            }
            for it in inv_txs
        ]

        # 8. Recurring Rules
        recurring = (
            self.session.execute(select(RecurringRule).where(RecurringRule.user_id == user_id))
            .scalars()
            .all()
        )
        recurring_data = [
            {
                "id": r.id,
                "account_id": r.account_id,
                "category_id": r.category_id,
                "destination_account_id": r.destination_account_id,
                "name": r.name,
                "amount": f"{r.amount:.2f}",
                "currency": r.currency,
                "transaction_type": r.transaction_type.value,
                "frequency": r.frequency.value,
                "interval": r.interval,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "next_occurrence": r.next_occurrence.isoformat(),
                "is_active": r.is_active,
                "notes": r.notes,
            }
            for r in recurring
        ]

        return {
            "schema_version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
            "data": {
                "financial_accounts": accounts_data,
                "categories": categories_data,
                "transactions": transactions_data,
                "budgets": budgets_data,
                "savings_goals": goals_data,
                "loans": loans_data,
                "investment_holdings": holdings_data,
                "investment_transactions": inv_txs_data,
                "recurring_rules": recurring_data,
            },
        }

    def validate_backup(self, backup_dict: dict[str, Any]) -> BackupValidationResponse:
        """Dry-run validation of a backup snapshot verifying version, completeness, and structure.

        NOTE: Per Phase 4 security requirements, destructive restore execution is disabled.
        """
        messages: list[str] = []
        is_valid = True

        version = backup_dict.get("schema_version")
        if version != "1.0.0":
            messages.append(f"Incompatible backup schema version: '{version}'. Expected '1.0.0'.")
            is_valid = False

        if "data" not in backup_dict or not isinstance(backup_dict["data"], dict):
            messages.append("Missing or invalid 'data' section in backup payload.")
            return BackupValidationResponse(
                is_valid=False,
                version=str(version or "unknown"),
                tables_found=[],
                total_records=0,
                validation_messages=messages,
            )

        data = backup_dict["data"]
        expected_tables = [
            "financial_accounts",
            "categories",
            "transactions",
            "budgets",
            "savings_goals",
            "loans",
            "investment_holdings",
            "investment_transactions",
            "recurring_rules",
        ]

        found_tables: list[str] = []
        total_records = 0

        for table in expected_tables:
            if table in data:
                found_tables.append(table)
                records = data[table]
                if isinstance(records, list):
                    total_records += len(records)
                else:
                    messages.append(f"Table '{table}' is not a valid list of records.")
                    is_valid = False
            else:
                messages.append(f"Warning: Table '{table}' not present in backup.")

        messages.append("Dry-run validation successful. No destructive database changes executed.")
        return BackupValidationResponse(
            is_valid=is_valid,
            version=str(version or "1.0.0"),
            tables_found=found_tables,
            total_records=total_records,
            validation_messages=messages,
        )
