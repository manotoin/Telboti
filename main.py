import os
import re
import io
import logging
import asyncio

import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("متغیر محیطی BOT_TOKEN تنظیم نشده است.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ANILIST_URL = "https://graphql.anilist.co"
TRACE_MOE_URL = "https://api.trace.moe/search"
JIKAN_URL = "https://api.jikan.moe/v4/anime"

ANILIST_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    title { romaji english native }
    description(asHtml: false)
    startDate { year }
    averageScore
    genres
    siteUrl
  }
}
"""


def clean_html(raw: str) -> str:
    if not raw:
        return "توضیحاتی موجود نیست."
    text = re.sub(r"<br\s*/?>", "\n", raw)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def truncate(text: str, limit: int = 400) -> str:
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


async def search_by_image(image_bytes: bytes) -> str:
    try:
        resp = requests.post(
            TRACE_MOE_URL,
            data=image_bytes,
            headers={"Content-Type": "image/jpeg"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logging.error(f"trace.moe error: {e}")
        return "خطا در ارتباط با سرویس تشخیص تصویر. دوباره امتحان کن."

    results = data.get("result") or []
    if not results:
        return "متأسفانه هیچ انیمه‌ای با این تصویر پیدا نشد 😕"

    best = results[0]
    anilist_id = best.get("anilist")
    similarity = round(best.get("similarity", 0) * 100, 1)

    if not anilist_id:
        return "انیمه پیدا شد ولی جزئیات بیشتری در دسترس نیست."

    try:
        al_resp = requests.post(
            ANILIST_URL,
            json={"query": ANILIST_QUERY, "variables": {"id": anilist_id}},
            timeout=20,
        )
        al_resp.raise_for_status()
        media = al_resp.json()["data"]["Media"]
    except (requests.RequestException, KeyError, TypeError) as e:
        logging.error(f"AniList error: {e}")
        return "انیمه شناسایی شد ولی گرفتن جزئیات با خطا مواجه شد."

    title = media["title"].get("romaji") or media["title"].get("english") or "نامشخص"
    year = media.get("startDate", {}).get("year", "نامشخص")
    score = media.get("averageScore")
    score_txt = f"{score / 10:.1f}/10" if score else "نامشخص"
    description = truncate(clean_html(media.get("description", "")))

    return (
        f"🎬 <b>{title}</b>\n"
        f"📅 سال: {year}\n"
        f"⭐ امتیاز: {score_txt}\n"
        f"🔍 میزان تطابق تصویر: {similarity}%\n\n"
        f"📝 {description}\n\n"
        f"🔗 {media.get('siteUrl', '')}"
    )


async def search_by_text(query: str) -> str:
    try:
        resp = requests.get(JIKAN_URL, params={"q": query, "limit": 1}, timeout=20)
        resp.raise_for_status()
        data = resp.json().get("data") or []
    except requests.RequestException as e:
        logging.error(f"Jikan error: {e}")
        return "خطا در ارتباط با سرویس اطلاعات انیمه. دوباره امتحان کن."

    if not data:
        return "انیمه‌ای با این اسم پیدا نشد. اسم رو کامل‌تر یا متفاوت بنویس."

    anime = data[0]
    title = anime.get("title", "نامشخص")
    year = anime.get("year", "نامشخص")
    score = anime.get("score", "نامشخص")
    synopsis = truncate(anime.get("synopsis") or "توضیحاتی موجود نیست.")
    url = anime.get("url", "")

    return (
        f"🎬 <b>{title}</b>\n"
        f"📅 سال: {year}\n"
        f"⭐ امتیاز: {score}\n\n"
        f"📝 {synopsis}\n\n"
        f"🔗 {url}"
    )


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "سلام! 👋\n"
        "اسم یک انیمه رو بفرست یا یک عکس (اسکرین‌شات) ازش بذار تا برات پیداش کنم 🎬"
    )


@dp.message(lambda msg: msg.photo)
async def photo_handler(message: types.Message):
    await message.answer("در حال جستجو... ⏳")
    file = await bot.get_file(message.photo[-1].file_id)
    buf = await bot.download_file(file.file_path)
    result = await search_by_image(buf.read())
    await message.answer(result, parse_mode="HTML")


@dp.message()
async def text_handler(message: types.Message):
    if not message.text:
        return
    await message.answer("در حال جستجو... ⏳")
    result = await search_by_text(message.text.strip())
    await message.answer(result, parse_mode="HTML")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
