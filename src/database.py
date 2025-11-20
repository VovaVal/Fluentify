import sqlite3
from pathlib import Path
from datetime import date, datetime
import hashlib


class VocabularyDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "vocabulary.db"
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Создаёт базу и все таблицы, если их нет"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Включаем поддержку внешних ключей
            conn.execute("PRAGMA foreign_keys = ON;")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    folder_id INTEGER,
                    description TEXT,
                    topic TEXT DEFAULT '',
                    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    native_word TEXT NOT NULL,
                    translated_word TEXT NOT NULL,
                    module_id INTEGER NOT NULL,
                    example_sentence TEXT,
                    learned TEXT CHECK(learned IN ('yes', 'no')) DEFAULT 'no',
                    add_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    learned_date TIMESTAMP,
                    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
                )
            """)

            conn.execute('''
                CREATE TABLE IF NOT EXISTS radio(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                image_path TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS essay(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP,
                score INTEGER
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_info(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                register_day TIMESTAMP NOT NULL,
                user_password TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_entries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP NOT NULL
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS words_statistics(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TIMESTAMP NOT NULL,
                learned INTEGER,
                not_learned INTEGER
                )
            ''')

            conn.execute('''
                            CREATE TABLE IF NOT EXISTS ai_key(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            key TEXT NOT NULL
                            )
                        ''')

            # Индексы для ускорения поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_modules_folder ON modules(folder_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_words_module ON words(module_id);")
            self.add_key()

            conn.commit()

    def add_key(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            key = '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'
            cur.execute('''INSERT INTO ai_key(key) VALUES(?)''', (key,))

            conn.commit()

    def get_key(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT key FROM ai_key WHERE id = 1''')

            return cur.fetchone()[0]

    def set_key(self, key):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''UPDATE ai_key SET key = ? WHERE id = 1''',
                        (key,))

            conn.commit()

    def add_folder(self, name: str) -> int:
        """Добавляет папку, возвращает её id"""
        if name.strip() == '':
            raise ValueError('Вы ввели пустую строку.')

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM folders WHERE name = ?", (name,))
            if cur.fetchone():
                raise ValueError("Папка с таким названием уже существует")

            cur.execute("INSERT OR IGNORE INTO folders (name) VALUES (?)", (name,))
            conn.commit()
            cur.execute("SELECT id FROM folders WHERE name = ?", (name,))
            return cur.fetchone()[0]

    def get_all_folders(self):
        """Возвращает [(id, name), ...]"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM folders ORDER BY name")
            return cur.fetchall()

    def add_module(self, name: str, folder_id=None, description: str = "") -> int:
        name = name.strip()
        if name == '':
            raise ValueError("Имя модуля не может быть пустым")

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            if folder_id is not None:
                cur.execute("SELECT id FROM modules WHERE name = ? AND folder_id = ?", (name, folder_id))
                if cur.fetchone():
                    raise ValueError("Модуль с таким названием уже существует")

            cur.execute("""
                INSERT INTO modules (name, folder_id, description)
                VALUES (?, ?, ?)
            """, (name, folder_id, description))
            conn.commit()
            return cur.lastrowid

    def get_modules_in_folder(self, folder_id: int):
        """Возвращает [(id, name), ...]"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name FROM modules WHERE folder_id = ? ORDER BY name",
                (folder_id,)
            )
            return cur.fetchall()

    def add_word(self, native: str, translated: str, module_id: int,
                 example: str = "") -> int:
        """Добавляет слово, возвращает его id"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO words (native_word, translated_word, module_id, example_sentence)
                VALUES (?, ?, ?, ?)
            """, (translated, native, module_id, example))
            conn.commit()
            return cur.lastrowid

    def get_words_in_module(self, module_id: int):
        """Возвращает список слов в модуле"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT native_word, translated_word
                FROM words
                WHERE module_id = ?
            """, (module_id,))
            return cur.fetchall()

    def get_learned_words_in_module(self, module_id: int):
        """Возвращает список слов в модуле"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT native_word, translated_word
                FROM words
                WHERE module_id = ? AND learned = 'yes'
            """, (module_id,))
            return cur.fetchall()

    def get_not_learned_words_in_module(self, module_id: int):
        """Возвращает список слов в модуле"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT native_word, translated_word
                FROM words
                WHERE module_id = ? AND learned = 'no'
            """, (module_id,))
            return cur.fetchall()

    def get_words_for_module(self, module_id):
        '''возвращает с индексом'''
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, native_word, translated_word FROM words WHERE module_id = ?",
                        (module_id,))
            return cur.fetchall()

    def mark_word_known(self, word_id: int, known: bool):
        '''Помечает слова как изученные или нет'''
        known = 'yes' if known else 'no'

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE words
                SET learned = ?, learned_date = ?
                WHERE id = ?
            """, (known, date.today().isoformat(), word_id))
            conn.commit()

    def get_statistics_words_learned(self, module_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT learned FROM words WHERE module_id = ?''', (module_id,))

            learned = 0
            not_learned = 0
            for i in cur.fetchall():
                if i[0] == 'yes':
                    learned += 1
                else:
                    not_learned += 1
            return learned, not_learned

    def delete_word(self, word_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
            conn.commit()

    def delete_module(self, module_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM modules WHERE id = ?", (module_id,))
            conn.commit()

    def delete_folder(self, folder_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            conn.commit()

    def get_all_modules(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM modules ORDER BY name")
            return cur.fetchall()

    def get_all_searched_modules(self, text, folder_id=None):
        query = text.strip().lower()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if folder_id is None:
                cur.execute("SELECT id, name FROM modules")
            else:
                cur.execute("SELECT id, name FROM modules WHERE folder_id = ?", (folder_id,))
            all_modules = cur.fetchall()

        return [(mid, name) for mid, name in all_modules if query in name.lower()]

    def get_all_searched_folders(self, text):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM folders")
            all_folders = cur.fetchall()

        query = text.strip().lower()
        return [(fid, name) for fid, name in all_folders if query in name.lower()]

    def rename_module(self, text: str, id_module: int):
        text = text.strip()

        if not text:
            return False

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''
                        SELECT id, folder_id FROM modules
                        WHERE id = ?''', (id_module, ))

            folder_id = cur.fetchall()[0][1]

            if folder_id is None:
                cur.execute("""
                    SELECT id, folder_id FROM modules
                    WHERE name = ? AND folder_id IS NULL AND id != ?
                """, (text, id_module))
            else:
                cur.execute("""
                    SELECT id, folder_id FROM modules
                    WHERE name = ? AND folder_id = ?
                """, (text, folder_id))

            if cur.fetchone():
                return False

            cur.execute("UPDATE modules SET name = ? WHERE id = ?", (text, id_module))
            conn.commit()
            return True

    def rename_folder(self, text: str, id_module: int):
        m = [i[1] for i in self.get_all_folders()]
        if text.strip() == '' or text in m:
            return False

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''UPDATE folders
                            SET name = ?
                            WHERE id = ?''', (text, id_module))
            conn.commit()
            return True

    def get_unassigned_modules(self):
        """Возвращает модули, не привязанные ни к одной папке: [(id, name), ...]"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM modules WHERE folder_id IS NULL ORDER BY name")
            return cur.fetchall()

    def assign_module_to_folder(self, module_id: int, folder_id: int):
        """Привязывает модуль к папке"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''
                        SELECT name FROM modules
                        WHERE id = ?''', (module_id, ))
            module_name = cur.fetchall()[0][0]

            cur.execute("""
                            SELECT id FROM modules
                            WHERE name = ? AND folder_id = ?""",
                        (module_name, folder_id))

            if cur.fetchone():
                return False

            cur.execute("UPDATE modules SET folder_id = ? WHERE id = ?", (folder_id, module_id))
            conn.commit()
            return True

    def set_description(self, module_id: int, description: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''
                        UPDATE modules
                        SET description = ?
                        WHERE id = ?''', (description, module_id))

            conn.commit()

    def set_topic(self, module_id: int, topic: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''
                        UPDATE modules
                        SET topic = ?
                        WHERE id = ?''', (topic, module_id))

            conn.commit()

    def get_topic(self, module_id: int):
        '''возвращает тематику модуля по его id'''
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''SELECT topic FROM modules WHERE id = ?''', (module_id,))
            topic = cur.fetchall()[0][0]
            return topic

    def get_description(self, module_id: int):
        '''возвращает описание модуля по его id'''
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''SELECT description FROM modules WHERE id = ?''', (module_id,))
            description = cur.fetchall()[0][0]
            return description

    def has_words(self, module_id):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            cur.execute('''SELECT id from words
                            WHERE module_id = ?''', (module_id, ))
            if cur.fetchone():
                return False
            return True

    def delete_words_from_module(self, module_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''DELETE FROM words WHERE module_id = ?''', (module_id,))

            conn.commit()

    def add_radio_station(self, name: str, url: str):
        '''Добавляет радиостанцию'''
        if not name or not url:
            raise ValueError("Название и ссылка не могут быть пустыми")

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id FROM radio WHERE name = ? OR url = ?''', (name, url))
            if cur.fetchone():
                raise ValueError("Радиостанция с таким названием или ссылкой уже существует")

            cur.execute('''INSERT INTO radio (name, url) VALUES (?, ?)''', (name.strip(), url.strip()))

            conn.commit()
            return cur.lastrowid

    def add_image_radio(self, radio_id: int, image_path: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''UPDATE radio SET image_path = ? WHERE id = ?''', (image_path, radio_id))

            conn.commit()

    def get_all_radio_stations(self):
        """Возвращает [(id, name, url), ...]"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, url FROM radio ORDER BY name")
            return cur.fetchall()

    def get_all_radio_names(self):
        """Возвращает [(id, name), ...]"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM radio ORDER BY name")
            return cur.fetchall()

    def delete_radio_station(self, station_id: int):
        '''Удалить радиостанцию'''
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM radio WHERE id = ?", (station_id,))
            conn.commit()

    def update_radio_station(self, station_id: int, name: str, url: str):
        '''Обновить данные о радиостанции'''
        name = name.strip()
        url = url.strip()
        if not name or not url:
            raise ValueError("Название и ссылка не могут быть пустыми")

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Проверяем, не конфликтует ли новое имя/ссылка с другими
            cur.execute("""SELECT id FROM radio WHERE (name = ? OR url = ?) AND id != ?
            """, (name, url, station_id))
            if cur.fetchone():
                raise ValueError("Радиостанция с таким названием или ссылкой уже существует")

            cur.execute("""
                UPDATE radio 
                SET name = ?, url = ? 
                WHERE id = ?
            """, (name, url, station_id))
            conn.commit()

    def get_all_searched_radios(self, query):
        query = query.strip().lower()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id, name FROM radio''')

            all_radios = cur.fetchall()

        return [(rid, name) for rid, name in all_radios if query in name.lower()]

    def get_radio_url(self, radio_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT url FROM radio WHERE id = ?''', (radio_id,))

            return cur.fetchone()

    def get_image_path(self, radio_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT image_path FROM radio WHERE id = ?''', (radio_id,))

            return cur.fetchone()

    def add_data_essay(self, score: int):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''INSERT INTO essay(date, score) VALUES (?, ?)''', (date.today().isoformat(),
                                                                             score))

            conn.commit()

    def take_all_data_from_essay(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT date, score FROM essay''')

            return cur.fetchall()

    def get_user_info(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT * FROM user_info''')

            return cur.fetchone()

    def set_user_info(self, user_name, password=None):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if password is not None:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cur.execute('''INSERT INTO user_info (user_name, register_day, user_password) VALUES (?, ?, ?)''',
                            (user_name, date.today().isoformat(), password_hash))
            else:
                cur.execute('''INSERT INTO user_info (user_name, register_day) VALUES (?, ?)''',
                            (user_name, date.today().isoformat()))

            conn.commit()

    def get_password_hash(self) -> str | None:
        """Возвращает хеш пароля или None, если пароль не установлен"""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_password FROM user_info")
            row = cur.fetchone()

            return row[0] if row else None

    def verify_password(self, password: str) -> bool:
        """Проверяет пароль"""
        stored_hash = self.get_password_hash()

        if stored_hash is None:
            return True
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash

    def update_user_info(self, user_name, password=None):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if password is not None:
                password = hashlib.sha256(password.encode()).hexdigest()
            cur.execute('''UPDATE user_info SET user_name = ?, user_password = ?''',
                        (user_name, password))

    def get_all_not_learned_words(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id, native_word, translated_word FROM words WHERE learned = 'no' ''')

            return cur.fetchall()

    def get_word_id(self, meaning: str, translate: str):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id FROM words WHERE native_word = ? AND translated_word = ?''',
                        (translate, meaning))

            return cur.fetchone()[0]

    def add_date_entry(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT id FROM user_entries WHERE date = ?''', (date.today().isoformat(),))

            if cur.fetchone():
                return

            cur.execute('''INSERT INTO user_entries(date) VALUES(?)''', (date.today().isoformat(),))

            conn.commit()

    def get_all_entry_dates(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT date FROM user_entries''')

            return cur.fetchall()

    def get_learned_not_learned_by_date(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT learned, learned_date FROM words''')

            data = cur.fetchall()
            main_d = {}
            for i in data:
                if i[1] not in main_d:
                    main_d[i[1]] = []
                main_d[i[1]].append(i[0])

            for i in main_d:
                data_row = main_d[i]
                know, not_know = 0, 0
                for j in data_row:
                    if j == 'no':
                        not_know += 1
                    else:
                        know += 1

                main_d[i] = (know, not_know)
            return main_d

    def add_data_to_words_statistics(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            data = self.get_learned_not_learned_by_date()

            for i in data:
                cur.execute('''SELECT * FROM words_statistics WHERE date = ?''', (i,))
                if cur.fetchone():
                    cur.execute('''UPDATE words_statistics SET learned = ?, not_learned = ? WHERE date = ?''',
                                (data[i][0], data[i][1], i))

                else:
                    cur.execute('''INSERT INTO words_statistics(date, learned, not_learned) VALUES (?, ?, ?)''',
                                (i, data[i][0], data[i][1]))

            conn.commit()

    def get_by_date_learned(self, date):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT learned, not_learned FROM words_statistics WHERE date = ?''', (date,))

            return cur.fetchone()