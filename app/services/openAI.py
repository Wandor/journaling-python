from openai import OpenAI


from collections import Counter
import re
import spacy

import json


from app.core.config import settings
from app.core.logger import logger

client = OpenAI(api_key=settings.OPENAI_API_KEY)

nlp_spacy = spacy.load("en_core_web_sm")


STOP_WORDS = set(nlp_spacy.Defaults.stop_words)

def is_stop_word(word):
    return word.lower() in STOP_WORDS



def analyze_sentiment_openai(text: str):
    try:
        prompt = f"""Analyze the sentiment of the following text. Return a JSON object with the following fields:

- "score": total sentiment score from -1 (negative) to 1 (positive)
- "magnitude": the absolute strength of sentiment (sum of positive and negative weights)
- "comparative": score divided by the number of meaningful words (i.e., score per word)
- "emotion": overall emotion (e.g., Happy, Sad, Neutral, Angry)
- "positive": array of positive words found
- "negative": array of negative words found
- "calculation": a brief explanation of how the score was derived

Text: "{text}" """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that performs sentiment analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Increased token limit to avoid cutoff
            temperature=0.3
        )

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError as decode_err:
            logger.error(f"JSON decode error: {decode_err} | Content: {content}")
            return {
                "score": 0,
                "magnitude": 0,
                "comparative": 0,
                "emotion": "Neutral",
                "positive": [],
                "negative": [],
                "calculation": "Failed to parse OpenAI response"
            }

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return {
            "score": 0,
            "magnitude": 0,
            "comparative": 0,
            "emotion": "Neutral",
            "positive": [],
            "negative": [],
            "calculation": "API call failed"
        }

def entry_analysis(text: str):
    try:
        prompt = f"""Analyze the following journal entry and suggest a short descriptive title, a summary of the content, categories (Personal, Work, Travel, Health, Relationships, Miscellaneous), and relevant tags. Output the result in the following JSON format:

{{
  "title": "title",
  "summary": "summary",
  "categories": ["category1", "category2", ...],
  "tags": ["tag1", "tag2", ...]
}}

Entry: {text}"""

        response =  client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that generates journaling titles, summaries, categories, and tags."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=250)

        content = response.choices[0].message.content
        parsed = json.loads(content)
        return {
            "title": parsed.get("title", "Untitled"),
            "summary": parsed.get("summary", "No summary available."),
            "categories": parsed.get("categories", ["Miscellaneous"]),
            "tags": parsed.get("tags", [])
        }
    except Exception as e:
        logger.error(e)
        return {
            "title": "Untitled",
            "summary": "No summary available.",
            "categories": ["Miscellaneous"],
            "tags": []
        }

def generate_tags(text: str):
    doc = nlp_spacy(text)
    words = [token.text.lower() for token in doc if token.is_alpha and not is_stop_word(token.text)]
    freq = Counter(words)
    return [word for word, _ in freq.most_common(5)]

async def summarize_entry(text: str):
    try:
        response =  client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text concisely in the first person."},
            {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
        ])
        return response.choices[0].message.content
    except Exception as e:
        logger.error("Error summarizing entry: %s", e)
        return "Error generating summary"

async def generate_writing_prompt(previous_entries: list[str]):
    try:
        joined_entries = "\n".join(previous_entries)
        prompt = (
            "Based on the following past journal entries, suggest a new writing prompt:\n\n"
            f"{joined_entries}\n\nSuggested Prompt:"
        )

        response =  client.completions.create(model="gpt-4-turbo",
        prompt=prompt,
        max_tokens=50)
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error("Writing Prompt Error: %s", e)
        return "Write about something that made you happy today."


async def detect_themes(entries: list[str]):
    try:
        content = "\n\n".join(entries)
        response =  client.chat.completions.create(model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that helps analyze journal entries."},
            {"role": "user", "content": f"Analyze the following journal entries and detect recurring themes. Return a list of themes in JSON format and include one theme that stands out:\n\n{content}"}
        ],
        max_tokens=100)
        clean_content = response.choices[0].message.content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean_content)
    except Exception as e:
        logger.error("Theme Detection Error: %s", e)
        return ["General Reflection"]

def detect_word_trends(entries: list[str]) -> dict[str, int]:
    word_count = {}
    for entry in entries:
        words = re.findall(r"\b[a-z]+\b", entry.lower())
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1
    return word_count

async def summarize_entries(entries: list[str]):
    try:
        joined_entries = "\n\n".join(entries)
        prompt = (
            "Summarize the following journal entries into key takeaways:\n\n"
            f"{joined_entries}"
        )
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes journal entries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        content = response.choices[0].message.content
        return content.strip() if isinstance(content, str) else str(content)
    except Exception as e:
        logger.error("Summary Generation Error: %s", e)
        return "No summary available."


