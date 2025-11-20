import random
import sys
import datetime

from PyQt6.QtWidgets import QMainWindow, QMenu, QInputDialog, QMessageBox, QDialog, QTableWidget, QTableWidgetItem, \
    QVBoxLayout, QHeaderView, QListWidget, QLineEdit, QLabel, QHBoxLayout, QRadioButton, QGroupBox, QDialogButtonBox, \
    QPushButton, QTextBrowser
from PyQt6.QtWidgets import QCalendarWidget, QApplication
from PyQt6.QtGui import QColor, QTextCharFormat
from src.ui.words_window import Ui_MainWindow
from src.database import VocabularyDatabase
from pathlib import Path
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QAction, QFont, QIcon
from src.dialog import AddModulesToFolderDialog, DeleteModulesDialog, DeleteFoldersDialog, AddWordsDialog
from src.flashcards import Flashcards, StudyWords, ReStudyWords, TestWords
from src.radio_window import RadioTabHandler
from src.ai_window import AI


class WordsWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.db = VocabularyDatabase()  # подключаем/открываем бд

        if self.db.get_password_hash() is not None:
            self.check_password()

        if not self.db.get_user_info():
            self.register_user()

        self.setupUi(self)

        self.db.add_date_entry()

        self.setMinimumWidth(600)
        self.setMinimumHeight(600)

        self.setWindowTitle('Fluentify')
        self.setWindowIcon(QIcon(resource_path('image/fluentify_icon.ico')))

        self.setGeometry(400, 200, 750, 630)

        self.radio_handler = RadioTabHandler(self, self.db)
        self.ai_handler = AI(self, self.db)

        self.load_modules()
        self.load_folders()

        self.back_module_btn.clicked.connect(self.back_module_btn_clicked)
        self.back_foldure_btn.clicked.connect(self.back_folder_btn_clicked)
        self.back_folder_module_btn.clicked.connect(self.back_folder_module_btn_clicked)
        self.back_module_cards_btn.clicked.connect(self.back_module_cards_btn_clicked)
        self.back_folder_cards_btn.clicked.connect(self.back_folder_cards_clicked)
        self.back_study_btn.clicked.connect(self.back_study_module)
        self.back_study_btn_2.clicked.connect(self.back_study_module)
        self.back_study_folder.clicked.connect(self.back_study_folder_clicked)
        self.back_study_folder_2.clicked.connect(self.back_study_folder_clicked)
        self.back_btn_main.clicked.connect(self.back_learn_main)
        self.back_btn_main_1.clicked.connect(self.back_learn_main)
        self.back_test_btn_folder.clicked.connect(self.back_btn)

        self.theme.currentIndexChanged.connect(self.apply_theme)

        self.apply_theme(0)  # устанавливаем тему

        self.flashcards = Flashcards(
            card_label=self.card_label,
            flip_btn=self.flip_btn,
            know_btn=self.know_btn,
            not_know_btn=self.not_know_btn,
            prev_btn=self.prev_btn,
            db=self.db,
            stacked=self.stackedWidget,
            labels=(self.words_amount_label, self.amount_learned_words_label, self.amount_not_learned_words_label),
            progress_bar=self.progressBar_learn,
            labels_num_learn=(self.words_know_label, self.words_do_not_know_label),
            updater=self.update_words_after_learn
        )  # подключаем flashcards

        self.flashcards_folder = Flashcards(
            card_label=self.card_folder_label,
            flip_btn=self.flip_folder_btn,
            know_btn=self.know_folder_btn,
            not_know_btn=self.not_know_folder_btn,
            prev_btn=self.prev_folder_btn,
            db=self.db,
            stacked=self.stackedWidget_2,
            labels=(self.words_amount_folder_label, self.amount_learned_words_folder_label,
                    self.amount_not_learned_words_folder_label),
            progress_bar=self.progressBar_folder_learn,
            labels_num_learn=(self.words_know_folder_label, self.words_do_not_know_folder_label),
            updater=self.update_words_after_learn
        )  # подключаем flahcards для папок

        self.listWidget_folders.setSpacing(2)
        self.listWidget_modules.setSpacing(2)

        # В твоём классе WordsWindow или elsewhere
        self.calendar = HighlightCalendar(self.db, self)
        self.verticalLayout_43.addWidget(self.calendar)

        self.greet_user()

        self.listWidget_modules.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.listWidget_modules.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.listWidget_folders.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.listWidget_folders.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.listWidget_folders.itemClicked.connect(self.on_folder_clicked)
        self.listWidget_modules.itemClicked.connect(self.on_module_clicked)
        self.listWidget_folder_module.itemClicked.connect(self.on_folder_module_clicked)

        self.line_folder.textChanged.connect(self.search_folders)
        self.line_folder_module.textChanged.connect(self.search_folders_modules)
        self.line_module.textChanged.connect(self.search_modules)

        self.listWidget_modules.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget_modules.customContextMenuRequested.connect(self.show_modules_context_menu)

        self.listWidget_folders.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget_folders.customContextMenuRequested.connect(self.show_folders_context_menu)

        self.listWidget_folder_module.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget_folder_module.customContextMenuRequested.connect(self.show_folders_modules_context_menu)
        self.listWidget_folder_module.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.listWidget_folder_module.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.add_module.clicked.connect(self.add_mod)  # при нажатии на кнопку добавление
        self.add_folder.clicked.connect(self.add_fold)
        self.add_folder_module.clicked.connect(self.add_mod)

        self.insert_module.clicked.connect(self.add_existing_modules_to_folder)

        self.change_pas_name_btn.clicked.connect(self.change_user_info)

        self.restudy_words_btn.clicked.connect(self.restudy_words_clicked)

        self.delete_module.clicked.connect(self.delete_modules)
        self.delete_folder_module.clicked.connect(self.delete_modules)
        self.delete_folder.clicked.connect(self.delete_folders)

        # кнопки для изучения слов при открытии сразу в модуле
        self.cards_btn.clicked.connect(self.cards_words)
        self.learn_btn.clicked.connect(self.learn_words)
        self.test_btn.clicked.connect(self.test_words)

        # кнопки для изучения слов при открытии в папке
        self.cards_folder_btn.clicked.connect(self.cards_words)
        self.learn_folder_btn.clicked.connect(self.learn_words)
        self.test_folder_btn.clicked.connect(self.test_words)

        self.current_folder_id = None  # id текущей выбранной папки
        self.current_module_id = None  # id текущей выбранного модуля
        self.current_folder_module_id = None  # id текущей выбранного модуля в папке

        self.edit_words_btn.clicked.connect(self.update_words_in_module)  # кнопка изменения слов, тематики и описания
        self.edit_words_folder_btn.clicked.connect(self.update_words_in_module)  # кнопка изменения слов

        # подключаем если курсор был наведен на qlabel с информацией о словах, которые пользователь выучил
        self.words_amount_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.words_amount_label.mousePressEvent = self.words_amount_module_clicked

        self.amount_learned_words_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.amount_learned_words_label.mousePressEvent = self.words_amount_learned_module_clicked

        self.amount_not_learned_words_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.amount_not_learned_words_label.mousePressEvent = self.words_amount_not_learned_module_clicked

        self.words_amount_folder_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.words_amount_folder_label.mousePressEvent = self.words_amount_module_folder_clicked

        self.amount_learned_words_folder_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.amount_learned_words_folder_label.mousePressEvent = self.words_amount_learned_module_folder_clicked

        self.amount_not_learned_words_folder_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.amount_not_learned_words_folder_label.mousePressEvent = self.words_amount_not_learned_module_folder_clicked

        self.back_test_1.clicked.connect(self.back_test_btn)
        self.back_study_btn_2.clicked.connect(self.back_test_btn)

        self.add_key_openrouter.clicked.connect(self.add_key)

    def resource_path(self, relative_path):
        import sys, os
        if hasattr(sys, '_MEIPASS'):  # если приложение запущено как .exe
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    def back_btn(self):
        self.stackedWidget_2.setCurrentIndex(2)

    def back_test_btn(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 3)

    def restudy_words_clicked(self):
        words = self.db.get_all_not_learned_words()
        random.shuffle(words)
        words = words[:10]

        if not words:
            QMessageBox.information(self, 'Повторение', 'Невыученных слов нет! Вы молодцы!')
            return

        self.stackedWidget_5.setCurrentIndex(1)

        self.restudy_words = ReStudyWords(
            label_guess=self.word_label_main,
            label_explanation=self.label_explanation_main,
            list_widget=self.listWidget,
            line_edit_word=self.lineEdit_word_meaning_main,
            ok_btn=self.ok_btn_main,
            stacked=self.stackedWidget_6,
            stacked_main=self.stackedWidget_5,
            theme=self.get_theme
        )

        self.restudy_words.load_words(words)

    def back_learn_main(self):
        self.stackedWidget_5.setCurrentIndex(0)

    def change_user_info(self):
        class Register(QDialog):
            def __init__(self, db, parent=None):
                super().__init__(parent)

                self.db = db
                data = self.db.get_user_info()

                vbox = QVBoxLayout()
                hbox = QHBoxLayout()
                hbox_1 = QHBoxLayout()

                self.setWindowTitle('Регистрация')
                self.setFixedHeight(300)
                self.setFixedWidth(300)

                label_name = QLabel('Ваше имя:')
                hbox.addWidget(label_name)

                self.user_name = QLineEdit(data[1])
                self.user_name.setMinimumHeight(30)
                self.user_name.setPlaceholderText('Введите ваше имя')
                hbox.addWidget(self.user_name)

                vbox.addLayout(hbox)

                self.radio_btn_choice_yes = QRadioButton('Пароль')
                self.radio_btn_choice_no = QRadioButton('Без пароля')
                self.radio_btn_choice_yes.setChecked(True)
                self.radio_btn_choice_yes.toggled.connect(self.radio_btn_toggled)
                self.radio_btn_choice_no.toggled.connect(self.radio_btn_toggled)
                hbox_1.addWidget(self.radio_btn_choice_yes)
                hbox_1.addWidget(self.radio_btn_choice_no)

                group_box = QGroupBox('Вы будете добавлять пароль?')
                group_box.setLayout(hbox_1)
                group_box.setMaximumHeight(70)
                vbox.addWidget(group_box)

                self.password_line = QLineEdit()
                self.password_line.setMinimumHeight(30)
                self.password_line.setPlaceholderText('Введите пароль')
                hbox_2 = QHBoxLayout()
                hbox_2.addWidget(self.password_line)
                self.password_line.setEchoMode(QLineEdit.EchoMode.Password)

                self.toggle_password_btn = QPushButton("👁️")
                self.toggle_password_btn.setFixedWidth(50)
                self.toggle_password_btn.setCheckable(True)
                self.toggle_password_btn.setChecked(False)
                self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
                hbox_2.addWidget(self.toggle_password_btn)
                vbox.addLayout(hbox_2)

                button_box = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                vbox.addWidget(button_box)

                self.setLayout(vbox)

            def radio_btn_toggled(self):
                radio_btn = self.sender()

                if radio_btn.text() == 'Пароль':
                    self.password_line.show()
                    self.toggle_password_btn.show()
                    self.password_line.setText('')
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setChecked(False)

                else:
                    self.password_line.hide()
                    self.toggle_password_btn.hide()

            def accept(self):
                if self.user_name.text().strip() == '':
                    QMessageBox.warning(self, 'Ошибка', 'Имя не может быть пустой строкой.')
                    return

                if self.radio_btn_choice_yes.isChecked() and self.password_line.text().strip() == '':
                    QMessageBox.warning(self, 'Ошибка', 'Пароль не может быть пустой строкой.')
                    return

                if self.radio_btn_choice_no.isChecked():
                    self.db.update_user_info(self.user_name.text())

                else:
                    self.db.update_user_info(self.user_name.text(), self.password_line.text())
                super().accept()

            def toggle_password_visibility(self, checked):
                if checked:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Normal)
                    self.toggle_password_btn.setText("👁️")
                else:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setText("👁️")


        class CheckPas(QDialog):
            def __init__(self, db, flag, parent=None):
                super().__init__(parent)

                self.flag = flag

                self.setWindowTitle('Проверка пароля')
                self.setFixedWidth(300)
                self.setFixedHeight(200)

                self.db = db

                vbox = QVBoxLayout()
                hbox = QHBoxLayout()

                label = QLabel('Пароль:')
                self.password_line = QLineEdit()
                self.password_line.setPlaceholderText('Введите пароль')
                self.password_line.setFixedHeight(40)
                self.password_line.setEchoMode(QLineEdit.EchoMode.Password)

                self.toggle_password_btn = QPushButton("👁️")
                self.toggle_password_btn.setFixedWidth(50)
                self.toggle_password_btn.setCheckable(True)
                self.toggle_password_btn.setChecked(False)
                self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)

                hbox.addWidget(label)
                hbox.addWidget(self.password_line)
                hbox.addWidget(self.toggle_password_btn)

                vbox.addLayout(hbox)

                button_box = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                vbox.addWidget(button_box)

                self.setLayout(vbox)

            def toggle_password_visibility(self, checked):
                if checked:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Normal)
                    self.toggle_password_btn.setText("👁️")
                else:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setText("👁️")

            def accept(self):
                if self.db.verify_password(self.password_line.text().strip()):
                    self.flag = True
                    super().accept()

                else:
                    QMessageBox.warning(self, 'Ошибка', 'Неправильный пароль, в изменении пароля отказано.')

            def reject(self):
                self.flag = False
                super().reject()

            def get_flag(self):
                return self.flag


        flag = True
        if self.db.get_password_hash() is not None:
            check = CheckPas(self.db, flag, self)
            check.exec()
            flag = check.get_flag()

        if flag:  # если пользователь не закрыл окно
            reg = Register(self.db, self)
            reg.exec()

            self.greet_user()  # обновляем приветствие


    def greet_user(self):
        user_name = self.db.get_user_info()[1]
        current_time = datetime.datetime.now().time()
        if datetime.time(9) >= current_time >= datetime.time(0):
            text = f'Доброе утро, {user_name}!'
        elif datetime.time(17) >= current_time > datetime.time(9):
            text = f'Добрый день, {user_name}!'
        else:
            text = f'Добрый вечер, {user_name}!'

        self.greeting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.greeting_label.setText(f'<h3>{text}</h3>')

    def check_password(self):
        class CheckPassword(QDialog):
            def __init__(self, db, parent=None):
                super().__init__(parent)

                self.setWindowTitle('Проверка пароля')
                self.setFixedWidth(250)
                self.setFixedHeight(150)
                self.db = db

                vbox = QVBoxLayout()
                hbox = QHBoxLayout()

                label = QLabel('Пароль:')
                self.password_line = QLineEdit()
                self.password_line.setPlaceholderText('Введите пароль')
                self.password_line.setMinimumHeight(40)
                self.password_line.setEchoMode(QLineEdit.EchoMode.Password)

                self.toggle_password_btn = QPushButton("👁️")
                self.toggle_password_btn.setFixedWidth(30)
                self.toggle_password_btn.setCheckable(True)
                self.toggle_password_btn.setChecked(False)
                self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
                hbox.addWidget(label)
                hbox.addWidget(self.password_line)
                hbox.addWidget(self.toggle_password_btn)

                vbox.addLayout(hbox)

                button_box = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                vbox.addWidget(button_box)

                self.setLayout(vbox)

            def toggle_password_visibility(self, checked):
                if checked:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Normal)
                    self.toggle_password_btn.setText("👁️")
                else:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setText("👁️")

            def accept(self):
                res = self.db.verify_password(self.password_line.text().strip())
                if not res:
                    QMessageBox.warning(self, 'Ошибка', 'Неправильный пароль')
                    return

                super().accept()

            def reject(self):
                sys.exit()


        checkPassword = CheckPassword(self.db, self)
        checkPassword.exec()

    def register_user(self):
        class Register(QDialog):
            def __init__(self, db, parent=None):
                super().__init__(parent)

                self.db = db

                vbox = QVBoxLayout()
                hbox = QHBoxLayout()
                hbox_1 = QHBoxLayout()

                self.setWindowTitle('Регистрация')
                self.setFixedHeight(300)
                self.setFixedWidth(300)

                label_name = QLabel('Ваше имя:')
                hbox.addWidget(label_name)

                self.user_name = QLineEdit()
                self.user_name.setMinimumHeight(30)
                self.user_name.setPlaceholderText('Введите ваше имя')
                hbox.addWidget(self.user_name)

                vbox.addLayout(hbox)

                self.radio_btn_choice_yes = QRadioButton('Пароль')
                self.radio_btn_choice_no = QRadioButton('Без пароля')
                self.radio_btn_choice_yes.setChecked(True)
                self.radio_btn_choice_yes.toggled.connect(self.radio_btn_toggled)
                self.radio_btn_choice_no.toggled.connect(self.radio_btn_toggled)
                hbox_1.addWidget(self.radio_btn_choice_yes)
                hbox_1.addWidget(self.radio_btn_choice_no)

                group_box = QGroupBox('Вы будете добавлять пароль?')
                group_box.setLayout(hbox_1)
                group_box.setMaximumHeight(70)
                vbox.addWidget(group_box)

                hbox_2 = QHBoxLayout()

                self.password_line = QLineEdit()
                self.password_line.setMinimumHeight(30)
                self.password_line.setPlaceholderText('Введите пароль')
                self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                hbox_2.addWidget(self.password_line)

                self.toggle_password_btn = QPushButton("👁️")
                self.toggle_password_btn.setCheckable(True)
                self.toggle_password_btn.setChecked(False)
                self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
                hbox_2.addWidget(self.toggle_password_btn)

                button_box = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                vbox.addLayout(hbox_2)
                vbox.addWidget(button_box)

                self.setLayout(vbox)

            def toggle_password_visibility(self, checked):
                if checked:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Normal)
                    self.toggle_password_btn.setText("👁️")
                else:
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setText("👁️")

            def radio_btn_toggled(self):
                radio_btn = self.sender()

                if radio_btn.text() == 'Пароль':
                    self.password_line.show()
                    self.toggle_password_btn.show()
                    self.password_line.setText('')
                    self.password_line.setEchoMode(QLineEdit.EchoMode.Password)
                    self.toggle_password_btn.setChecked(False)

                else:
                    self.password_line.hide()
                    self.toggle_password_btn.hide()

            def accept(self):
                if self.user_name.text().strip() == '':
                    QMessageBox.warning(self, 'Ошибка', 'Имя не может быть пустой строкой.')
                    return

                if self.radio_btn_choice_yes.isChecked() and self.password_line.text().strip() == '':
                    QMessageBox.warning(self, 'Ошибка', 'Пароль не может быть пустой строкой.')
                    return

                if self.radio_btn_choice_no.isChecked():
                    self.db.set_user_info(self.user_name.text())

                else:
                    self.db.set_user_info(self.user_name.text(), self.password_line.text())
                super().accept()

            def reject(self):
                sys.exit()


        reg = Register(self.db, self)
        reg.exec()

    def apply_theme(self, index: int):
        '''использование стилей'''
        if index == 0:
            theme_name = 'light'
        else:
            theme_name = 'dark'

        theme_path = Path(__file__).parent.parent / 'assets' / 'themes' / f'{theme_name}.qss'

        with open(theme_path, 'r', encoding='utf-8') as file:
            style = file.read()
            self.setStyleSheet(style)

    def get_theme(self):
        if self.theme.currentIndex() == 0:
            return 'light'
        return 'dark'

    def back_study_module(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 2)

    def back_study_folder_clicked(self):
        self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() - 2)

    def back_module_btn_clicked(self):
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 1)
        self.current_module_id = None

    def back_folder_btn_clicked(self):
        self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() - 1)
        self.current_folder_id = None

    def back_folder_module_btn_clicked(self):
        self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() - 1)
        self.current_folder_module_id = None

    def back_module_cards_btn_clicked(self):
        self.update_words_after_learn()
        self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex() - 1)

    def back_folder_cards_clicked(self):
        self.update_words_after_learn()
        self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() - 1)

    def show_modules_context_menu(self, position):
        item = self.listWidget_modules.itemAt(position)

        if item is None:
            return

        context_menu = QMenu(self)

        action1 = QAction('Переименовать', self)
        action2 = QAction('Удалить', self)
        action3 = QAction('Создать', self)

        context_menu.addAction(action1)
        context_menu.addAction(action2)
        context_menu.addAction(action3)

        selected = context_menu.exec(self.listWidget_modules.mapToGlobal(position))
        if selected == action1:
            self.rename_mod(item)
        elif selected == action2:
            self.delete_mod(item)
        elif selected == action3:
            self.add_mod(folder_id=None)

    def show_folders_modules_context_menu(self, position):
        item = self.listWidget_folder_module.itemAt(position)

        if item is None:
            return

        context_menu = QMenu(self)

        action1 = QAction('Переименовать', self)
        action2 = QAction('Удалить', self)
        action3 = QAction('Создать', self)

        context_menu.addAction(action1)
        context_menu.addAction(action2)
        context_menu.addAction(action3)

        selected = context_menu.exec(self.listWidget_folder_module.mapToGlobal(position))
        if selected == action1:
            self.rename_mod(item)
        elif selected == action2:
            self.delete_mod(item, flag=False)
        elif selected == action3:
            self.add_folder_module.click()

    def add_mod(self, folder_id=None):
        '''добавление модуля, без добавления в папку'''
        name, ok_pressed = QInputDialog.getText(
            self, 'Создание модуля', 'Введите название модуля:'
        )
        if ok_pressed:
            try:
                if self.sender() == self.add_folder_module:
                    folder_id = self.current_folder_id
                elif folder_id is False:
                    folder_id = None

                self.db.add_module(name.strip(),folder_id=folder_id)

                if folder_id is None:
                    self.search_modules(self.line_module.text())
                else:
                    self.search_folders_modules(self.line_folder_module.text())
                    self.search_modules(self.line_module.text())

            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def add_fold(self):
        name, ok_pressed = QInputDialog.getText(
            self, 'Создание папки', 'Введите название папки:'
        )
        if ok_pressed:
            try:
                self.db.add_folder(name.strip())
                self.search_folders(self.line_folder.text())
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка", str(e))

    def rename_mod(self, item):
        id_module = item.data(100)
        old_name = item.text()

        name, ok_pressed = QInputDialog.getText(self, 'Изменение названия модуля',
                                                'Введите новое название модуля', text=old_name)

        if ok_pressed:
            if name == old_name:
                pass
            else:
                res = self.db.rename_module(name, id_module)
                if res:
                    item.setText(name.strip())
                    self.search_modules(self.line_module.text())
                    self.search_folders_modules(self.line_folder_module.text())

                else:
                    QMessageBox.warning(self, "Ошибка", "Модуль с таким названием уже существует, либо вы ввели "
                                                        "пустую строку.")

    def delete_mod(self, item, flag=True):
        id_module = item.data(100)
        name = item.text()

        reply = QMessageBox.question(self, 'Подтверждение', f'Вы уверены, что хотите удалить модуль {name}?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            query = self.line_module.text()

            self.db.delete_module(id_module)

            if flag:
                row = self.listWidget_modules.row(item)
                self.listWidget_modules.takeItem(row)

                self.search_modules(query)
                self.search_folders_modules(self.line_folder_module.text())
            else:  # если в папке
                row = self.listWidget_folder_module.row(item)
                self.listWidget_folder_module.takeItem(row)

                self.search_modules(self.line_module.text())
                self.search_folders_modules(query)

        else:
            pass

    def show_folders_context_menu(self, position):
        item = self.listWidget_folders.itemAt(position)
        if item is None:
            return

        context_menu = QMenu(self)

        action1 = QAction('Переименовать', self)
        action2 = QAction('Удалить', self)
        action3 = QAction('Создать', self)

        context_menu.addAction(action1)
        context_menu.addAction(action2)
        context_menu.addAction(action3)

        selected = context_menu.exec(self.listWidget_folders.mapToGlobal(position))
        if selected == action1:
            self.rename_fold(item)
        elif selected == action2:
            self.delete_fold(item)
        elif selected == action3:
            self.add_fold()
        

    def rename_fold(self, item):
        id_module = item.data(100)
        old_name = item.text()

        name, ok_pressed = QInputDialog.getText(self, 'Изменение названия папки',
                                                'Введите новое название папки', text=old_name)

        if ok_pressed:
            if name == old_name:
                pass
            else:
                res = self.db.rename_folder(name, id_module)
                if res:
                    item.setText(name.strip())

                else:
                    QMessageBox.warning(self, "Ошибка", "Папка с таким названием уже существует, либо вы ввели"
                                                        "пустую строку.")

    def delete_fold(self, item):
        id_module = item.data(100)
        name = item.text()

        reply = QMessageBox.question(self, 'Подтверждение', f'Вы уверены, что хотите удалить папку {name}?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            query = self.line_module.text()

            self.db.delete_folder(id_module)

            row = self.listWidget_folders.row(item)
            self.listWidget_folders.takeItem(row)


            self.search_modules(query)

    def load_folders(self):
        """Загружает папки на страницу 0 words_stack"""
        self.listWidget_folders.clear()
        for folder_id, name in self.db.get_all_folders():
            self.listWidget_folders.addItem(name)
            item = self.listWidget_folders.item(self.listWidget_folders.count() - 1)
            item.setData(100, folder_id)

    def on_folder_clicked(self, item):
        """При клике на папку — показываем модули (страница 1)"""
        folder_id = item.data(100)
        self.load_modules_in_folder(folder_id)
        self.current_folder_id = item.data(100)
        self.stackedWidget_2.setCurrentIndex(1)

    def on_module_clicked(self, item):
        """При клике на модуль — показываем слова (страница 2)"""
        module_id = item.data(100)
        self.current_module_id = module_id
        res = False
        if self.db.has_words(module_id):  # проверяем есть ли слова (True -> нет; False -> есть)
            res = self.add_words(module_id)
            # вызываем метод для добавления слов; возвращает True если пользователь добавил слова
        else:  # если у пользователя уже есть слова в модуле
            self.stackedWidget.setCurrentIndex(1)  # переключаем на другую страницу
            self.words_design(module_id)

        if res:  # если пользователь добавил слова в модуль
            self.stackedWidget.setCurrentIndex(1)  # переключаем на другую страницу
            self.words_design(module_id)

    def add_words(self, module_id):
        dialog = AddWordsDialog(module_id, self.db, self)  # подключаем класс, который добавляет слова
        if dialog.exec() == QDialog.DialogCode.Accepted:  # если слова были успешно добавлены
            QMessageBox.information(self, "Успех", "Слова успешно добавлены!")
            return True
        return False

    def on_folder_module_clicked(self, item):
        module_id = item.data(100)
        self.current_folder_module_id = module_id
        res = False

        if self.db.has_words(module_id):  # проверяем есть ли слова (True -> нет; False -> есть)
            res = self.add_words(module_id)
            # вызываем метод для добавления слов; возвращает True если пользователь добавил слова
        else:  # если у пользователя уже есть слова в модуле
            self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() + 1)  # переключаем на другую страницу
            self.words_design(module_id, folder=True)

        if res:  # если пользователь добавил слова в модуль
            self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() + 1)  # переключаем на другую страницу
            self.words_design(module_id, folder=True)

    def load_modules_in_folder(self, folder_id: int):
        self.listWidget_folder_module.clear()
        for module_id, name in self.db.get_modules_in_folder(folder_id):
            self.listWidget_folder_module.addItem(name)
            item = self.listWidget_folder_module.item(self.listWidget_folder_module.count() - 1)
            item.setData(100, module_id)

    def load_modules(self):
        """Загружает папки на страницу 0 words_stack"""
        self.listWidget_modules.clear()
        for folder_id, name in self.db.get_all_modules():
            self.listWidget_modules.addItem(name)
            item = self.listWidget_modules.item(self.listWidget_modules.count() - 1)
            item.setData(100, folder_id)

        self.stackedWidget.setCurrentIndex(0)

    def search_modules(self, text):
        '''ищем модули'''
        modules = self.db.get_all_searched_modules(text)
        self.show_modules(modules)

    def show_modules(self, modules):
        '''выводить только модули, которые пользователь искал'''
        self.listWidget_modules.clear()

        for module_id, name in modules:
            self.listWidget_modules.addItem(name)
            item = self.listWidget_modules.item(self.listWidget_modules.count() - 1)
            item.setData(100, module_id)

    def search_folders(self, text):
        '''ищем папки'''
        folders = self.db.get_all_searched_folders(text)
        self.show_folders(folders)

    def show_folders(self, folders):
        '''выводить только папки, которые пользователь искал'''
        self.listWidget_folders.clear()

        for folder_id, name in folders:
            self.listWidget_folders.addItem(name)
            item = self.listWidget_folders.item(self.listWidget_folders.count() - 1)
            item.setData(100, folder_id)

    def search_folders_modules(self, text):
        modules = self.db.get_all_searched_modules(text, folder_id=self.current_folder_id)
        self.show_folder_modules(modules)

    def show_folder_modules(self, modules):
        '''Отображает найденные модули в listWidget_folder_module'''
        self.listWidget_folder_module.clear()
        for module_id, name in modules:
            self.listWidget_folder_module.addItem(name)
            item = self.listWidget_folder_module.item(self.listWidget_folder_module.count() - 1)
            item.setData(100, module_id)

    def add_existing_modules_to_folder(self):
        """Открывает диалог для добавления существующих (непривязанных) модулей в текущую папку"""
        if self.current_folder_id is None:
            QMessageBox.warning(self, "Ошибка", "Не выбрана папка для добавления модулей.")
            return

        # Получаем модули без папки
        unassigned_modules = self.db.get_unassigned_modules()
        if not unassigned_modules:
            QMessageBox.information(self, "Информация", "Нет модулей вне папок для добавления.")
            return

        dialog = AddModulesToFolderDialog(unassigned_modules, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_module_ids()

            if selected_ids:
                # Обновляем folder_id для выбранных модулей
                fl = False
                for module_id in selected_ids:
                    res = self.db.assign_module_to_folder(module_id, self.current_folder_id)
                    if not res:
                        fl = True

                self.load_modules_in_folder(self.current_folder_id)

                self.search_modules(self.line_module.text())
                self.search_folders_modules(self.line_folder_module.text())

                if not fl:
                    QMessageBox.information(self, "Успех", f"Модули успешно добавлены в папку.")

                else:
                    QMessageBox.information(self, "Успех", 'К сожалению, не все модули были добавлены,'
                                                           ' так как они имели схожее название'
                                                           ' с уже созданными модулями.')

    def delete_modules(self):
        '''удаление модулей'''
        if self.sender() == self.delete_folder_module:
            modules = self.db.get_all_searched_modules(text='', folder_id=self.current_folder_id)

        else:
            modules = self.db.get_all_modules()

        if not modules:
            QMessageBox.information(self, "Информация", "Нет модулей для удаления.")
            return

        dialog = DeleteModulesDialog(modules, self)  # запускаем диалоговое окно

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_module_ids()

            if selected_ids:
                for module_id in selected_ids:
                    self.db.delete_module(module_id)

                self.load_modules_in_folder(self.current_folder_id)
                self.search_folders_modules(self.line_folder_module.text())

                self.search_modules(self.line_module.text())
                self.search_folders_modules(self.line_folder_module.text())

                QMessageBox.information(self, "Успех", f"Модули успешно удалены.")

    def delete_folders(self):
        '''удаление папок'''
        folders = self.db.get_all_folders()

        if not folders:
            QMessageBox.information(self, "Информация", "Нет папок для удаления.")
            return

        dialog = DeleteFoldersDialog(folders, self)  # запускаем диалоговое окно

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_module_ids()

            if selected_ids:
                for folder_id in selected_ids:
                    self.db.delete_folder(folder_id)

                self.load_folders()
                self.search_folders_modules(self.line_folder_module.text())

                self.search_folders(self.line_folder.text())
                self.search_modules(self.line_module.text())
                self.search_folders_modules(self.line_folder_module.text())

                QMessageBox.information(self, "Успех", f"Папки успешно удалены.")

    def words_design(self, module_id, folder: bool=False):
        '''заполняет необходимую информацию в окне слов(тематика, описание и тд.)'''
        if not folder:  # если мы открыли слова в модуле
            self.textBrowser_topic.setText(self.db.get_topic(module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(module_id)
            self.words_amount_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_label.setText('Невыученных: ' + str(words_not_learned))

            self.label_topic.setStyleSheet('color: rgb(41, 72, 226)')
            self.description_label.setStyleSheet('color: rgb(212, 15, 192)')
            self.amount_learned_words_label.setStyleSheet('color: green')
            self.amount_not_learned_words_label.setStyleSheet('color: red')
            self.description_textBrowser.setText(self.db.get_description(module_id))

        else:  # если мы открыли слова через папку
            self.textBrowser_topic_folder.setText(self.db.get_topic(module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(module_id)
            self.words_amount_folder_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_folder_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_folder_label.setText('Невыученных: ' + str(words_not_learned))

            self.label_folder_topic.setStyleSheet('color: rgb(41, 72, 226)')
            self.label_folder_description.setStyleSheet('color: rgb(212, 15, 192)')
            self.amount_learned_words_folder_label.setStyleSheet('color: green')
            self.amount_not_learned_words_folder_label.setStyleSheet('color: red')
            self.textBrowser_folder_description.setText(self.db.get_description(module_id))

    def add_key(self):
        class Add(QDialog):
            def __init__(self, db, parent=None):
                super().__init__(parent)

                self.db = db
                self.setWindowTitle('Добавить ключ для ИИ')
                vbox = QVBoxLayout()
                la = QLabel('Ключ:')
                vbox.addWidget(la)

                self.lineedit = QLineEdit()
                self.lineedit.setPlaceholderText('Введите ключ')
                vbox.addWidget(self.lineedit)

                button_box = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
                )
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                vbox.addWidget(button_box)

                self.setLayout(vbox)

            def accept(self):
                self.db.set_key(self.lineedit.text().strip())
                super().accept()

        a = Add(self.db, self)
        a.exec()

    def update_words_in_module(self):
        '''Метод который редактирует слова'''
        if self.sender() == self.edit_words_btn:
            module_id = self.current_module_id

        elif self.sender() == self.edit_words_folder_btn:
            module_id = self.current_folder_module_id

        dialog = AddWordsDialog(module_id, self.db, self)  # подключаем класс, который добавляет слова
        dialog.set_description(self.db.get_description(module_id))  # текст описания модуля
        dialog.set_topic(self.db.get_topic(module_id))  # текст тематики

        for i in self.db.get_words_in_module(module_id):
            native_word, translated_word = i
            dialog.add_word_pair_file(translated_word, native_word)

        dialog.del_line()

        if dialog.exec() == QDialog.DialogCode.Accepted:  # если слова были успешно добавлены
            QMessageBox.information(self, "Успех", "Слова успешно обновлены!")

        if self.current_module_id is not None:
            # для слов в модулях
            self.textBrowser_topic.setText(self.db.get_topic(self.current_module_id))
            self.description_textBrowser.setPlainText(self.db.get_description(self.current_module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(self.current_module_id)
            self.words_amount_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_label.setText('Невыученных: ' + str(words_not_learned))

        if self.current_folder_module_id is not None:
            # для слов в папках
            self.textBrowser_topic_folder.setText(self.db.get_topic(self.current_folder_module_id))
            self.textBrowser_folder_description.setPlainText(self.db.get_description(self.current_folder_module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(self.current_folder_module_id)
            self.words_amount_folder_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_folder_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_folder_label.setText('Невыученных: ' + str(words_not_learned))

    def cards_words(self):
        if self.sender() == self.cards_btn:
            words = self.db.get_words_for_module(self.current_module_id)

            self.flashcards.load_words(words, self.current_module_id)
            self.words_know_label.setText('0')
            self.words_do_not_know_label.setText('0')
            self.stackedWidget.setCurrentIndex(2)

        elif self.sender() == self.cards_folder_btn:
            words = self.db.get_words_for_module(self.current_folder_module_id)

            self.flashcards_folder.load_words(words, self.current_folder_module_id)
            self.words_know_folder_label.setText('0')
            self.words_do_not_know_folder_label.setText('0')
            self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() + 1)

    def learn_words(self):
        if self.sender() == self.learn_btn:
            words = self.db.get_words_for_module(self.current_module_id)

            self.study_words = StudyWords(
                label_guess=self.word_label,
                label_explanation=self.word_explanation,
                list_widget=self.listWidget_module,
                line_edit_word=self.lineEdit_word_meaning,
                ok_btn=self.ok_btn,
                stacked=self.stackedWidget_3,
                stacked_main=self.stackedWidget,
                theme=self.get_theme
            )

            self.study_words.load_words(words, self.current_module_id)

            self.stackedWidget.setCurrentIndex(3)

        elif self.sender() == self.learn_folder_btn:
            words = self.db.get_words_for_module(self.current_folder_module_id)

            self.study_words_folder = StudyWords(
                label_guess=self.word_folder,
                label_explanation=self.word_explanation_folder,
                list_widget=self.listWidget_folder,
                line_edit_word=self.lineEdit_folder,
                ok_btn=self.ok_btn_folder,
                stacked=self.stackedWidget_4,
                stacked_main=self.stackedWidget_2,
                theme=self.get_theme
            )

            self.study_words_folder.load_words(words, self.current_folder_module_id)

            self.stackedWidget_2.setCurrentIndex(self.stackedWidget_2.currentIndex() + 2)

    def test_words(self):
        if self.sender() == self.test_btn:
            words = self.db.get_words_for_module(self.current_module_id)

            self.test_words = TestWords(
                label_guess=self.word_label_guess,
                label_explanation=self.word_test_explanation,
                list_widget=self.listWidget_words_ans,
                line_edit_word=self.lineEdit_test_word,
                ok_btn=self.ok_btn_test,
                stacked=self.stackedWidget_9,
                stacked_main=self.stackedWidget,
                theme=self.get_theme,
                parent=self,
                db=self.db,
                updater=self.update_words_after_learn
            )

            self.test_words.load_words(words, self.current_module_id)
            self.stackedWidget.setCurrentIndex(4)

        else:
            words = self.db.get_words_for_module(self.current_folder_module_id)

            self.test_words_folder = TestWords(
                label_guess=self.label_guess_test_folder,
                label_explanation=self.label_explanation_test_folder,
                list_widget=self.listWidget_test_folder,
                line_edit_word=self.lineEdit,
                ok_btn=self.ok_btn_test_folder,
                stacked=self.stackedWidget_7,
                stacked_main=self.stackedWidget_2,
                theme=self.get_theme,
                parent=self,
                db=self.db,
                updater=self.update_words_after_learn
            )

            self.test_words_folder.load_words(words, self.current_folder_module_id)
            self.stackedWidget_2.setCurrentIndex(5)

    def update_words_after_learn(self):
        '''обновляет интерфейсы, кнопки и labelы'''

        if self.current_module_id is not None:
            # для слов в модулях
            self.textBrowser_topic.setText(self.db.get_topic(self.current_module_id))
            self.description_textBrowser.setPlainText(self.db.get_description(self.current_module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(self.current_module_id)
            self.words_amount_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_label.setText('Невыученных: ' + str(words_not_learned))

            self.db.add_data_to_words_statistics()

        if self.current_folder_module_id is not None:
            # для слов в папках
            self.textBrowser_topic_folder.setText(self.db.get_topic(self.current_folder_module_id))
            self.textBrowser_folder_description.setPlainText(self.db.get_description(self.current_folder_module_id))

            words_learned, words_not_learned = self.db.get_statistics_words_learned(self.current_folder_module_id)
            self.words_amount_folder_label.setText('Всего слов: ' + str(words_learned + words_not_learned))
            self.amount_learned_words_folder_label.setText('Выученных: ' + str(words_learned))
            self.amount_not_learned_words_folder_label.setText('Невыученных: ' + str(words_not_learned))

    def words_amount_module_clicked(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_words_in_module(self.current_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()

    def words_amount_learned_module_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    table.setStyleSheet("""
                        QTableWidget {
                            background-color: transparent;
                            alternate-background-color: transparent;
                            gridline-color: #2e7d32;
                            color: #1b5e20;
                            border: none;
                            selection-background-color: #c8e6c9;
                        }

                        QTableWidget::item {
                            background-color: #e8f5e9;
                            color: #1b5e20;
                            padding: 5px;
                        }

                        QHeaderView::section {
                            background-color: #4caf50;
                            color: white;
                            font-weight: bold;
                            padding: 5px;
                            border: 1px solid #2e7d32;
                        }
                        
                        QTableWidget::item:focus {
                            outline: none;
                        }
                    """)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_learned_words_in_module(self.current_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()

    def words_amount_not_learned_module_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    table.setStyleSheet("""
                        QTableWidget {
                            background-color: transparent;
                            alternate-background-color: transparent;
                            gridline-color: red;
                            color: red;
                            border: none;
                        }
                        
                        QTableWidget::item {
                            background-color: #ffdddd;
                            color: red;
                        }
                        
                        QHeaderView::section {
                            background-color: #ff9999;
                            color: white;
                            font-weight: bold;
                            border: 1px solid red;
                        }
                        
                        QScrollBar:vertical {
                            background: #ffeeee;
                            width: 12px;
                        }
                    """)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_not_learned_words_in_module(self.current_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()




    def words_amount_module_folder_clicked(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_words_in_module(self.current_folder_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()

    def words_amount_learned_module_folder_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    table.setStyleSheet("""
                                            QTableWidget {
                                                background-color: transparent;
                                                alternate-background-color: transparent;
                                                gridline-color: #2e7d32;
                                                color: #1b5e20;
                                                border: none;
                                                selection-background-color: #c8e6c9;
                                            }

                                            QTableWidget::item {
                                                background-color: #e8f5e9;
                                                color: #1b5e20;
                                                padding: 5px;
                                            }

                                            QHeaderView::section {
                                                background-color: #4caf50;
                                                color: white;
                                                font-weight: bold;
                                                padding: 5px;
                                                border: 1px solid #2e7d32;
                                            }

                                            QTableWidget::item:focus {
                                                outline: none;
                                            }
                                        """)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_learned_words_in_module(self.current_folder_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()

    def words_amount_not_learned_module_folder_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            class ShowAllWords(QDialog):
                def __init__(self, words, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle('Все слова')
                    self.words = words

                    self.make_table_widget()
                    self.resize(500, 500)

                def make_table_widget(self):
                    layout = QVBoxLayout()

                    table = QTableWidget()
                    table.setRowCount(len(self.words))
                    table.setColumnCount(2)
                    table.setHorizontalHeaderLabels(['Слово', 'Значение'])

                    for r, row in enumerate(self.words):
                        for c, val in enumerate(row[::-1]):
                            item = QTableWidgetItem(val)
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            table.setItem(r, c, item)

                    table.setSortingEnabled(True)
                    table.resizeColumnsToContents()
                    table.resizeRowsToContents()
                    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

                    header = table.horizontalHeader()
                    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

                    table.setStyleSheet("""
                                            QTableWidget {
                                                background-color: transparent;
                                                alternate-background-color: transparent;
                                                gridline-color: red;
                                                color: red;
                                                border: none;
                                            }

                                            QTableWidget::item {
                                                background-color: #ffdddd;
                                                color: red;
                                            }

                                            QHeaderView::section {
                                                background-color: #ff9999;
                                                color: white;
                                                font-weight: bold;
                                                border: 1px solid red;
                                            }

                                            QScrollBar:vertical {
                                                background: #ffeeee;
                                                width: 12px;
                                            }
                                        """)

                    layout.addWidget(table)

                    self.setLayout(layout)

            words = self.db.get_not_learned_words_in_module(self.current_folder_module_id)  # только для модулей

            sh = ShowAllWords(words=words, parent=self)
            sh.exec()


class HighlightCalendar(QCalendarWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.db = db
        self.events = list()

        self.all_dates = self.db.get_all_entry_dates()

        for date_str in self.all_dates:
            y, m, d = list(map(int, date_str[0].split('-')))
            date = QDate(y, m, d)
            if date not in self.events:
                self.events.append(date)

        self.clicked.connect(self.on_date_clicked)

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)

        if date in self.events:
            painter.save()
            painter.setRenderHint(painter.RenderHint.Antialiasing)

            painter.setBrush(QColor(144, 238, 144, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)

            painter.setPen(QColor("black"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(date.day()))

            painter.restore()

    def on_date_clicked(self, date):
        """Обработчик клика по дате"""
        if date in self.events:
            self.show_date_info(date)
        else:
            QMessageBox.information(self, "Информация",
                                    f"На {date.toString('dd.MM.yyyy')} нет записей")

    def show_date_info(self, date):
        """Показывает информацию о выбранной дате"""
        class Info(QDialog):
            def __init__(self, current_date, db, parent=None):
                super().__init__(parent)
                current_date = '-'.join(str(current_date.toString('yyyy.MM.dd')).split('.'))
                print(current_date)
                print(db.get_by_date_learned(current_date))
                info = db.get_by_date_learned(current_date)
                if info is None:
                    self.all_dates = (0, 0)
                else:
                    self.all_dates = info
                self.setWindowTitle(f"Информация за {date.toString('dd.MM.yyyy')}")
                self.setFixedSize(300, 200)

                layout = QVBoxLayout()
                text = f'''<span style="color: blue";>{date.toString('dd.MM.yyyy')}</span> вы выучили <span style="color: green";>{self.all_dates[0]}</span> слов, не смогли выучить <span style="color: red;">{self.all_dates[1]}</span>.'''
                label = QTextBrowser()
                label.setHtml(text)
                layout.addWidget(label)

                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(self.close)
                layout.addWidget(close_btn)

                self.setLayout(layout)

        d = Info(date, self.db, self.parent)
        d.exec()


def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу, работает для .exe и обычного запуска """
    try:
        # PyInstaller создает временную папку _MEIPASS
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.parent
    return str(base_path / relative_path)