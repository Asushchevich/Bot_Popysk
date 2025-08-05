from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from db import (
    add_message,
    like_message,
    count_likes,
    get_week_stats,
    add_user_if_not_exists, get_least_active_user, reset_database, get_messages_count, get_all_messages,
)

from db import get_all_users_with_messages, delete_user_by_username
from telegram.ext import ContextTypes
from scheduler import start_scheduler
import re
from db import add_point, remove_point, get_user_id_by_username
from db import get_top_popush

TOKEN = "8264220267:AAGNQ6MQ6HVOSetwjwWAarDviIhOjC_9J0Q"
ADMIN_ID = 772078520

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав для этой команды.")
            return
        return await func(update, context)
    return wrapper

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    add_message(user.id, user.username or "anon")

    text = update.message.text.lower()

    if "итоги" in text:
        await show_weekly_stats(update)
        return

    # Проверяем формат: "очко попущенности + @username"
    match = re.search(r'очко попущенности\s*\+?\s*@?(\w+)', text)
    if not match:
        return

    mentioned_username = match.group(1)

    # Ищем user_id в базе по username
    target_id = get_user_id_by_username(mentioned_username)
    if not target_id:
        await update.message.reply_text(f"Пользователь @{mentioned_username} не найден в базе.")
        return

    # Проверяем, ставил ли лайк текущий пользователь на это сообщение
    message_id = update.message.message_id
    liker_id = user.id

    if like_message(message_id, target_id, liker_id):
        like_count = count_likes(message_id)
        if like_count >= 2:
            add_point(target_id, mentioned_username)
            await update.message.reply_text(f"@{mentioned_username} получает очко попущенности!")
        else:
            await update.message.reply_text(f"Лайк засчитан! Сейчас у сообщения {like_count} лайков.")
    else:
        await update.message.reply_text("Ты уже лайкал это сообщение.")

async def show_weekly_stats(update: Update):
    stats = get_week_stats()
    if not stats:
        await update.message.reply_text("На этой неделе пока нет очков попущенности.")
        return

    msg = "🏆 Очки попущенности за неделю:\n"
    for user, points in stats:
        msg += f"@{user} — {points} очк.\n"
    top = get_top_popush()
    if top:
        msg += f"\n🤡 Попуск недели: @{top}"
    await update.message.reply_text(msg)

async def command_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users_with_messages()
    if not users:
        await update.message.reply_text("Пользователей ещё нет.")
        return

    msg = "📋 Очки попущенности и активность участников:\n"
    for username, points, messages in users:
        msg += f"@{username or 'Без_имени'} — {points} очк.\n"
    await update.message.reply_text(msg)

async def command_add_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    username = user.username or f"{user.first_name}_{user_id}"

    if add_user_if_not_exists(user_id, username):
        await update.message.reply_text("✅ Вы успешно добавлены в базу данных.")
    else:
        await update.message.reply_text("ℹ️ Вы уже есть в базе данных.")

async def top_popysk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_user = get_top_popush()
    if top_user:
        await update.message.reply_text(f"🤡 Попуск недели: @{top_user}")
    else:
        await update.message.reply_text("Пока нет очков попущенности.")

async def all_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = get_all_messages()
    if not users:
        await update.message.reply_text("📭 Пока что нет пользователей.")
        return

    message = "📨 *Все сообщения пользователей (всего):*\n\n"
    for i, (username, count) in enumerate(users, start=1):
        message += f"{i}. @{username} — {count} сообщений\n"

    await update.message.reply_text(message, parse_mode='Markdown')

@admin_only
async def command_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, есть ли аргумент (username)
    if not context.args:
        await update.message.reply_text("❗️ Пожалуйста, укажи имя пользователя: /deleteuser username")
        return

    username = context.args[0].lstrip('@')  # Убираем @, если есть

    delete_user_by_username(username)
    await update.message.reply_text(f"Пользователь @{username} удалён из базы данных (если он там был).")

@admin_only
async def add_point_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи username. Пример: /AddPointPoPysk @username")
        return

    username = context.args[0].lstrip('@')
    user_id = get_user_id_by_username(username)
    if not user_id:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return

    add_point(user_id, username)
    await update.message.reply_text(f"Очко попущенности добавлено @{username}.")

@admin_only
async def remove_point_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажи username. Пример: /RemovePointPoPysk @username")
        return

    username = context.args[0].lstrip('@')
    user_id = get_user_id_by_username(username)
    if not user_id:
        await update.message.reply_text(f"Пользователь @{username} не найден в базе.")
        return

    remove_point(user_id)
    await update.message.reply_text(f"Очко попущенности убрано у @{username}.")

async def not_active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_least_active_user()  # Эта функция из твоего db.py, возвращает (user_id, username)
    if user:
        user_id, username = user
        await update.message.reply_text(f"😴 Самый неактивный пользователь: @{username}\nКоличество сообщений: {get_messages_count(user_id)}")
    else:
        await update.message.reply_text("Пока нет данных по активности пользователей.")



async def reset_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # (по желанию) Ограничь доступ, например, только админу
    if user.id != ADMIN_ID:  # ← сюда вставь свой user_id
        await update.message.reply_text("❌ У тебя нет прав на выполнение этой команды.")
        return

    reset_database()
    await update.message.reply_text("✅ База данных успешно сброшена!")


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 *Список доступных команд:*\n\n"

        "🧾 `/stats` — показать очки попущенности.\n"
        "📨 `/AllMessages` — показать количество сообщений всех пользователей.\n\n"

        "➕ `/AddNewUserSVO` — добавить себя в базу данных бота.\n"
        "❌ `/deleteuser` — удалить себя из базы данных.\n\n"

        "🏅 `/AddPointPoPysk @username` — добавить очко попущенности выбранному пользователю.\n"
        "↩️ `/RemovePointPoPysk @username` — убрать очко попущенности у выбранного пользователя.\n\n"

        "👑 `/TopPoPysk` — показать пользователя с наибольшим числом очков попущенности.\n"
        "😴 `/NotActive` — показать самого неактивного пользователя по количеству сообщений.\n\n"

        "🔁 `/ResetDB` — *сбросить базу данных* (очки, сообщения, лайки). Только для Санечки.\n\n"

        "ℹ️ Для команд с упоминанием пользователя используйте формат:\n"
        "`/AddPointPoPysk @username`\n"
        "`/RemovePointPoPysk @username`"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')



def run():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(CommandHandler("stats", command_stats))
    app.add_handler(CommandHandler("AddNewUserSVO", command_add_new_user))
    app.add_handler(CommandHandler("deleteuser", command_delete_user))
    app.add_handler(CommandHandler("AddPointPoPysk", add_point_command))
    app.add_handler(CommandHandler("RemovePointPoPysk", remove_point_command))
    app.add_handler(CommandHandler("TopPoPysk", top_popysk_command))
    app.add_handler(CommandHandler("NotActive", not_active_command))
    app.add_handler(CommandHandler("ResetDB", reset_db_command))
    app.add_handler(CommandHandler("AllMessages", all_messages_command))
    app.add_handler(CommandHandler("help", command_help))

    start_scheduler(app)

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    run()
