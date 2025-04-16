from sqlalchemy.orm import selectinload
from sqlalchemy import  delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import List

from fastapi import Query, HTTPException, status

from app.db.models import Category, Tag, JournalEntryTag, JournalEntry, JournalEntryCategory

from app.schemas.journal import CategorySchema, TagSchema, CreateJournalEntrySchema

from app.services.queueing import publish_to_queue

from datetime import datetime

from uuid import UUID


async def get_categories(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        limit: int = 10
) -> tuple:
    skip = (page - 1) * limit
    result = await db.execute(
        select(Category).filter(Category.user_id == user_id)
        .order_by(Category.name.asc())
        .offset(skip)
        .limit(limit)
    )
    categories = result.scalars().all()

    if not categories:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categories not found")

    return {"categories": categories}, status.HTTP_200_OK


async def create_journal_category(
        db: AsyncSession,
        category_data: CategorySchema,
        user_id: str
):
    category_name = category_data.category_name

    result = await db.execute(
        select(Category).filter(
            Category.name.ilike(category_name),
            Category.user_id == user_id
        )
    )
    existing_category = result.scalar_one_or_none()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category exists!"
        )

    category = Category(
        name=category_name,
        user_id=user_id
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return {
        "message": "Category created!",
        "category": category
    }, status.HTTP_200_OK


async def update_journal_category(
        db: AsyncSession,
        category_data: CategorySchema,
        user_id: str,
        category_id: str
):
    category_name = category_data.category_name

    result = await db.execute(
        select(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or does not belong to the user."
        )

    category.name = category_name
    await db.commit()
    await db.refresh(category)

    return {
        "message": "Category updated!",
        "category": category
    }, status.HTTP_200_OK


async def delete_journal_category(
        db: AsyncSession,
        category_id: str,
        user_id: str
):
    result = await db.execute(
        select(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or does not belong to the user."
        )

    result = await db.execute(
        select(JournalEntryCategory).filter(
            JournalEntryCategory.category_id == category_id
        )
    )
    category_usage = result.scalar_one_or_none()

    if category_usage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be deleted as it is used in a journal entry."
        )

    # Delete the category
    await db.delete(category)
    await db.commit()

    return {
        "message": "Category deleted successfully!"
    }, status.HTTP_200_OK


async def get_tags(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        limit: int = 10
) -> tuple:
    skip = (page - 1) * limit
    result = await db.execute(
        select(Tag).filter(Tag.user_id == user_id)
        .order_by(Tag.name.asc())
        .offset(skip)
        .limit(limit)
    )
    tags = result.scalars().all()

    if not tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tags not found")

    return {"tags": tags}, status.HTTP_200_OK


async def create_journal_tag(
        db: AsyncSession,
        tag_data: TagSchema,
        user_id: str
):
    tag_name = tag_data.tag_name

    result = await db.execute(
        select(Tag).filter(
            Tag.name.ilike(tag_name),
            Tag.user_id == user_id
        )
    )
    existing_tag = result.scalar_one_or_none()

    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag exists!"
        )

    tag = Tag(
        name=tag_name,
        user_id=user_id
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return {
        "message": "Tag created!",
        "tag": tag
    }, status.HTTP_200_OK


async def update_journal_tag(
        db: AsyncSession,
        tag_data: TagSchema,
        user_id: str,
        tag_id: str
):
    tag_name = tag_data.tag_name

    result = await db.execute(
        select(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found or does not belong to the user."
        )

    tag.name = tag_name
    await db.commit()
    await db.refresh(tag)

    return {
        "message": "Tag updated!",
        "tag": tag
    }, status.HTTP_200_OK


async def delete_journal_tag(
        db: AsyncSession,
        tag_id: str,
        user_id: str
):
    result = await db.execute(
        select(Tag).filter(
            Tag.id == tag_id,
            Tag.user_id == user_id
        )
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found or does not belong to the user."
        )

    # Check if the tag is being used in any journal entries
    result = await db.execute(
        select(JournalEntryTag).filter(
            JournalEntryTag.tag_id == tag_id
        )
    )
    tag_usage = result.scalar_one_or_none()

    if tag_usage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag cannot be deleted as it is used in a journal entry."
        )

    await db.delete(tag)
    await db.commit()

    return {
        "message": "Tag deleted successfully!"
    }, status.HTTP_200_OK


async def create_journal_entry(
    db: AsyncSession,
    parsed_data: CreateJournalEntrySchema,
    user_id: str,
):
    title = parsed_data.title or ""
    content = parsed_data.content
    tags = parsed_data.tags or []
    categories = parsed_data.categories or []

    # Create the journal entry
    journal_entry = JournalEntry(
        title=title,
        content=content,
        user_id=user_id,
        entry_date=datetime.now(),
    )

    db.add(journal_entry)
    await db.flush()

    # Handle tags
    for tag_name in tags:
        tag_name = tag_name.lower()

        result = await db.execute(
            select(Tag).filter_by(name=tag_name, user_id=user_id)
        )
        tag = result.scalars().first()

        if not tag:
            tag = Tag(name=tag_name, user_id=user_id)
            db.add(tag)
            await db.flush()

        tag_assoc = JournalEntryTag(journal_id=journal_entry.id, tag_id=tag.id)
        db.add(tag_assoc)

    # Handle categories
    for category_name in categories:
        category_name = category_name.lower()

        result = await db.execute(
            select(Category).filter_by(name=category_name, user_id=user_id)
        )
        category = result.scalars().first()

        if not category:
            category = Category(name=category_name, user_id=user_id)
            db.add(category)
            await db.flush()

        category_assoc = JournalEntryCategory(
            journal_id=journal_entry.id, category_id=category.id
        )
        db.add(category_assoc)

    await db.commit()

    # Eager-load the relationships to avoid lazy loading in async context
    result = await db.execute(
        select(JournalEntry)
        .options(
            selectinload(JournalEntry.tags),
            selectinload(JournalEntry.categories),
        )
        .filter(JournalEntry.id == journal_entry.id)
    )
    journal_entry = result.scalars().first()

    journal_dict = {
        "id": str(journal_entry.id),
        "title": journal_entry.title,
        "content": journal_entry.content,
        "entryDate": journal_entry.entry_date.isoformat(),
        "userId": str(journal_entry.user_id),
        "tags": [tag.name for tag in journal_entry.tags],
        "categories": [cat.name for cat in journal_entry.categories],
    }

    publish_to_queue("", "entry_queue", journal_dict)

    return {"message": "Entry created!", "journal": journal_dict}, status.HTTP_201_CREATED


async def update_journal_entry(
    db: AsyncSession,
    update_data: CreateJournalEntrySchema,
    user_id: str,
    journal_id: str
):

    result = await db.execute(
        select(JournalEntry).filter_by(id=journal_id, user_id=user_id)
    )
    journal = result.scalars().first()

    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    journal.title = update_data.title
    journal.content = update_data.content

    await db.execute(
        delete(JournalEntryTag).filter_by(journal_entry_id=journal_id)
    )
    await db.execute(
        delete(JournalEntryCategory).filter_by(journal_entry_id=journal_id)
    )

    # Handle updated tags
    for tag_name in update_data.tags:
        tag_name = tag_name.lower()
        result = await db.execute(
            select(Tag).filter_by(name=tag_name, user_id=user_id)
        )
        tag = result.scalars().first()
        if not tag:
            tag = Tag(name=tag_name, user_id=user_id)
            db.add(tag)
            await db.flush()
        db.add(JournalEntryTag(journal_entry_id=journal_id, tag_id=tag.id))

    # Handle updated categories
    for category_name in update_data.categories:
        category_name = category_name.lower()
        result = await db.execute(
            select(Category).filter_by(name=category_name, user_id=user_id)
        )
        category = result.scalars().first()
        if not category:
            category = Category(name=category_name, user_id=user_id)
            db.add(category)
            await db.flush()
        db.add(JournalEntryCategory(journal_entry_id=journal_id, category_id=category.id))

    await db.commit()

    # Reload updated entry with relations
    result = await db.execute(
        select(JournalEntry)
        .options(
            selectinload(JournalEntry.tags),
            selectinload(JournalEntry.categories),
        )
        .filter(JournalEntry.id == journal_id)
    )
    journal = result.scalars().first()

    journal_dict = {
        "id": str(journal.id),
        "title": journal.title,
        "content": journal.content,
        "entryDate": journal.entry_date.isoformat(),
        "userId": str(journal.user_id),
        "tags": [tag.name for tag in journal.tags],
        "categories": [cat.name for cat in journal.categories],
    }

    publish_to_queue("", "entry_queue", journal_dict)

    return {"message": "Journal updated successfully"}, status.HTTP_200_OK


async def delete_journal_entry(
    db: AsyncSession,
    journal_id: str,
    user_id: str,
):

    result = await db.execute(
        select(JournalEntry).filter_by(id=journal_id, user_id=user_id)
    )
    journal = result.scalars().first()

    if not journal:
        raise HTTPException(status_code=404, detail="Entry not found")

    await db.execute(
        delete(JournalEntry).filter_by(id=journal_id, user_id=user_id)
    )
    await db.commit()

    return {"message": "Entry deleted"}, status.HTTP_200_OK

async def get_journal_entries(
    db: AsyncSession,
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
):
    offset = (page - 1) * limit

    result = await db.execute(
        select(JournalEntry)
        .filter(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.entry_date.desc())
        .offset(offset)
        .limit(limit)
        .options(
            selectinload(JournalEntry.categories),
            selectinload(JournalEntry.tags),
        )
    )

    journals: List[JournalEntry] = result.scalars().all()

    return [
        {
            "id": str(journal.id),
            "user_id": str(journal.user_id),
            "entry_date": journal.entry_date.isoformat(),
            "categories": [{"id": str(category.id), "name": category.name} for category in journal.categories],
            "tags": [{"id": str(tag.id), "name": tag.name} for tag in journal.tags],
        }
        for journal in journals
    ], status.HTTP_200_OK


async def get_journal_entry(
        db: AsyncSession,
        journal_id: str,
        user_id: str,
):
    result = await db.execute(
        select(JournalEntry)
        .filter_by(id=journal_id, user_id=user_id)
        .options(
            selectinload(JournalEntry.categories),
            selectinload(JournalEntry.tags)
        )
    )

    journal = result.scalars().first()

    if not journal:
        raise HTTPException(status_code=404, detail="Entry not found")

    if journal.categories is None or journal.tags is None:
        raise HTTPException(status_code=400, detail="Categories or tags not loaded properly.")

    return {journal}, status.HTTP_200_OK
