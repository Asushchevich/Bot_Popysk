import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('popush.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицы при первом запуске
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS likes (
    message_id INTEGER,
    liked_user_id INTEGER,
    liker_user_id INTEGER,
    PRIMARY KEY(message_id, liker_user_id)
)
''')

conn.commit()

def add_message(user_id, username):
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, username, messages) VALUES (?, ?, 1)', (user_id, username))
    else:
        cursor.execute('UPDATE users SET messages = messages + 1 WHERE user_id = ?', (user_id,))
    conn.commit()

def like_message(message_id, liked_user_id, liker_user_id):
    cursor.execute('SELECT 1 FROM likes WHERE message_id = ? AND liker_user_id = ?', (message_id, liker_user_id))
    if cursor.fetchone():
        return False  # Уже лайкал
    cursor.execute('INSERT INTO likes (message_id, liked_user_id, liker_user_id) VALUES (?, ?, ?)', (message_id, liked_user_id, liker_user_id))
    conn.commit()
    return True

def count_likes(message_id):
    cursor.execute('SELECT COUNT(*) FROM likes WHERE message_id = ?', (message_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def add_point(user_id, username):
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, username, points) VALUES (?, ?, 1)', (user_id, username))
    else:
        cursor.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (user_id,))
    conn.commit()

def get_user_id_by_username(username):
    cursor.execute('SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)', (username,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_week_stats():
    cursor.execute('SELECT username, points FROM users ORDER BY points DESC, username ASC')
    return cursor.fetchall()


def get_top_popush():
    cursor.execute('SELECT username FROM users ORDER BY points DESC LIMIT 1')
    row = cursor.fetchone()
    return row[0] if row else None

def get_all_users():
    cursor.execute('SELECT username, points FROM users ORDER BY points DESC, username ASC')
    return cursor.fetchall()

def add_user_if_not_exists(user_id, username):
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO users (user_id, username, points, messages) VALUES (?, ?, 0, 0)', (user_id, username))
        conn.commit()
        return True
    return False

def remove_point(user_id):
    cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if not row:
        return False
    points = row[0]
    if points > 0:
        cursor.execute('UPDATE users SET points = points - 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        return True
    return False

def get_messages_count(user_id):
    cursor.execute('SELECT messages FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

def reset_database():
    cursor.execute('UPDATE users SET points = 0, messages = 0')
    cursor.execute('DELETE FROM likes')
    conn.commit()

def reset_daily_messages():
    cursor.execute('UPDATE users SET messages = 0')
    conn.commit()


# Или по user_id
def delete_user_by_username(username):
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()

def get_all_users_with_messages():
    cursor.execute('SELECT username, points, messages FROM users ORDER BY points DESC, username ASC')
    return cursor.fetchall()

def get_all_messages():
    cursor.execute('SELECT username, messages FROM users ORDER BY messages DESC, username ASC')
    return cursor.fetchall()

# Вот добавленные функции:

def reset_likes():
    cursor.execute('DELETE FROM likes')
    conn.commit()

def reset_daily_messages():
    cursor.execute('UPDATE users SET messages = 0')
    conn.commit()

def get_least_active_user():
    cursor.execute('SELECT user_id, username FROM users ORDER BY messages ASC LIMIT 1')
    return cursor.fetchone()

