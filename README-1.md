# ربات تلگرامی پیدا کردن انیمه

## نحوه‌ی کارکرد
- ارسال **متن** (اسم انیمه) → جستجو در **Jikan API** (بر پایه MyAnimeList)
- ارسال **عکس** (اسکرین‌شات از انیمه) → تشخیص با **trace.moe** → گرفتن جزئیات از **AniList**

هر دو سرویس (Jikan، trace.moe، AniList) کاملاً رایگان و بدون نیاز به کلید API هستند.

---

## مرحله ۱: آماده‌سازی روی گیت‌هاب
1. یک ریپازیتوری جدید (خصوصی ترجیحاً) در گیت‌هاب بساز.
2. تمام فایل‌های این پوشه **به‌جز `.env`** رو push کن (`.env` اصلاً نباید ساخته بشه، `.gitignore` جلوش رو می‌گیره).

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin <آدرس-ریپازیتوری-تو>
git push -u origin main
```

## مرحله ۲: ساخت سرویس در Render
1. وارد [render.com](https://render.com) شو و با گیت‌هاب لاگین کن.
2. **New → Web Service** رو بزن و ریپازیتوری بالا رو انتخاب کن (پلن Free فقط برای Web Service در دسترسه، نه Background Worker).
3. تنظیمات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** Free

## مرحله ۳: تنظیم متغیر محیطی
1. توی تب **Environment** سرویس، یک متغیر اضافه کن:
   - Key: `BOT_TOKEN`
   - Value: توکن **جدیدی** که از BotFather گرفتی (چون توکن قبلی لو رفته، حتماً با `/revoke` عوضش کن)

## مرحله ۴: اجرا
- چون پلن Free فقط برای Web Service هست و Render انتظار داره روی یک پورت HTTP جواب بدی، توی `main.py` یک سرور سبک (`aiohttp`) اضافه شده که فقط به health check جواب می‌ده؛ منطق اصلی ربات همچنان polling هست.
- توی تب **Logs** مطمئن شو ربات بالا اومده (باید `Health server listening on port ...` و بعدش شروع polling رو ببینی، بدون ارور).
- نکته: پلن Free بعد از ۱۵ دقیقه بدون ترافیک ورودی spin down می‌شه و درخواست بعدی با تأخیر (cold start) بالا میاد؛ چون health server داخلی هست نه ترافیک خارجی واقعی، ممکنه لازم باشه یک سرویس مانیتورینگ رایگان (مثل UptimeRobot) هر چند دقیقه به آدرس سرویس پینگ بزنه تا بیدار بمونه.
- حالا برو توی تلگرام و به ربات پیام بده.

---

## نکات مهم امنیتی
- توکن ربات و کلیدهای API رو **هیچ‌وقت** توی کد هاردکد نکن یا جایی به‌صورت متن ساده به اشتراک نذار.
- اگر توکنی لو رفت، بلافاصله revoke/regenerate کن.
- ریپازیتوری گیت‌هاب رو خصوصی نگه دار.

## تست محلی (اختیاری، قبل از deploy)
```bash
pip install -r requirements.txt
export BOT_TOKEN=توکن_جدید_تو
python main.py
```
