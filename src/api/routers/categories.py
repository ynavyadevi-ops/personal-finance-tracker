"""FastAPI router for categories management and selection."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.db.models.category import CategoryType
from src.db.models.user import User
from src.db.session import get_db
from src.repositories.category_repo import CategoryRepository
from src.schemas.category import CategoryRead
from src.schemas.common import GenericResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=GenericResponse[list[CategoryRead]],
    status_code=status.HTTP_200_OK,
    summary="List Accessible Categories",
    description="List all categories accessible to the authenticated user (including global default categories).",
)
def list_categories(
    category_type: CategoryType | None = Query(None, description="Filter by category type (INCOME or EXPENSE)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenericResponse[list[CategoryRead]]:
    """Retrieve list of user's personal categories plus system defaults."""
    repo = CategoryRepository(db)
    categories = repo.list_by_user(
        user_id=current_user.id,
        category_type=category_type,
        include_defaults=True,
    )
    result = [CategoryRead.model_validate(c) for c in categories]
    return GenericResponse(success=True, data=result)
