from apscheduler.schedulers.background import BackgroundScheduler
from db import (
    get_least_active_user,
    add_point,
    reset_daily_messages,
    get_week_stats,
    get_top_popush,
    reset_likes,
)
import logging

def start_scheduler(app):
    scheduler = BackgroundScheduler()

    def daily_summary():

        user = get_least_active_user()
        if user:
            user_id, username = user[0], user[1]
            add_point(user_id, username)
            try:
                app.bot.send_message(
                    chat_id='-1002446794353',
                    text=f"😴 @{username} сегодня был самым неактивным. Очко попущенности."
                )
            except Exception as e:
                logging.error(f"Ошибка отправки ежедневного отчёта: {e}")
        else:
            logging.info("Нет данных о самом неактивном пользователе за день.")

        reset_daily_messages()
        print("✔ Ежедневные сообщения сброшены.")
        reset_likes()



    def weekly_summary():
        stats = get_week_stats()
        if not stats:
            logging.info("Пока нет очков попущенности за неделю.")
            return

        msg = "📊 Итоги недели:\n"
        for user, points in stats:
            msg += f"@{user} — {points} очк.\n"

        top = get_top_popush()
        if top:
            msg += f"\n🤡 Попуск недели: @{top}"

        try:
            app.bot.send_message(chat_id='-1002446794353', text=msg)
        except Exception as e:
            logging.error(f"Ошибка отправки еженедельного отчёта: {e}")

    # Запуск ежедневного отчёта в 23:59 каждый день
    scheduler.add_job(daily_summary, 'cron', hour=23, minute=59)

    # Запуск еженедельного отчёта в 23:59 в воскресенье
    scheduler.add_job(weekly_summary, 'cron', day_of_week='sun', hour=23, minute=59)

    scheduler.start()
    logging.info("Планировщик запущен.")
