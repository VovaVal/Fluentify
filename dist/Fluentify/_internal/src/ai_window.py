import random

import requests
import markdown
import re
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import socket

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QStackedWidget, QWidget, QPushButton, QComboBox, QTextBrowser, QTextEdit, QMessageBox, \
    QLabel, QDialog, QVBoxLayout, QListWidgetItem, QListWidget, QLineEdit, QSpinBox
from PyQt6.QtGui import QMovie, QColor


class AI:
    def __init__(self, parent_window, db):
        self.window = parent_window
        self.db = db
        self.setup_ai_tab()

    def setup_ai_tab(self):
        ai_tab = self.window.ai_tab

        self.ai_stacked = ai_tab.findChild(QStackedWidget, 'stackedWidget_ai')
        self.page_start = self.ai_stacked.findChild(QWidget, 'page_start')
        self.page_essay = self.ai_stacked.findChild(QWidget, 'page_essay')

        self.essay_btn = ai_tab.findChild(QPushButton, 'essay_btn')
        self.essay_btn.clicked.connect(self.essay_btn_clicked)

        self.statistic_essay_btn = ai_tab.findChild(QPushButton, 'statistic_essay_btn')
        self.statistic_essay_btn.clicked.connect(self.statistic_essay_btn_clicked)

        self.label_gif = ai_tab.findChild(QLabel, 'label_gif')
        self.label_gif.hide()
        self.label_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.back_essay_btn = ai_tab.findChild(QPushButton, 'back_essay_btn')
        self.back_essay_btn.clicked.connect(self.back_essay_btn_clicked)

        self.comboBox_lang = ai_tab.findChild(QComboBox, 'comboBox_lang')

        self.comboBox_topic = ai_tab.findChild(QComboBox, 'comboBox_topic')

        self.comboBox_ai_model = ai_tab.findChild(QComboBox, 'comboBox_ai_model')
        self.comboBox_ai_model.setCurrentText('Средняя')

        self.comboBox_level = ai_tab.findChild(QComboBox, 'comboBox_level')

        self.comboBox_criteria = ai_tab.findChild(QComboBox, 'comboBox_criteria')

        self.generate_topic_btn = ai_tab.findChild(QPushButton, 'generate_topic_btn')
        self.generate_topic_btn.setEnabled(True)
        self.generate_topic_btn.clicked.connect(self.make_prompt_to_get_essay_topic)

        self.textBrowser_essay_topic = ai_tab.findChild(QTextBrowser, 'textBrowser_essay_topic')

        self.textEdit_essay = ai_tab.findChild(QTextEdit, 'textEdit_essay')

        self.send_essay_btn = ai_tab.findChild(QPushButton, 'send_essay_btn')
        self.send_essay_btn.clicked.connect(self.send_essay)
        self.send_essay_btn.show()

        self.new_essay_btn = ai_tab.findChild(QPushButton, 'new_essay_btn')
        self.new_essay_btn.hide()
        self.new_essay_btn.clicked.connect(self.new_essay_clicked)

        self.ai_ans_btn = ai_tab.findChild(QPushButton, 'ai_ans_btn')
        self.ai_ans_btn.hide()
        self.ai_ans_btn.clicked.connect(self.ai_ans_btn_clicked)

        self.movie = QMovie(resource_path('image/load.gif'))

        self.words_btn = ai_tab.findChild(QPushButton, 'words_btn')
        self.words_btn.clicked.connect(self.words_btn_clicked_look)

        self.label_guess_word = ai_tab.findChild(QLabel, 'label_guess_word')
        self.label_explanation_look_word = ai_tab.findChild(QLabel, 'label_explanation_look_word')
        self.listWidget_words_look = ai_tab.findChild(QListWidget, 'listWidget_words_look')
        self.lineEdit_words_look = ai_tab.findChild(QLineEdit, 'lineEdit_words_look')
        self.ok_btn_words_look = ai_tab.findChild(QPushButton, 'ok_btn_words_look')
        self.stacked = ai_tab.findChild(QStackedWidget, 'stackedWidget_8')
        self.main_stacked = ai_tab.findChild(QStackedWidget, 'stackedWidget_ai')
        self.comboBox_lang_words_ai = ai_tab.findChild(QComboBox, 'comboBox_lang_words_ai')
        self.comboBox_lang_look_2 = ai_tab.findChild(QComboBox, 'comboBox_lang_look_2')
        self.comboBox_topic_words = ai_tab.findChild(QComboBox, 'comboBox_topic_words')
        self.comboBox_level_words = ai_tab.findChild(QComboBox, 'comboBox_level_words')
        self.generate_words_btn = ai_tab.findChild(QPushButton, 'generate_words_btn')
        self.generate_words_btn.clicked.connect(self.make_prompt_words_ai_to_get_words)
        self.spinBox_words_num = ai_tab.findChild(QSpinBox, 'spinBox_words_num')

        self.label_img_look = ai_tab.findChild(QLabel, 'label_img_look')
        self.label_img_look.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_img_look.hide()

        self.back_ai_words_btn = ai_tab.findChild(QPushButton, 'back_ai_words_btn')
        self.back_ai_words_btn.clicked.connect(self.back_ai_words_btn_clicked)

        self.back_words_look_btn = ai_tab.findChild(QPushButton, 'back_words_look_btn')
        self.back_words_look_btn.clicked.connect(self.back_words)

        self.back_words_look_btn_1 = ai_tab.findChild(QPushButton, 'back_words_look_btn_1')
        self.back_words_look_btn_1.clicked.connect(self.back_words)

    def back_ai_words_btn_clicked(self):
        self.ai_stacked.setCurrentIndex(0)

    def back_words(self):
        self.ai_stacked.setCurrentIndex(2)
        self.generate_words_btn.setEnabled(True)

    def words_btn_clicked_look(self):
        if check_wifi():
            self.ai_stacked.setCurrentIndex(2)
        else:
            QMessageBox.warning(self.window, 'Ошибка', 'Нет доступа к интернету.')

    def essay_btn_clicked(self):
        if check_wifi():
            self.ai_stacked.setCurrentIndex(1)
            self.new_essay_clicked()
        else:
            QMessageBox.warning(self.window, 'Ошибка', 'Нет доступа к интернету.')

    def statistic_essay_btn_clicked(self):
        date_score_dict = {}

        for i in self.db.take_all_data_from_essay():
            if i[0] not in date_score_dict:
                date_score_dict[i[0]] = []
            date_score_dict[i[0]].append(i[1])

        for i in date_score_dict:
            date_score_dict[i] = sum(date_score_dict[i]) / len(date_score_dict[i])

        date_score_dict_1 = sorted(date_score_dict)

        x = [i for i in date_score_dict_1]
        y = [date_score_dict[i] for i in date_score_dict_1]

        plt.figure(figsize=(6, 4))
        plt.ylim(0, 100)
        plt.plot(x, y, marker='o')
        plt.title("График оценки сочинений")
        plt.xlabel("Дата")
        plt.ylabel("Баллы")
        plt.grid(True)

        plt.show(block=False)

    def back_essay_btn_clicked(self):
        self.ai_stacked.setCurrentIndex(0)

    def words_test(self, translated, meaning):
        self.words_ai = StudyAIWords(
            label_guess=self.label_guess_word,
            label_explanation=self.label_explanation_look_word,
            list_widget=self.listWidget_words_look,
            line_edit_word=self.lineEdit_words_look,
            ok_btn=self.ok_btn_words_look,
            stacked=self.stacked,
            stacked_main=self.main_stacked,
            theme=self.window.get_theme
        )

        words = [(i, meaning[i], translated[i]) for i in range(len(translated))]

        self.words_ai.load_words(words)
        self.ai_stacked.setCurrentIndex(3)

    def make_prompt_words_ai_to_get_words(self):
        self.label_img_look.setMovie(self.movie)
        self.movie.start()
        self.label_img_look.show()
        self.generate_words_btn.hide()
        mother_tong = self.comboBox_lang_words_ai.currentText()
        not_mother_tong = self.comboBox_lang_look_2.currentText()
        topic = self.comboBox_topic_words.currentText()
        level = self.comboBox_level_words.currentText()
        num_of_words = self.spinBox_words_num.text()

        self.generate_words_btn.setEnabled(False)

        model = 1
        prompt = f'''Привет. Сгенерируй слова на тему: {topic}; с уровнем знаний: {level}; на первой строке
{num_of_words} слов через запятую на {not_mother_tong}, а на второй строке {num_of_words} слов через запятую на
{mother_tong} со значением каждого слова. Строго соблюдай заданное количество слов.
То есть условно первая строка должна выглядеть примерно так
 "Hello, Bye, Good night", а вторая "Привет, Пока, Спокойной ночи", выведи только две строчки с сгенерированными слова, 
больше ничего не нужно.'''

        QTimer.singleShot(10, lambda: self.get_words_ai_response(model, prompt))

    def get_words_ai_response(self, model, prompt):
        res = self.ai_return_ans(model, prompt)
        self.label_img_look.hide()
        self.generate_words_btn.show()

        translated_words = []
        meaning_words = []

        if res:
            translated_words = [i.strip() for i in res.split('\n')[0].split(', ')]
            meaning_words = [i.strip() for i in res.split('\n')[1].split(', ')]
            self.words_test(translated_words, meaning_words)

        if res and translated_words and meaning_words and len(translated_words) == len(meaning_words):
            pass
        else:
            self.generate_words_btn.setEnabled(True)
            QMessageBox.information(self.window, 'Ошибка', 'К сожалению, мы не смогли сгенерировать вам слова. '
                                                           'Попробуйте позже ещё раз.')

    def new_essay_clicked(self):
        self.generate_topic_btn.setEnabled(True)
        self.send_essay_btn.show()
        self.new_essay_btn.hide()
        self.ai_ans_btn.hide()
        self.comboBox_lang.setCurrentText('Русский')
        self.comboBox_topic.setCurrentText('Любая')
        self.comboBox_ai_model.setCurrentText('Средняя')
        self.comboBox_level.setCurrentText('A1')
        self.comboBox_criteria.setCurrentText('Нет')
        self.label_gif.hide()
        self.textBrowser_essay_topic.setText('')
        self.textEdit_essay.setText('')

    def ai_ans_btn_clicked(self):
        class ShowAIAns(QDialog):
            def __init__(self, text, parent=None):
                super().__init__(parent)
                self.resize(600, 600)
                self.setWindowTitle('Ответ ИИ')
                vbox = QVBoxLayout()

                textBrowser = QTextBrowser()
                markdown_text = markdown.markdown(text)
                textBrowser.setHtml(markdown_text)
                vbox.addWidget(textBrowser)

                self.setLayout(vbox)


        s = ShowAIAns(self.ans, self.window)
        s.exec()

    def send_essay(self):
        essay_text = self.textEdit_essay.toPlainText()
        model = self.comboBox_ai_model.currentIndex()
        topic = self.textBrowser_essay_topic.toPlainText()
        criteria = self.comboBox_criteria.currentText()

        prompt = f'''Проанализируй сочинение, написанное мной. Подробно объясняй все грамматические, орфографические и
лексические ошибки. Можешь добавлять emoji. Сочинение оценивай по критерии: {criteria}(если их нет, то оценивай сам).
 В выводе напиши, почему ты оставил такую оценку, похвали пользователя, даже если он плохо написал сочинение. Весь ответ
 на русском. На последней строке оставь оценку от 0 до 100. На последней строке должна быть ТОЛЬКО одна оценка, цифрами,
  не словами, ничего писать словами не надо, АБСОЛЮТНО, ПРОСТО ОЦЕНКА, ЧИСЛОМ, НЕ ПИШИ СЛОВА "ОЦЕНКА",
   "ИТОГОВАЯ ОЦЕНКА", просто число. Тема сочинения: {topic}; Текст сочинения: {essay_text}.'''

        self.label_gif.setMovie(self.movie)
        self.movie.start()
        self.label_gif.show()

        self.generate_topic_btn.setEnabled(False)
        self.send_essay_btn.hide()
        self.new_essay_btn.show()
        self.ai_ans_btn.show()

        QTimer.singleShot(10, lambda: self._perform_ai_request(model, prompt, flag=True))


    def make_prompt_to_get_essay_topic(self):
        prompt = f'''Привет! Напиши тему для сочинения на тему: "{self.comboBox_topic.currentText()}"(если написано,
что-то типа "Любая", "Без разницы", то генерируй любую тему),
уровень языковых знаний: {self.comboBox_level.currentText()}, тема должна буть написана на
{self.comboBox_lang.currentText()} языке.
Напиши ТОЛЬКО ОДНО ПРЕДЛОЖЕНИЕ с темой. Больше ничего не надо. Старайся генерировать интересные темы, не повторяй старые
 темы!'''

        model = self.comboBox_ai_model.currentIndex()

        self.textBrowser_essay_topic.setText('')
        self.textBrowser_essay_topic.hide()

        self.label_gif.setMovie(self.movie)
        self.movie.start()
        self.label_gif.show()

        QTimer.singleShot(10, lambda: self._perform_ai_request(model, prompt))

    def _perform_ai_request(self, model, prompt, flag=False):
        ans = self.ai_return_ans(model, prompt)
        if not flag:
            if ans:
                self.textBrowser_essay_topic.setText(ans)
            else:
                QMessageBox.warning(self.window, "Ошибка", "К сожалению, не удалось сгенерировать тему.")

            self.movie.stop()
            self.label_gif.hide()
            self.textBrowser_essay_topic.show()

        else:
            if not ans:
                QMessageBox.warning(self.window, "Ошибка", "К сожалению, не удалось проверить сочинение.")

            else:
                self.label_gif.hide()
                self.ans = ans
                print(self.ans.split('\n'))
                last_row = self.ans.split('\n')[-1]
                print(last_row)
                num = self.extract_single_number(str(last_row))
                print(num)

                if isinstance(num, int):
                    self.db.add_data_essay(num)

    def extract_single_number(self, text: str) -> int | None:
        numbers = re.findall(r'\d+', text)
        if len(numbers) == 1:
            return int(numbers[0])

        return None

    def get_openrouter_key(self):
        return self.db.get_key()

    def ai_return_ans(self, model, message):
        # ваш OPENROUTER_API_KEY
        # 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
        # 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
        # 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
        # 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
        OPENROUTER_API_KEY = self.get_openrouter_key()
        models = ["tngtech/deepseek-r1t2-chimera:free", "x-ai/grok-4.1-fast:free",
                  "mistralai/mistral-small-3.1-24b-instruct:free"]

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost",
            },
            json={
                "model": models[model],
                "messages": [
                    {"role": "user",
                     "content": message},
                ],
                "temperature": 0.7,
            }
        )

        # Вывод ответа
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(response.status_code)
            return False


