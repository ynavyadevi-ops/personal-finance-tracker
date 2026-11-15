"""FastAPI router for Statement Import (CSV/XLSX), Data Export, and User Backup Validation."""

from datetime import date
from typing import Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)

from src.api.dependencies import (
    get_backup_service,
    get_current_user,
    get_data_export_service,
    get_statement_import_service,
)
from src.core.exceptions import ValidationError
from src.db.models.user import User
from src.schemas.common import GenericResponse
from src.schemas.portability import (
    BackupValidationResponse,
    ImportCommitRequest,
    ImportCommitResponse,
    ImportPreviewResponse,
    StatementMapping,
)
from src.services.portability_service import (
    BackupService,
    DataExportService,
    StatementImportService,
)

router = APIRouter(prefix="/data", tags=["Data Portability"])


@router.post(
    "/import/preview",
    response_model=GenericResponse[ImportPreviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Preview Statement File Import",
    description="Parses uploaded CSV or XLSX statement, validates columns, flags duplicates, and previews rows without committing.",
)
async def preview_statement_import(
    account_id: str = Form(..., description="Target financial account ID"),
    date_column: str = Form("Date", description="Name of column containing dates"),
    amount_column: str = Form("Amount", description="Name of column containing amounts"),
    description_column: str = Form(
        "Description", description="Name of column containing description"
    ),
    category_column: str | None = Form(None, description="Optional category column"),
    type_column: str | None = Form(None, description="Optional transaction type column"),
    file: UploadFile = File(..., description="Statement file (.csv, .xlsx, .xls)"),
    current_user: User = Depends(get_current_user),
    import_service: StatementImportService = Depends(get_statement_import_service),
) -> GenericResponse[ImportPreviewResponse]:
    """Parse statement file buffer and return row preview with duplicate flags."""
    if not file.filename:
        raise ValidationError("Uploaded file must have a valid filename.")

    file_bytes = await file.read()
    mapping = StatementMapping(
        date_column=date_column,
        amount_column=amount_column,
        description_column=description_column,
        category_column=category_column,
        type_column=type_column,
    )

    preview = import_service.parse_statement_file(
        file_bytes=file_bytes,
        filename=file.filename,
        mapping=mapping,
        user_id=current_user.id,
        account_id=account_id,
    )
    return GenericResponse(success=True, data=preview)


@router.post(
    "/import/commit",
    response_model=GenericResponse[ImportCommitResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Commit Statement Import",
    description="Batch commits previewed transaction rows into the financial ledger.",
)
def commit_statement_import(
    payload: ImportCommitRequest,
    current_user: User = Depends(get_current_user),
    import_service: StatementImportService = Depends(get_statement_import_service),
) -> GenericResponse[ImportCommitResponse]:
    """Atomically commit transactions into the double-entry accounting ledger."""
    summary = import_service.commit_statement_import(
        user_id=current_user.id,
        payload=payload,
    )
    return GenericResponse(success=True, data=summary)


@router.get(
    "/export/csv",
    summary="Export Transactions to CSV",
    description="Streams RFC 4180 compliant CSV export with formula injection mitigation.",
)
def export_transactions_csv(
    start_date: date | None = Query(None, description="Optional start date filter"),
    end_date: date | None = Query(None, description="Optional end date filter"),
    account_id: str | None = Query(None, description="Optional account ID filter"),
    category_id: str | None = Query(None, description="Optional category ID filter"),
    current_user: User = Depends(get_current_user),
    export_service: DataExportService = Depends(get_data_export_service),
) -> Response:
    """Stream user-scoped transactions as CSV."""
    csv_content = export_service.export_csv(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        category_id=category_id,
    )
    filename = f"transactions_export_{date.today().isoformat()}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/export/xlsx",
    summary="Export Transactions to Excel",
    description="Streams formatted Excel workbook with formula injection protection.",
)
def export_transactions_xlsx(
    start_date: date | None = Query(None, description="Optional start date filter"),
    end_date: date | None = Query(None, description="Optional end date filter"),
    account_id: str | None = Query(None, description="Optional account ID filter"),
    category_id: str | None = Query(None, description="Optional category ID filter"),
    current_user: User = Depends(get_current_user),
    export_service: DataExportService = Depends(get_data_export_service),
) -> Response:
    """Stream user-scoped transactions as XLSX workbook."""
    xlsx_bytes = export_service.export_xlsx(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        category_id=category_id,
    )
    filename = f"transactions_export_{date.today().isoformat()}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/backup",
    response_model=GenericResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Download User Backup Snapshot",
    description="Generates complete user-scoped JSON backup snapshot across all 11 domain models.",
)
def get_user_backup(
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
) -> GenericResponse[dict[str, Any]]:
    """Export complete user-scoped database snapshot."""
    backup_data = backup_service.generate_backup(user_id=current_user.id)
    return GenericResponse(success=True, data=backup_data)


@router.post(
    "/backup/validate",
    response_model=GenericResponse[BackupValidationResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate Backup Snapshot (Dry-Run)",
    description="Validates schema version and table completeness without modifying database data.",
)
def validate_backup_dry_run(
    payload: dict[str, Any] = Body(..., description="Backup JSON payload"),
    current_user: User = Depends(get_current_user),
    backup_service: BackupService = Depends(get_backup_service),
) -> GenericResponse[BackupValidationResponse]:
    """Dry-run validation of a user backup snapshot."""
    result = backup_service.validate_backup(backup_dict=payload)
    return GenericResponse(success=True, data=result)
