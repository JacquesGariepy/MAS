from typing import Any, List, TypeVar, Generic
from sqlalchemy.orm import Query
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class PaginationResult(BaseModel, Generic[T]):
    """Generic pagination result"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

def paginate(query: Query, page: int, per_page: int, model: Any) -> dict:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Current page number (1-indexed)
        per_page: Items per page
        model: Pydantic model for serialization
    
    Returns:
        Dictionary with pagination data
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Get total count
    total = query.count()
    
    # Calculate total pages
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    # Get items for current page
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Serialize items using Pydantic model
    serialized_items = [model.from_orm(item) for item in items]
    
    return {
        "items": serialized_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages
    }