def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу"""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.parent
    return str(base_path / relative_path)


def check_wifi():
    '''Проверка на наличие wifi'''
    try:
        socket.gethostbyaddr('www.yandex.ru')
    except socket.gaierror:
        return False
    return True


class StudyAIWords:
    def __init__(self, label_guess, label_explanation, list_widget, line_edit_word,
                 ok_btn, stacked, stacked_main, theme):
        self.label_guess = label_guess
        self.label_guess.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_guess.setWordWrap(True)
        self.label_explanation = label_explanation
        self.list_widget = list_widget
        self.line_edit_word = line_edit_word
        self.ok_btn = ok_btn
        self.theme_func = theme
        self.stacked = stacked
        self.stacked_main = stacked_main
        self.in_process = False
        self.label_explanation.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_explanation.setWordWrap(True)
        self.label_explanation.setStyleSheet("""
            QLabel {
                background-color: #C3D0F7;
                color: #1b5e20;
                border: 2px solid #3253B8;
                border-radius: 16px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.label_guess.setStyleSheet("""
                    QLabel {
                        background-color: #C3D0F7;
                        color: #1b5e20;
                        border: 2px solid #3253B8;
                        border-radius: 16px;
                        padding: 10px;
                        font-size: 14px;
                    }
                """)
        self.ok_btn.clicked.connect(self.ok_btn_clicked)
        self.list_widget.itemClicked.connect(self.list_widget_clicked)


    def load_words(self, words):
        self.words = words
        random.shuffle(self.words)
        self.stacked.setCurrentIndex(0)
        self.in_process = False
        self.list_widget.setEnabled(True)

        self.all_words = [i[-1] for i in self.words.copy()]
        self.unique_all_words = list(set([i[-1] for i in self.words.copy()]))

        # слова, когда нужно выбрать слово, основываясь по термину
        self.words_with_choice = [i[1] for i in self.words.copy()]
        self.words_without_choice = [i[-1] for i in self.words.copy()]

        # словарь(термин слова: слово)
        self.word_meaning_dict = [(i[1], i[-1]) for i in self.words.copy()]
        random.shuffle(self.word_meaning_dict)

        self.choice = True
        self.steps = 0

        self.settings()

    def settings(self):
        self.words_choice = self.words_with_choice[:5]
        self.words_not_choice = self.words_without_choice[:5]

        del self.words_with_choice[:5]
        del self.words_without_choice[:5]

        self.words_dict = self.word_meaning_dict[:5]

        del self.word_meaning_dict[:5]

        self.load_words_choice()

    def load_words_choice(self):
        self.label_guess.setText(self.words_choice[0])

        right_ans = self.words_not_choice[0]
        rand_words = random.sample(self.unique_all_words, k=4 if len(self.unique_all_words) >= 5
        else len(self.unique_all_words) - 1)

        while right_ans in rand_words:
            rand_words = random.sample(self.unique_all_words, k=4 if len(self.unique_all_words) >= 5
            else len(self.unique_all_words) - 1)

        self.list_widget.clear()
        self.list_widget.setSpacing(2)
        self.list_widget.setWordWrap(True)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        rand_words += [right_ans]
        random.shuffle(rand_words)
        for i, val in enumerate(rand_words):
            item = QListWidgetItem(val)
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.list_widget.addItem(item)

    def list_widget_clicked(self, item):
        '''Метод нажатия на слово в QListWidget'''
        self.in_process = True
        self.list_widget.setEnabled(False)
        text = item.text()
        res = text == self.words_not_choice[0]
        self.steps += 1

        if not self.words_not_choice:  # защита от пустого списка
            return

        if res:
            # если ответ правильный
            item.setForeground(QColor("green"))
            item.setText('✅ ' + item.text())

            if self.words_not_choice:
                # удаляем слово и его значение
                del self.words_not_choice[0]
                del self.words_choice[0]

        else:
            # если ответ неправильный
            item.setForeground(QColor('red'))
            item.setText('❌ ' + item.text())
            self.highlight_correct_answer(self.words_not_choice[0])

            # добаляем для повторного повторения
            self.words_with_choice.append(self.words_choice[0])
            self.words_without_choice.append(self.words_not_choice[0])

            if self.words_not_choice:
                # удаляем слово и его значение
                del self.words_not_choice[0]
                del self.words_choice[0]

        if (not self.words_with_choice and not self.word_meaning_dict and not self.words_not_choice and
                not self.words_choice and not self.words_dict):
            QTimer.singleShot(1400, self.finish_study)

        else:
            if self.steps >= 5 or not self.words_not_choice:
                QTimer.singleShot(1400, self.different_style)
            else:
                # Переходим к следующему слову
                QTimer.singleShot(1400, self.next_word)

    def highlight_correct_answer(self, correct_text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            clean = item.text().replace("✅ ", "").replace("❌ ", "")
            if clean == correct_text:
                item.setForeground(QColor("green"))
                item.setText("✅ " + clean)
                break

    def next_word(self):
        """Показывает следующую карточку"""
        if self.words_not_choice:
            self.list_widget.setEnabled(True)
            self.in_process = False
            self.load_words_choice()  # только обновляем интерфейс, не перезапускаем сессию

    def finish_study(self):
        """Завершает обучение"""
        self.in_process = False
        self.stacked_main.setCurrentIndex(self.stacked_main.currentIndex() - 3)

    def different_style(self, flag=True):
        if self.stacked.currentIndex() == 0:
            self.stacked.setCurrentIndex(1)
            if not self.words_dict and not self.word_meaning_dict:
                self.words_choice = self.words_with_choice[:5]
                self.words_not_choice = self.words_without_choice[:5]

                del self.words_with_choice[:5]
                del self.words_without_choice[:5]

                self.different_style(flag=False)
                return

            self.steps = 0
            self.load_words_write()

        else:
            self.in_process = False
            self.list_widget.setEnabled(True)
            self.stacked.setCurrentIndex(0)
            if not self.words_with_choice and not self.words_not_choice:  # если нету слов при изучении выбором слов
                self.words_dict = self.word_meaning_dict[:5]
                del self.word_meaning_dict[:5]

                self.different_style()
                return

            if flag:
                self.settings()
            self.steps = 0
            self.load_words_choice()

    def load_words_write(self):
        self.line_edit_word.setEnabled(True)
        self.ok_btn.setEnabled(True)

        if self.theme_func() == 'light':
            self.line_edit_word.setStyleSheet('color: black')
        else:
            self.line_edit_word.setStyleSheet('color: white')
        self.line_edit_word.setText('')
        self.label_explanation.setText(self.words_dict[0][0])

    def ok_btn_clicked(self):
        self.steps += 1
        self.line_edit_word.setEnabled(False)
        self.ok_btn.setEnabled(False)

        if ('_'.join([i.strip().strip(',.!?-=+/*') for i in self.line_edit_word.text().lower().strip().split()])
                == self.words_dict[0][1].lower().strip()):
            self.line_edit_word.setStyleSheet('color: green')
            self.line_edit_word.setText(self.line_edit_word.text().strip() + " ✅")

            del self.words_dict[0]

        else:
            self.line_edit_word.setStyleSheet('color: red')
            self.line_edit_word.setText(self.line_edit_word.text().strip() + " ❌")

            QMessageBox.information(
                self.label_explanation.window(),
                "Неправильный ответ",
                f"Правильный ответ: <b><span style='color: green;'>{self.words_dict[0][1]}</span></b>"
            )

            self.word_meaning_dict.append(self.words_dict[0])  # добавляем невыученное слово с его значением
            del self.words_dict[0]

        if (not self.words_with_choice and not self.word_meaning_dict and not self.words_not_choice and
                not self.words_choice and not self.words_dict):
            QTimer.singleShot(1400, self.finish_study)

        else:
            if self.steps >= 5 or not self.words_dict:
                QTimer.singleShot(1400, self.different_style)
            else:
                # Переходим к следующему слову
                QTimer.singleShot(1400, self.load_words_write)