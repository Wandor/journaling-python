from datetime import datetime, timedelta

from typing import List, Dict

from app.db import Mood, TimeOfDay



def is_stop_word(word: str) -> bool:
    stop_words = {
        "the", "is", "at", "of", "and", "a", "in", "to", "for",
        "on", "with", "by", "an", "this", "that", "it", "he",
        "she", "we", "you", "they", "or", "so",
    }
    return word.lower() in stop_words

def determine_mood(sentiment: dict) -> Mood:
    score = sentiment.get("score", 0)
    if score > 0:
        return Mood.POSITIVE
    elif score < 0:
        return Mood.NEGATIVE
    return Mood.NEUTRAL

def determine_time_of_day(date: datetime) -> TimeOfDay:
    entry_date = datetime.fromisoformat(date)
    hour = entry_date.hour
    if 5 <= hour < 12:
        return TimeOfDay.MORNING
    elif 12 <= hour < 18:
        return TimeOfDay.AFTERNOON
    return TimeOfDay.EVENING

def calculate_analytics(content: str) -> dict:
    words = content.split()
    word_count = len(words)
    character_count = len(content)
    sentence_count = len([s for s in content.split('.') if s.strip()])
    reading_time = word_count // 200
    average_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    return {
        "characterCount": character_count,
        "wordCount": word_count,
        "sentenceCount": sentence_count,
        "readingTime": reading_time,
        "averageSentenceLength": average_sentence_length,
    }


def get_week(date: datetime) -> tuple:
    year, week_num, _ = date.isocalendar()

    return year, week_num




def get_overall_mood_per_day(mood_trends: List[Dict[str, any]]) -> Dict[str, Mood]:
    moods_per_day: Dict[str, Dict[str, int]] = {}

    for entry in mood_trends:
        date = entry["date"].split("T")[0]
        if date not in moods_per_day:
            moods_per_day[date] = {"totalScore": 0, "count": 0}
        moods_per_day[date]["totalScore"] += entry["score"]
        moods_per_day[date]["count"] += 1

    overall_mood_per_day: Dict[str, Mood] = {}
    for date, stats in moods_per_day.items():
        average_score = stats["totalScore"] / stats["count"]
        if average_score >= 7:
            overall_mood_per_day[date] = Mood.POSITIVE
        elif average_score >= 4:
            overall_mood_per_day[date] = Mood.NEUTRAL
        else:
            overall_mood_per_day[date] = Mood.NEGATIVE

    return overall_mood_per_day