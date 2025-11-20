from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox, QScrollArea, QWidget, QListWidget, QTextBrowser, QComboBox,
    QFileDialog
)
from PyQt6.QtCore import Qt

import csv


class AddModulesToFolderDialog(QDialog):
    def __init__(self, available_modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить модули в папку")
        self.resize(400, 300)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите модули для добавления:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.list_widget.setSpacing(2)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for module_id, name in available_modules:
            item = self.list_widget.addItem(name)
            self.list_widget.item(self.list_widget.count() - 1).setData(100, module_id)

        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_module_ids(self):
        """Возвращает список ID выбранных модулей"""
        selected_items = self.list_widget.selectedItems()
        return [item.data(100) for item in selected_items]


class DeleteModulesDialog(QDialog):
    def __init__(self, available_modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление модулей")
        self.resize(400, 300)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите модули для удаления:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.list_widget.setSpacing(2)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for module_id, name in available_modules:
            item = self.list_widget.addItem(name)
            self.list_widget.item(self.list_widget.count() - 1).setData(100, module_id)

        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_module_ids(self):
        """Возвращает список ID выбранных модулей"""
        selected_items = self.list_widget.selectedItems()
        return [item.data(100) for item in selected_items]


class DeleteFoldersDialog(QDialog):
    def __init__(self, available_modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление папок.")
        self.resize(400, 300)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите папки для удаления:"))

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for folder_id, name in available_modules:
            item = self.list_widget.addItem(name)
            self.list_widget.item(self.list_widget.count() - 1).setData(100, folder_id)

        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_module_ids(self):
        """Возвращает список ID выбранных модулей"""
        selected_items = self.list_widget.selectedItems()
        return [item.data(100) for item in selected_items]


class AddWordsDialog(QDialog):
    def __init__(self, module_id, db, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.db = db
        self.setWindowTitle("Добавление слов")
        self.resize(700, 700)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        main_layout = QVBoxLayout()

        header_layout = QVBoxLayout()
        header_layout.addWidget(QLabel("<h3>Добавление слов в модуль.</h3>"))

        topic_label = QLabel('Тематика модуля:')
        self.topic_box = QComboBox()
        self.topic_box.setEditable(True)
        self.topic_box.addItems(['Английский', 'Немецкий', 'Русский', 'Французский',
                                 'История', 'Математика', 'Биология', 'Иное'])
        self.topic_box.setCurrentText('')

        header_layout.addWidget(topic_label)
        header_layout.addWidget(self.topic_box)

        description_label = QLabel('Описание модуля:')
        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(False)
        self.text_browser.setFixedHeight(100)
        self.text_browser.setPlaceholderText('Добавьте описание модуля.')
        header_layout.addWidget(description_label)
        header_layout.addWidget(self.text_browser)
        main_layout.addLayout(header_layout)

        # Создаём прокручиваемую область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.fields_layout = QVBoxLayout(self.scroll_content)
        self.fields_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)

        self.field_pairs = []

        # Добавляем первую пару
        self.add_word_pair()

        main_layout.addWidget(self.scroll_area)

        # Кнопка "+"
        self.add_pair_btn = QPushButton("+ Добавить ещё слово")
        self.add_pair_btn.clicked.connect(self.add_word_pair)
        main_layout.addWidget(self.add_pair_btn)

        self.add_file_btn = QPushButton('+ Добавить слова файлом')
        self.add_file_btn.clicked.connect(self.add_word_file)
        main_layout.addWidget(self.add_file_btn)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

    def add_word_pair(self):
        pair_layout = QHBoxLayout()

        native_edit = QLineEdit()
        native_edit.setPlaceholderText('Впишите слово')
        trans_edit = QLineEdit()
        trans_edit.setPlaceholderText('Впишите перевод или определение данного слова')

        pair_layout.addWidget(native_edit)
        pair_layout.addWidget(trans_edit)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(30, 30)
        remove_btn.clicked.connect(lambda ch, pl=pair_layout: self.remove_word_pair(pl))
        pair_layout.addWidget(remove_btn)

        self.fields_layout.addLayout(pair_layout)
        self.field_pairs.append((native_edit, trans_edit))

        native_edit.setFocus()

    def add_word_file(self):
        message = QMessageBox()
        message.information(self, 'Информация', 'ВНИМАНИЕ!!!\nСлова в файлах должны иметь такую структуру:\n'
                                          'Термин : Его значение или перевод.\n\n В .txt фалах слова должны быть'
                                          ' разделены одним из символов: ";",  ",",  ":" или табуляцией.')

        try:
            fname = QFileDialog.getOpenFileName(self, 'Выбрать файл', '', 'CSV (*.csv);;TXT (*.txt)')[0]
            # получаем файл со словами

            if not fname:
                return

            with open(fname, encoding='utf-8') as file:  # читаем файл
                if fname.endswith('.csv'):
                    sniffer = csv.Sniffer()  # метод, который ищет разделитель в .csv файлах
                    delimiter = sniffer.sniff(file.read(3000)).delimiter  # находим разделитель
                    file.seek(0)  # возвращаемся в начало .csv файла
                    data = csv.reader(file, delimiter=delimiter)

                    word_pairs = []
                    for row in data:
                        if len(row) >= 2:
                            word_pairs.append((row[0].strip(), row[1].strip()))
                            native = row[0].strip()
                            foreign = row[1].strip()
                            self.add_word_pair_file(native, foreign)

                else:
                    word_pairs = []  # пара слов
                    for line in file.readlines():  # читаем посторочно строки со словами
                        if '\t' in line:
                            parts = line.split('\t', 1)

                        elif ';' in line:
                            parts = line.split(';', 1)

                        elif ':' in line:
                            parts = line.split(':', 1)

                        elif ',' in line:
                            parts = line.split(',', 1)

                        if len(parts) < 2:  # если менее двух слов
                            continue

                        native = parts[0].strip()  # термин
                        foreign = parts[1].strip()  # значение термина или его перевод

                        if native and foreign:
                            word_pairs.append((native, foreign))
                            self.add_word_pair_file(native, foreign)

        except Exception:  # при ошибке оповещаем пользователя о ней
            error = QMessageBox(self)
            error.setWindowTitle('Ошибка')
            error.setText('При чтении файла произошла ошибка. Помните, слова в .txt файлах должны быть разделены'
                          ' одним из символов: ";", ",", ":", "\\tab".')
            error.exec()

    def add_word_pair_file(self, native, foreign):
        '''добавляет слова после того как мы получили их из файлов или когда мы редактируем слова'''
        pair_layout = QHBoxLayout()

        native_edit = QLineEdit(native)
        trans_edit = QLineEdit(foreign)

        pair_layout.addWidget(native_edit)
        pair_layout.addWidget(trans_edit)

        remove_btn = QPushButton("x")
        remove_btn.setFixedSize(30, 30)
        remove_btn.clicked.connect(lambda ch, pl=pair_layout: self.remove_word_pair(pl))
        pair_layout.addWidget(remove_btn)

        self.fields_layout.addLayout(pair_layout)
        self.field_pairs.append((native_edit, trans_edit))

    def remove_word_pair(self, layout_to_remove):
        if len(self.field_pairs) <= 1:
            return

        # Находим индекс
        index = -1
        for i in range(self.fields_layout.count()):
            item = self.fields_layout.itemAt(i)
            if item and item.layout() is layout_to_remove:
                index = i
                break

        if index == -1:
            return  # не найден

        # Удаляем из списка данных
        self.field_pairs.pop(index)

        # Удаляем все виджеты в layout'е
        while layout_to_remove.count():
            child = layout_to_remove.takeAt(0)
            if child.widget():
                child.widget().setParent(None)  # ← ключевое: отсоединяем от родителя

        # Удаляем layout из родительского layout'а
        self.fields_layout.removeItem(layout_to_remove)

        # Принудительно обновляем
        self.scroll_content.update()
        self.scroll_area.update()
        self.scroll_area.repaint()

    def get_valid_word_pairs(self):
        pairs = []
        for native_edit, trans_edit in self.field_pairs:
            native = native_edit.text().strip()
            trans = trans_edit.text().strip()
            if native and trans:
                pairs.append((native, trans))
        return pairs

    def accept(self):
        pairs = self.get_valid_word_pairs()
        if not pairs:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну пару слов.")
            return

        try:
            self.db.delete_words_from_module(self.module_id)

            for native, trans in pairs:
                self.db.add_word(native, trans, self.module_id)
            self.db.set_description(self.module_id, self.text_browser.toPlainText())
            self.db.set_topic(self.module_id, self.topic_box.currentText())
            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить слова:\n{e}")

    def set_description(self, text: str):
        self.text_browser.setText(text)

    def set_topic(self, topic: str):
        self.topic_box.setEditText(topic)

    def del_line(self):
        if len(self.field_pairs) <= 1:
            return

        first_item = self.fields_layout.itemAt(0)
        if not first_item or not first_item.layout():
            return

        layout_to_remove = first_item.layout()

        # Удаляем из данных
        self.field_pairs.pop(0)

        # Удаляем виджеты
        while layout_to_remove.count():
            child = layout_to_remove.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        # Удаляем layout
        self.fields_layout.removeItem(layout_to_remove)

        # Обновляем
        self.scroll_content.update()
        self.scroll_area.update()
        self.scroll_area.repaint()