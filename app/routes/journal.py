from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authenticator import authenticate_user, authorize
from app.schemas.auth import  AuthenticatedUser

from app.controllers import journal as journal
from app.controllers import summary as summary
from app.db.session import get_db


from app.schemas.journal import CategorySchema, TagSchema, CreateJournalEntrySchema

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.get("/list-categories")
async def get_categories(
    user: AuthenticatedUser = Depends(authenticate_user),
        _=Depends(authorize(["ADMIN", "USER"])),
    db: AsyncSession = Depends(get_db)
):
    result, code = await journal.get_categories(db=db, user_id=user.user_id)

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/create-category")
async def create_category(request: CategorySchema,     user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])),  db: AsyncSession = Depends(get_db)):

    result, code = await journal.create_journal_category(db, request, user_id=str(user.user_id))

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.put("/update-category/{categoryId}")
async def update_category(categoryId: str, request: CategorySchema, user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])), db: AsyncSession = Depends(get_db)):

    result, code = await journal.update_journal_category(db, request, user_id=str(user.user_id), category_id=categoryId)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.delete("/delete-category/{categoryId}")
async def delete_category(categoryId: str,  user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])), db: AsyncSession = Depends(get_db)):

    result, code = await journal.delete_journal_category(db,  category_id=categoryId, user_id=str(user.user_id),)

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.get("/list-tags")
async def get_tags(
    user: AuthenticatedUser = Depends(authenticate_user),
        _=Depends(authorize(["ADMIN", "USER"])),
    db: AsyncSession = Depends(get_db)
):
    result, code = await journal.get_tags(db=db, user_id=user.user_id)

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.post("/create-tag")
async def create_tag(request: TagSchema,     user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])),  db: AsyncSession = Depends(get_db)):

    result, code = await journal.create_journal_tag(db, request, user_id=str(user.user_id))

    print(result)
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.put("/update-tag/{tagId}")
async def update_tag(tagId: str, request: TagSchema, user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])), db: AsyncSession = Depends(get_db)):

    result, code = await journal.update_journal_tag(db, request, user_id=str(user.user_id), tag_id=tagId)

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.delete("/delete-tag/{tagId}")
async def delete_tag(tagId: str,  user: AuthenticatedUser = Depends(authenticate_user), _=Depends(authorize(["ADMIN", "USER"])), db: AsyncSession = Depends(get_db)):

    result, code = await journal.delete_journal_tag(db,  tag_id=tagId, user_id=str(user.user_id))

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result



@router.post("/create-entry")
async def create_entry(
        request: CreateJournalEntrySchema,
        user: AuthenticatedUser = Depends(authenticate_user),
        _: None = Depends(authorize(["ADMIN", "USER"])),
        db: AsyncSession = Depends(get_db)
):

        result, code = await journal.create_journal_entry(
            db=db,
            parsed_data=request,
            user_id=str(user.user_id)
        )

        if "error" in result:
            raise HTTPException(status_code=code, detail=result["error"])
        return result


@router.put("/update-entry/{entryId}")
async def update_entry(
        entryId: str,
        request: CreateJournalEntrySchema,
        user: AuthenticatedUser = Depends(authenticate_user),
        _: None = Depends(authorize(["ADMIN", "USER"])),

        db: AsyncSession = Depends(get_db)
):

        result, code = await journal.update_journal_entry(
            db=db,
            update_data=request,
            user_id=str(user.user_id),
            journal_id=entryId
        )

        if "error" in result:
            raise HTTPException(status_code=code, detail=result["error"])
        return result

@router.delete("/delete-entry/{entryId}")
async def delete_entry(
        entryId: str,
        user: AuthenticatedUser = Depends(authenticate_user),
        _: None = Depends(authorize(["ADMIN", "USER"])),
        db: AsyncSession = Depends(get_db)
):

        result, code = await journal.delete_journal_entry(
            db=db,
            user_id=str(user.user_id),
            journal_id=entryId
        )

        if "error" in result:
            raise HTTPException(status_code=code, detail=result["error"])
        return result


@router.get("/list-entries")
async def get_journal_entries(
    user: AuthenticatedUser = Depends(authenticate_user),
    _=Depends(authorize(["ADMIN", "USER"])),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),  # Default to page 1, with a minimum of 1
    limit: int = Query(10, le=100)  # Default to 10 entries per page, with a max of 100
):
    # Call the updated function to get journal entries, passing in pagination params
    result, code = await journal.get_journal_entries(db=db, user_id=str(user.user_id), page=page, limit=limit)

    # Check if there's an error in the result and raise an HTTPException
    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])

    # Return the journal entries result
    return result

@router.get("/view-entry/{entryId}")
async def view_entry(
        entryId: str,
        user: AuthenticatedUser = Depends(authenticate_user),
        _: None = Depends(authorize(["ADMIN", "USER"])),
        db: AsyncSession = Depends(get_db)
):

        result, code = await journal.get_journal_entry(
            db=db,
            user_id=str(user.user_id),
            journal_id=entryId
        )

        if "error" in result:
            raise HTTPException(status_code=code, detail=result["error"])
        return result

@router.get("/summary")
async def journal_summary(
    start_date: str = Query(None),
    end_date: str = Query(None),
    user: AuthenticatedUser = Depends(authenticate_user),
    _: None = Depends(authorize(["ADMIN", "USER"])),
    db: AsyncSession = Depends(get_db),
):
    result, code = await summary.get_journal_summary(
        user_id=str(user.user_id),
        db=db,
        start=start_date,
        end=end_date
    )

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result


@router.get("/sentiment-extremes")
async def sentiment_extremes(
    start_date: str = Query(None),
    end_date: str = Query(None),
    user: AuthenticatedUser = Depends(authenticate_user),
    _: None = Depends(authorize(["ADMIN", "USER"])),
    db: AsyncSession = Depends(get_db),
):
    result, code = await summary.get_sentiment_extremes(
        user_id=str(user.user_id),
        db=db,
        start_date=start_date,
        end_date=end_date
    )

    if "error" in result:
        raise HTTPException(status_code=code, detail=result["error"])
    return result