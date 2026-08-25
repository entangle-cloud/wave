import re 
import uuid 

from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select 
from database.database import get_db
from database import Category as CategoryModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/category", tags=["categories"])
DB = Annotated[AsyncSession, Depends(get_db)]

class Category(BaseModel):
    name: str
    description: str
    color: str
    parent_category: int| None = None

@router.get("/categories")
async def get_categories(db:DB):
    result = await db.execute(select(CategoryModel))
    categories = result.scalars().all()
    return categories

@router.delete("/{category_id}")
async def delete_category(category_id: int, db: DB):
    result = await db.execute(select(CategoryModel).where(CategoryModel.id == category_id))
    db_category = result.scalar_one_or_none()
    if db_category is None: 
        raise HTTPException(status_code=404, detail="Category not found")
    
    check_children = await db.execute(select(CategoryModel).where(CategoryModel.parent_id == category_id))
    child_categories = check_children.scalar_one_or_none()
    
    if child_categories is not None:
        raise HTTPException(status_code=401, detail="Unable to delete category. Delete child categories first")
    await db.delete(db_category)
    await db.commit()
    return {"detail": "deleted"}

@router.post("")
async def create_category(category: Category, db: DB):

    db_category = CategoryModel(
    name = category.name, 
    description= category.description,
    colour=category.color,
    slug=re.sub(r"[^a-z0-9]+", "-", category.name.lower()).strip("-"), 
    parent_id = category.parent_category
    )
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category