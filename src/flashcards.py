import os
import sys
from pathlib import Path
import pymorphy3

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtWidgets import QMessageBox, QListWidget, QListWidgetItem
from PyQt6.QtGui import QFont, QColor
import random
from PyQt6.QtMultimedia import QSoundEffect


class Flashcards:
    def __init__(self, card_label, flip_btn, know_btn, not_know_btn, prev_btn, db, stacked, labels,
                 progress_bar, labels_num_learn, updater):
        self.card_label = card_label
        self.flip_btn = flip_btn
        self.know_btn = know_btn
        self.not_know_btn = not_know_btn
        self.prev_btn = prev_btn
        self.db = db
        self.stacked = stacked
        self.labels = labels
        self.progress_bar = progress_bar
        self.learn_label = labels_num_learn[0]
        self.do_not_learn_label = labels_num_learn[-1]
        self.updater = updater

        self.learn_label.setText('0')
        self.do_not_learn_label.setText('0')

        self.words = []
        self.current_index = 0
        self.is_front = True

        self.card_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.card_label.mousePressEvent = lambda event: self.label_clicked(event)

        self.flip_sound = QSoundEffect()
        sound_path = os.path.abspath(resource_path("assets/sounds/page-flip-sound.wav"))
        self.flip_sound.setSource(QUrl.fromLocalFile(sound_path))
        self.flip_sound.setVolume(0.1)

        # Настройка стиля карточки
        self._setup_card_style()

        # Подключаем кнопки
        self.flip_btn.clicked.connect(self.flip_card)
        self.know_btn.clicked.connect(lambda: self.mark_known(True))
        self.not_know_btn.clicked.connect(lambda: self.mark_known(False))
        self.prev_btn.clicked.connect(self.prev_card)

    def label_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.flip_card()

    def _setup_card_style(self):
        """Настройка внешнего вида карточки"""
        self.card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_label.setWordWrap(True)
        self.card_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Normal))
        self.card_label.setMinimumHeight(250)
        self._update_card_style(is_front=True)

    def _update_card_style(self, is_front: bool):
        """Обновляет стиль в зависимости от стороны"""
        if is_front:
            style = """
                QLabel {
                    background-color: #e8f4fc;
                    color: #0d47a1;
                    border: 2px solid #2196F3;
                    border-radius: 16px;
                    padding: 40px;
                    font-weight: 500;
                }
            """
        else:
            style = """
                QLabel {
                    background-color: #f0f7ee;
                    color: #1b5e20;
                    border: 2px solid #4CAF50;
                    border-radius: 16px;
                    padding: 40px;
                    font-weight: 500;
                }
            """
        self.card_label.setStyleSheet(style)

    def load_words(self, words, module_id: int):
        self.module_id = module_id
        self.words = words
        random.shuffle(self.words)
        self.current_index = 0
        self.is_front = True
        self.learn_words = []
        self.not_learned_words = []
        self.show_card()
        self._show_front_side()
        self.learn_label.setStyleSheet('color: green')
        self.do_not_learn_label.setStyleSheet('color: red')

        # загружаем данные в progress bar
        self.progress_bar.setRange(0, len(self.words))
        self.progress_bar.setValue(0)

    def show_card(self):
        if not self.words:
            self.card_label.setText("Нет слов")
            self._update_card_style(is_front=True)
            return

        word = self.words[self.current_index]
        term = str(word[2]).strip() if word[2] else "(термин)"
        self.card_label.setText(term)
        self.is_front = True
        self._update_card_style(is_front=True)

    def flip_card(self):
        if not self.words:
            return

        if self.is_front:
            # Показываем обратную сторону
            word = self.words[self.current_index]
            definition = str(word[1]).strip() if word[1] else "(перевод)"

            self.card_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f4fc;
                    color: #0d47a1;
                    border: 2px solid #2196F3;
                    border-radius: 16px;
                    padding: 10px;
                    font-size: 14px;
                }
            """)
            self.card_label.setText("")

            # Через короткую задержку — показываем обратную сторону
            QTimer.singleShot(120, lambda: self._show_back_side(definition))
        else:
            self._show_front_side()

    def _show_back_side(self, text):
        self.card_label.setText(text)
        self.is_front = False
        self._update_card_style(is_front=False)

    def _show_front_side(self):
        word = self.words[self.current_index]
        term = str(word[2]).strip() if word[2] else "(термин)"

        self.card_label.setStyleSheet("""
            QLabel {
                background-color: #f0f7ee;
                color: #1b5e20;
                border: 2px solid #4CAF50;
                border-radius: 16px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.card_label.setText("")

        QTimer.singleShot(120, lambda: self.__final_show_front(term))

    def __final_show_front(self, term):
        self.card_label.setText(term)
        self.is_front = True
        self._update_card_style(is_front=True)

    def mark_known(self, known: bool):
        if not self.words:
            return

        word_id = self.words[self.current_index][0]
        self.db.mark_word_known(word_id, known)

        if known:
            self.learn_words.append(1)
            self.not_learned_words.append(0)
        else:
            self.learn_words.append(0)
            self.not_learned_words.append(1)

        self.learn_label.setText(str(sum(self.learn_words)))
        self.do_not_learn_label.setText(str(sum(self.not_learned_words)))

        self.progress_bar.setValue(self.current_index + 1)  # обновляем progress_bar

        if self.current_index < len(self.words) - 1:
            self.current_index += 1
            self.flip_sound.play()
            self.show_card()

        else:
            learned, not_learned = self.db.get_statistics_words_learned(self.module_id)
            total = learned + not_learned
            percent = round(learned / total * 100) if total > 0 else 0
            QMessageBox.information(
                self.card_label.window(),
                "Готово!",
                f"<h3>Повторение завершено!</h3>"
                f"Сегодня выучено слов: <b>{learned}</b>; не выучено: <b>{not_learned}</b>.<br>"
                f"<h4>Процент знания слов: {percent}%</h4>"
            )

            self.stacked.setCurrentIndex(self.stacked.currentIndex() - 1)  # возвращаемся в раздел с информацией о модуле

            self.updater()  # обновляет интерфейсы

    def prev_card(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.flip_sound.play()
            self.show_card()
            self.progress_bar.setValue(self.current_index)  # обновляем progress bar

            self.not_learned_words = self.not_learned_words[:-1]
            self.learn_words = self.learn_words[:-1]

            self.learn_label.setText(str(sum(self.learn_words)))
            self.do_not_learn_label.setText(str(sum(self.not_learned_words)))

    def is_active(self):
        return len(self.words) > 0


class StudyWords:
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


    def load_words(self, words, module_id: int):
        self.words = words
        self.module_id = module_id
        random.shuffle(self.words)
        self.stacked.setCurrentIndex(0)
        self.in_process = False
        self.list_widget.setEnabled(True)

        self.all_words = [i[-1] for i in self.words.copy()]
        self.unique_all_words = list(set([i[-1] for i in self.words.copy()]))

        # слова, когда нужно выбрать слово, основываясь по термину
        self.words_with_choice = [i[1] for i in self.words.copy()]
        self.words_without_choice = [i[-1] for i in self.words.copy()]

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

        if not self.words_not_choice:
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
        self.stacked_main.setCurrentIndex(self.stacked_main.currentIndex() - 2)

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


class ReStudyWords:
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
        self.list_widget.clear()
        self.in_process = False
        self.stacked_main.setCurrentIndex(0)
        self.words_with_choice = []
        self.words_without_choice = []

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


class TestWords:
    def __init__(self, label_guess, label_explanation, list_widget, line_edit_word,
                 ok_btn, stacked, stacked_main, theme, db, updater, parent=None):
        self.label_guess = label_guess
        self.label_guess.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_guess.setWordWrap(True)
        self.label_explanation = label_explanation
        self.list_widget = list_widget
        self.line_edit_word = line_edit_word
        self.ok_btn = ok_btn
        self.updater = updater
        self.theme_func = theme
        self.stacked = stacked
        self.stacked_main = stacked_main
        self.db = db
        self.in_process = False
        self.parent = parent
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


    def load_words(self, words, module_id: int):
        self.words = words
        self.correct_words = 0
        self.module_id = module_id
        random.shuffle(self.words)
        self.stacked.setCurrentIndex(0)
        self.in_process = False
        self.list_widget.setEnabled(True)

        half_words = len(self.words) // 2

        self.all_words = [i[-1] for i in self.words.copy()]
        self.unique_all_words = list(set([i[-1] for i in self.words.copy()]))

        # слова, когда нужно выбрать слово, основываясь по термину
        self.words_with_choice = [i[1] for i in self.words[:half_words + 1].copy()]  # половина слов
        self.words_without_choice = [i[-1] for i in self.words[:half_words + 1].copy()]  # половина слов

        self.word_meaning_dict = [(i[1], i[-1]) for i in self.words[half_words:].copy()]
        random.shuffle(self.word_meaning_dict)

        self.choice = True

        self.settings()

    def settings(self):
        self.words_choice = self.words_with_choice.copy()
        self.words_not_choice = self.words_without_choice.copy()

        self.words_dict = self.word_meaning_dict.copy()

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

        if not self.words_not_choice:  # защита от пустого списка
            return

        if res:
            # если ответ правильный
            item.setForeground(QColor("green"))
            item.setText('✅ ' + item.text())
            self.correct_words += 1
            word_id = self.db.get_word_id(self.words_not_choice[0], self.words_choice[0])
            self.db.mark_word_known(word_id, True)

            if self.words_not_choice:
                # удаляем слово и его значение
                del self.words_not_choice[0]
                del self.words_choice[0]

        else:
            # если ответ неправильный
            item.setForeground(QColor('red'))
            item.setText('❌ ' + item.text())
            self.highlight_correct_answer(self.words_not_choice[0])

            word_id = self.db.get_word_id(self.words_not_choice[0], self.words_choice[0])
            self.db.mark_word_known(word_id, False)

            if self.words_not_choice:
                # удаляем слово и его значение
                del self.words_not_choice[0]
                del self.words_choice[0]

        if not self.words_not_choice and not self.words_choice and not self.words_dict:
            QTimer.singleShot(1400, self.finish_study)

        else:
            if not self.words_choice and not self.words_not_choice:
                QTimer.singleShot(1400, self.different_style)
            else:
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

        self.updater()  # обновляем показатели в меню

        morph = pymorphy3.MorphAnalyzer()

        comment = morph.parse('вопрос')[0]

        QMessageBox.information(self.parent, 'Оценка',
                                        f'Вы правильно ответили на <span style="color: green;">{self.correct_words}'
                                        f' {comment.make_agree_with_number(self.correct_words).word}</span>.'
                                        f' Не правильно на <span style="color: red;">{len(self.words) - self.correct_words} '
                                        f'{comment.make_agree_with_number(len(self.words) - self.correct_words).word}</span>.')

        self.stacked_main.setCurrentIndex(self.stacked_main.currentIndex() - 3)

    def different_style(self):
        if self.stacked.currentIndex() == 0:
            self.stacked.setCurrentIndex(1)
            self.load_words_write()

        else:
            self.in_process = False
            self.list_widget.setEnabled(True)
            self.stacked.setCurrentIndex(0)
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
        self.line_edit_word.setEnabled(False)
        self.ok_btn.setEnabled(False)

        if ('_'.join([i.strip().strip(',.!?-=+/*') for i in self.line_edit_word.text().lower().strip().split()])
                == self.words_dict[0][1].lower().strip()):
            self.line_edit_word.setStyleSheet('color: green')
            self.line_edit_word.setText(self.line_edit_word.text().strip() + " ✅")
            self.correct_words += 1

            word_id = self.db.get_word_id(self.words_dict[0][1], self.words_dict[0][0])
            self.db.mark_word_known(word_id, True)

            del self.words_dict[0]

        else:
            self.line_edit_word.setStyleSheet('color: red')
            self.line_edit_word.setText(self.line_edit_word.text().strip() + " ❌")

            QMessageBox.information(
                self.label_explanation.window(),
                "Неправильный ответ",
                f"Правильный ответ: <b><span style='color: green;'>{self.words_dict[0][1]}</span></b>"
            )

            word_id = self.db.get_word_id(self.words_dict[0][1], self.words_dict[0][0])
            self.db.mark_word_known(word_id, False)

            del self.words_dict[0]

        if not self.words_dict:
            QTimer.singleShot(1400, self.finish_study)

        else:
            # Переходим к следующему слову
            QTimer.singleShot(1400, self.load_words_write)


def resource_path(relative_path):
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent
    return str(base_path / relative_path)