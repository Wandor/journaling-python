from aio_pika import IncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload

from sqlalchemy.dialects.postgresql import insert

from app.db import engine
from app.db.models import (
    JournalEntry, UserPreferences, SentimentScore,
    Tag, Category, JournalEntryTag, JournalEntryCategory,
    AnalyticsData
)
from app.utils.functions import calculate_analytics, determine_time_of_day, determine_mood
from app.services.openAI import analyze_sentiment_openai, entry_analysis
from app.core.logger import logger
import json
from datetime import datetime

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def rabbitmq_handler(message: IncomingMessage):
    async with message.process():
        try:
            msg_body = message.body
            async with SessionLocal() as session:
                await journal_entry_worker(msg_body, session)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

async def journal_entry_worker(msg_body: bytes, db: AsyncSession):
    data = json.loads(msg_body.decode())

    content = data.get("content")
    journal_id = data.get("id")
    title = data.get("title")
    user_id = data.get("userId")
    entry_date = data.get("entryDate", datetime.now().isoformat())

    try:
        # Ensure the database session is queried asynchronously
        user_pref_result = await db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        user_preferences = user_pref_result.scalars().first()

        auto_categorize = user_preferences.auto_categorize if user_preferences else False
        auto_tag = user_preferences.auto_tag if user_preferences else False
        summarize = user_preferences.summarize if user_preferences else False

        sentiment_analysis = analyze_sentiment_openai(content)
        mood = determine_mood(sentiment_analysis)

        # Store sentiment score
        sentiment_score = SentimentScore(
            journal_id=journal_id,
            score=sentiment_analysis["score"],
            magnitude=sentiment_analysis["comparative"],
            mood=mood,
            calculation=sentiment_analysis["calculation"],
            positive_words=",".join(sentiment_analysis["positive"]),
            negative_words=",".join(sentiment_analysis["negative"]),
        )
        db.add(sentiment_score)
        await db.flush()

        # Journal entry analysis
        analysis = entry_analysis(content)
        analysis_title = analysis.get("title")
        summary = analysis.get("summary")
        categories = analysis.get("categories", [])
        tags = analysis.get("tags", [])

        update_fields = {}
        if not title:
            update_fields["title"] = analysis_title
        if summarize:
            update_fields["summary"] = summary

        entry_result = await db.execute(
            select(JournalEntry)
            .options(
                selectinload(JournalEntry.tags),
                selectinload(JournalEntry.categories)
            )
            .where(JournalEntry.id == journal_id)
        )
        existing_entry = entry_result.scalars().first()

        # Auto-tagging
        if auto_tag:
            existing_tags = {tag.name for tag in existing_entry.tags}
            new_tags = [tag.upper() for tag in tags if tag.upper() not in existing_tags]
            for tag_name in new_tags:
                tag_result = await db.execute(
                    select(Tag).where(Tag.name == tag_name, Tag.user_id == user_id)
                )
                tag = tag_result.scalars().first()
                if not tag:
                    tag = Tag(name=tag_name, user_id=user_id)
                    db.add(tag)
                    await db.flush()  # Ensure to flush tag to DB asynchronously
                db.add(JournalEntryTag(journal_entry_id=journal_id, tag_id=tag.id))
        #
        # Auto-categorizing
        if auto_categorize:
            existing_cats = {cat.name for cat in existing_entry.categories}
            new_cats = [cat.upper() for cat in categories if cat.upper() not in existing_cats]
            for cat_name in new_cats:
                cat_result = await db.execute(
                    select(Category).where(Category.name == cat_name, Category.user_id == user_id)
                )
                category = cat_result.scalars().first()
                if not category:
                    category = Category(name=cat_name, user_id=user_id)
                    db.add(category)
                    await db.flush()  # Ensure to flush category to DB asynchronously
                db.add(JournalEntryCategory(journal_entry_id=journal_id,  category_id=category.id))

        if update_fields:
            await db.execute(
                update(JournalEntry)
                .where(JournalEntry.id == journal_id)
                .values(**update_fields)
            )

        # Calculate analytics data
        analytics_data = calculate_analytics(content)
        time_of_day = determine_time_of_day(entry_date)


        stmt = insert(AnalyticsData).values(
            journal_id=journal_id,
            tags_count=len(existing_entry.tags),
            categories_count=len(existing_entry.categories),
            time_of_day=time_of_day,
            entry_date= datetime.fromisoformat(entry_date),
            word_count= analytics_data["wordCount"],
            character_count= analytics_data["characterCount"],
            sentence_count= analytics_data["sentenceCount"],
            reading_time= analytics_data["readingTime"],
            average_sentence_length= analytics_data["averageSentenceLength"],
        )

        update_dict = {
            "tags_count": len(existing_entry.tags),
            "categories_count": len(existing_entry.categories),
            "time_of_day": time_of_day,
            "entry_date": datetime.fromisoformat(entry_date),
            "word_count": analytics_data["wordCount"],
            "character_count": analytics_data["characterCount"],
            "sentence_count": analytics_data["sentenceCount"],
            "reading_time": analytics_data["readingTime"],
            "average_sentence_length": analytics_data["averageSentenceLength"],
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=["journal_id"],
            set_=update_dict,
        )

        await db.execute(stmt)


        await db.commit()

    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing journal entry {journal_id}: {e}")
