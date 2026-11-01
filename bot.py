import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "9018988662:AAH6L2_CqXOeEi_ymY5hT8AQ9dgwbB60-OE"
ADMIN_ID = 6389871651

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI (SQLite) ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            auto_react INTEGER DEFAULT 1,
            default_emojis TEXT DEFAULT '👍,❤️,🔥,👏,🎉,🤩'
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO settings (id, auto_react, default_emojis) VALUES (1, 1, '👍,❤️,🔥,👏,🎉,🤩')")
    conn.commit()
    conn.close()

init_db()

def get_settings():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT auto_react, default_emojis FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"auto_react": bool(row[0]), "emojis": row[1]}

def update_settings(auto_react=None):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    if auto_react is not None:
        cursor.execute("UPDATE settings SET auto_react = ? WHERE id = 1", (1 if auto_react else 0,))
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# --- PASTKI MENYU (REPLY KEYBOARD) ---
def get_main_keyboard(user_id):
    if user_id == ADMIN_ID:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👑 Admin Panel"), KeyboardButton(text="📊 Statistika")],
                [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="ℹ️ Bot haqida")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="ℹ️ Bot haqida")]
            ],
            resize_keyboard=True
        )
    return keyboard

# --- XABAR OSTIDAGI INLINE TUGMALAR ---
def get_admin_inline_keyboard():
    settings = get_settings()
    status_text = "🟢 Yoqilgan" if settings["auto_react"] else "🔴 O'chirilgan"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⚡ 6 talik avto-reaksiya: {status_text}", callback_data="toggle_react")],
            [InlineKeyboardButton(text="🎭 Reaksiyalar: 👍 ❤️ 🔥 👏 🎉 🤩", callback_data="info_emojis")],
            [InlineKeyboardButton(text="📢 Kanalga botni sozlash", callback_data="channel_info")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton(text="📨 Xabar yuborish", callback_data="broadcast")]
        ]
    )
    return keyboard

# --- BOT BUYRUQLARI VA TUGMALARI ---
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    add_user(message.from_user.id)
    kb = get_main_keyboard(message.from_user.id)
    await message.answer(
        "Salom! 6 talik avto-reaksiya botiga xush kelibsiz. 🤖\nPastdagi menyudan kerakli bo'limni tanlang:",
        reply_markup=kb
    )

@dp.message(F.text == "👑 Admin Panel")
async def open_admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👑 <b>Admin panel boshqaruvi:</b>\n\nQuyidagi tugmalar orqali sozlamalarni boshqaring:",
            parse_mode="HTML",
            reply_markup=get_admin_inline_keyboard()
        )
    else:
        await message.answer("Sizda bu huquq yo'q!")

@dp.message(F.text == "📊 Statistika")
async def menu_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        await message.answer(f"📊 <b>Bot statistikasi:</b>\n\nFoydalanuvchilar: {count} ta", parse_mode="HTML")

@dp.message(F.text == "📢 Xabar yuborish")
async def menu_broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Barcha foydalanuvchilarga xabar yuborish uchun quyidagi formatda yozing:\n<code>/send Sizning xabaringiz</code>", parse_mode="HTML")

@dp.message(F.text == "ℹ️ Bot haqida")
async def about_bot(message: types.Message):
    await message.answer("Bu bot kanallarga har bir post chiqqanda avtomatik ravishda bir vaqtning o'zida 6 ta reaksiya bosadi! 👍❤️🔥👏🎉🤩")

# --- INLINE TUGMALARNI BOSHQARISH ---
@dp.callback_query(F.data == "toggle_react")
async def toggle_react_handler(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        current = get_settings()["auto_react"]
        update_settings(auto_react=not current)
        await call.message.edit_reply_markup(reply_markup=get_admin_inline_keyboard())
        await call.answer("Reaksiya holati o'zgartirildi!")

@dp.callback_query(F.data == "info_emojis")
async def info_emojis_handler(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        await call.answer("Bot har bir yangi postga doimiy ravishda 6 ta emojini (👍, ❤️, 🔥, 👏, 🎉, 🤩) birgalikda bosadi!", show_alert=True)

@dp.callback_query(F.data == "channel_info")
async def channel_info_handler(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        info_text = (
            "📢 <b>Kanalga avto-reaksiya ulash tartibi:</b>\n\n"
            "1. Botni o'zingizning kanalingizga qo'shing.\n"
            "2. Botga kanal sozlamalarida <b>Administrator</b> huquqini bering.\n"
            "3. Admin huquqlarida <b>Postlarni o'zgartirish (Edit messages)</b> ruxsati yoqilgan bo'lishi shart!\n\n"
            "Shundan so'ng bot kanalga chiqqan har bir postga 6 ta reaksiyani avtomatik bosadi."
        )
        await call.message.answer(info_text, parse_mode="HTML")
        await call.answer()

@dp.callback_query(F.data == "stats")
async def show_stats_inline(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        count = get_users_count()
        await call.message.answer(f"📊 <b>Bot statistikasi:</b>\n\nFoydalanuvchilar: {count} ta", parse_mode="HTML")
        await call.answer()

@dp.callback_query(F.data == "broadcast")
async def ask_broadcast_text(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:
        await call.message.answer("Xabarni quyidagi formatda yozing:\n<code>/send Sizning xabaringiz</code>", parse_mode="HTML")
        await call.answer()

@dp.message(F.text.startswith("/send"))
async def broadcast_message(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send", "", 1).strip()
        if not text:
            await message.answer("Matn kiriting! Masalan: <code>/send Salom</code>", parse_mode="HTML")
            return
        
        users = get_all_users()
        count = 0
        for uid in users:
            try:
                await bot.send_message(chat_id=uid, text=text)
                count += 1
            except Exception:
                pass
        
        await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

# --- KANALGA POST CHIQGANDA 6 TA REAKSIYA BOSISH ---
@dp.channel_post()
async def auto_reaction_on_channel_post(message: types.Message):
    settings = get_settings()
    if settings["auto_react"]:
        try:
            emojis_list = settings["emojis"].split(",")
            reaction_list = [types.ReactionTypeEmoji(emoji=e.strip()) for e in emojis_list]
            
            await bot.set_message_reaction(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reaction=reaction_list
            )
        except Exception as e:
            print(f"Reaksiya bosishda xatolik: {e}")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi va 6 talik reaksiya rejimiga sozlandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
