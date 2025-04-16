from fastapi import status, Query,HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from typing import List, Dict, Optional

from datetime import datetime

from sqlalchemy import func

from collections import defaultdict

from app.core.error_handler import logger
from app.db.models import JournalEntry, SentimentScore, AnalyticsData, Category
from app.utils.functions import get_week, get_overall_mood_per_day


# Helper function to get the start and end dates from the query params
def get_start_end_dates(start_date: Optional[str], end_date: Optional[str]):
    now = datetime.now()
    start = (
        datetime.fromisoformat(start_date)
        if start_date
        else datetime(now.year, 1, 1)
    )
    end = (
        datetime.fromisoformat(end_date)
        if end_date
        else now
    )
    return start, end

async def get_journal_summary(
    user_id: str,
    db: AsyncSession,
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
):
    try:
        start_date, end_date = get_start_end_dates(start, end)

        total_entries_result = await db.execute(
            select(func.count(JournalEntry.id)).filter(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
            )
        )
        total_entries = total_entries_result.scalar()

        if total_entries == 0:
            return {"message": "No entries found"}, 404

        analytics_result = await db.execute(
            select(AnalyticsData)
            .join(JournalEntry)
            .filter(
                JournalEntry.user_id == user_id,
                AnalyticsData.entry_date >= start_date,
                AnalyticsData.entry_date <= end_date,
            )
            .options(selectinload(AnalyticsData.journal_entry))
        )


        analytics = analytics_result.scalars().all()

        for entry in analytics:
            print(f"Entry: {entry.id}, word_count: {entry.word_count}, date: {entry.entry_date.date()}")

        print(analytics, 'someresult', total_entries, get_week(end_date))
        sentiment_result = await db.execute(
            select(SentimentScore)
            .join(JournalEntry)
            .filter(
                JournalEntry.user_id == user_id,
                SentimentScore.created_at >= start_date,
                SentimentScore.created_at <= end_date,
            )
        )
        sentiment_data = sentiment_result.scalars().all()



        avg_word_count = sum(entry.word_count for entry in analytics) / total_entries if total_entries else 0

        word_count_trends = defaultdict(int)
        total_words_per_year = defaultdict(int)
        total_words_per_week = defaultdict(int)
        total_entries_per_year = defaultdict(int)
        total_entries_per_week = defaultdict(int)
        grouped_entries = defaultdict(int)
        time_of_day_analysis = defaultdict(int)

        for entry in analytics:
            entry_date = entry.entry_date.date()
            word_count_trends[entry_date.isoformat()] += entry.word_count

            year, week = get_week(entry.entry_date)


            total_words_per_year[year] += entry.word_count
            total_words_per_week[week] += entry.word_count
            total_entries_per_year[year] += 1
            total_entries_per_week[week] += 1
            grouped_entries[entry_date.isoformat()] += 1

            if entry.time_of_day:
                time_of_day_analysis[entry.time_of_day] += 1

        distinct_days_journaled = len(set(entry.entry_date.date() for entry in analytics))

        mood_summary = {
            "total_score": sum(s.score for s in sentiment_data),
            "max_score": max((s.score for s in sentiment_data), default=float('-inf')),
            "min_score": min((s.score for s in sentiment_data), default=float('inf')),
            "max_mood": max(sentiment_data, key=lambda s: s.score).mood if sentiment_data else "",
            "min_mood": min(sentiment_data, key=lambda s: s.score).mood if sentiment_data else "",
        }



        mood_trends = [
            {
                "date": s.created_at.date().isoformat(),
                "mood": s.mood,
                "score": s.score,
            }
            for s in sentiment_data
        ]
        overall_mood_per_day = get_overall_mood_per_day(mood_trends)

        category_distribution_result = await db.execute(
            select(Category.id, Category.name, func.count(Category.id))
            .join(JournalEntry.categories)
            .filter(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
            )
            .group_by(Category.id)
        )
        category_distribution = category_distribution_result.all()

        category_distribution_with_names = [
            {
                "categoryId": id_,
                "categoryName": name,
                "count": count
            }
            for id_, name, count in category_distribution
        ]

        most_used_category = max(category_distribution, key=lambda c: c[2], default=None)
        most_used_category_name = most_used_category[1] if most_used_category else "No category found"

        heatmap_data = [{"date": date, "count": count} for date, count in grouped_entries.items()]


        summary = {
            "total_entries": total_entries,
            "avg_word_count": avg_word_count,
            "most_used_category": most_used_category_name,
            "word_count_trends": [{"date": k, "wordCount": v} for k, v in word_count_trends.items()],
            "category_distribution": category_distribution_with_names,
            "time_of_day_analysis": dict(time_of_day_analysis),
            "mood_trends": mood_trends,
            "overall_mood_per_day": overall_mood_per_day,
            "total_entries_per_year": dict(total_entries_per_year),
            "total_entries_per_week": dict(total_entries_per_week),
            "total_words_per_year": dict(total_words_per_year),
            "total_words_per_week": dict(total_words_per_week),
            "distinct_days_journaled": distinct_days_journaled,
            "heatmap_data": heatmap_data,
            "mood_summary": mood_summary,
        }

        return summary, status.HTTP_200_OK

    except Exception as error:
        logger.error(error)
        return {"error": str(error)}, status.HTTP_500_INTERNAL_SERVER_ERROR


async def get_sentiment_extremes(
    user_id: str,
    start_date: str,
    end_date: str,
    db: AsyncSession,
):
    try:
        start_date, end_date = get_start_end_dates(start_date, end_date)

        sentiment_data = await db.execute(
            select(SentimentScore)
            .join(JournalEntry)
            .filter(
                JournalEntry.user_id == user_id,
                SentimentScore.created_at >= start_date,
                SentimentScore.created_at <= end_date,
            )
            .options(selectinload(SentimentScore.journal_entry))
        )
        sentiment_data = sentiment_data.scalars().all()

        most_positive = max(sentiment_data, key=lambda s: s.score, default=None)
        most_negative = min(sentiment_data, key=lambda s: s.score, default=None)

        if most_positive and most_negative:
            return {
                "most_positive": {
                    "journal_id": str(most_positive.journal_entry.id),
                    "mood": most_positive.mood,
                    "score": most_positive.score,
                    "content": most_positive.journal_entry.content,
                },
                "most_negative": {
                    "journal_id": str(most_negative.journal_entry.id),
                    "mood": most_negative.mood,
                    "score": most_negative.score,
                    "content": most_negative.journal_entry.content,
                },
            }, 200
        else:
            return {"message": "No sentiment data available for the given range"}, status.HTTP_404_NOT_FOUND

    except Exception as error:
        logger.error(error)
        return {"error": str(error)}, status.HTTP_500_INTERNAL_SERVER_ERROR
