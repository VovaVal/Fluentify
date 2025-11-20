import requests
import shutil
from pathlib import Path
import socket
import os
import random
import sys

from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QPushButton, QListWidget, QMessageBox, QMenu, QFileDialog, QSlider, QStackedWidget, QWidget, \
    QMainWindow, QHBoxLayout, QTabWidget
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox


class RadioTabHandler:
    def __init__(self, parent_window, db):
        self.window = parent_window
        self.db = db
        self.setup_radio_tab()

    def setup_radio_tab(self):
        radio_tab = self.window.radio_tab
        home_tab = self.window.main_tab
        words_tab = self.window.words_tab
        ai_tab = self.window.ai_tab

        tab_widget = self.window.tabWidget

        tab_index = tab_widget.indexOf(words_tab)  # находим индекс вкладки
        tab_widget.setTabIcon(tab_index, QIcon(resource_path("image/tab_images/word_tab_img.png")))

        tab_index = tab_widget.indexOf(home_tab)  # находим индекс вкладки
        tab_widget.setTabIcon(tab_index, QIcon(resource_path("image/tab_images/home_tab_img.png")))

        tab_index = tab_widget.indexOf(radio_tab)  # находим индекс вкладки
        tab_widget.setTabIcon(tab_index, QIcon(resource_path("image/tab_images/radio_tab_img.png")))

        tab_index = tab_widget.indexOf(ai_tab)  # находим индекс вкладки
        tab_widget.setTabIcon(tab_index, QIcon(resource_path("image/tab_images/ai_tab_img.png")))

        tab_widget.setIconSize(QtCore.QSize(30, 30))  # размер иконок

        self.radio_stacked = radio_tab.findChild(QStackedWidget, 'stackedWidget_radio')
        self.radio_player_page = self.radio_stacked.findChild(QWidget, "page_radio_listen")
        self.radio_list_page = self.radio_stacked.findChild(QWidget, "radio_page_list")

        # Создаём плеер
        self.radio_player = RadioPlayer(self.radio_stacked, self.radio_player_page)

        player_layout = self.radio_player_page.layout()
        if player_layout is None:
            player_layout = QVBoxLayout(self.radio_player_page)
        player_layout.addWidget(self.radio_player)


        self.radio_lineEdit = radio_tab.findChild(QLineEdit, 'radio_lineEdit')
        self.radio_lineEdit.textChanged.connect(self.search_radios)

        self.add_radio_btn = radio_tab.findChild(QPushButton, 'add_radio_btn')
        self.add_radio_btn.clicked.connect(self.add_radio)

        self.delete_radio_btn = radio_tab.findChild(QPushButton, 'delete_radio_btn')
        self.delete_radio_btn.clicked.connect(self.delete_radios)

        self.radio_lineEdit = radio_tab.findChild(QLineEdit, 'radio_lineEdit')
        self.radio_listWidget = radio_tab.findChild(QListWidget, 'radio_listWidget')
        self.radio_listWidget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.radio_listWidget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.radio_listWidget.setSpacing(2)
        self.radio_listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.radio_listWidget.customContextMenuRequested.connect(self.show_radio_context_menu)
        self.radio_listWidget.itemClicked.connect(self.open_radio_player)

        self.upload_words()

    def open_radio_player(self, item):
        try:
            socket.gethostbyaddr('www.yandex.ru')
        except socket.gaierror:
            QMessageBox.warning(self.window, 'Ошибка', 'У вас отстутсвует доступ в сеть.')
            return

        radio_id = item.data(100)
        url = self.db.get_radio_url(radio_id)[0]
        img_path = self.db.get_image_path(radio_id)[0]
        if not url:
            QMessageBox.warning(self.window, "Ошибка", "Нет ссылки на поток.")
            return

        if img_path is None:
            img_path = 'image/default_radio_img.jpg'
        else:
            img_path = 'data/' + img_path

        self.radio_player.load_url(url, img_path)
        self.radio_stacked.setCurrentWidget(self.radio_player_page)

    def show_radio_context_menu(self, position):
        item = self.radio_listWidget.itemAt(position)

        if item is None:
            return

        context_menu = QMenu(self.window)

        action1 = QAction('Переименовать', self.window)
        action2 = QAction('Удалить', self.window)
        action3 = QAction('Создать', self.window)

        context_menu.addAction(action1)
        context_menu.addAction(action2)
        context_menu.addAction(action3)

        selected = context_menu.exec(self.radio_listWidget.mapToGlobal(position))
        if selected == action1:
            self.rename_radios(item)
        elif selected == action2:
            self.delete_radio(item)
        elif selected == action3:
            self.add_radio()

    def search_radios(self):
        query = self.radio_lineEdit.text()
        radios = self.db.get_all_searched_radios(query)
        self.show_radios(radios)

    def show_radios(self, radios):
        self.radio_listWidget.clear()

        for radio_id, name in radios:
            self.radio_listWidget.addItem(name)
            item = self.radio_listWidget.item(self.radio_listWidget.count() - 1)
            item.setData(100, radio_id)

    def add_radio(self):
        dialog = AddRadioDialog(self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, url, img_path = dialog.get_inputs()
            if name and url:
                try:
                    if not self.is_stream_url_valid(url):
                        QMessageBox.information(self.window, 'Ошибка', 'Ссылка недействительна.')
                        return

                    radio_id = self.db.add_radio_station(name, url)

                    # Сохраняем изображение
                    if img_path and img_path != "Изображения нет":
                        saved_path = self.save_radio_image(img_path, radio_id)
                        self.db.add_image_radio(radio_id, saved_path)
                    else:
                        self.db.add_image_radio(radio_id, None)  # NULL в БД

                    self.upload_words()
                except ValueError as e:
                    QMessageBox.warning(self.window, "Ошибка", str(e))
            else:
                QMessageBox.warning(self.window, "Ошибка", "Название и ссылка не могут быть пустыми")

    def delete_radio(self, item):
        id_radio = item.data(100)
        name = item.text()

        reply = QMessageBox.question(self.window, 'Подтверждение', f'Вы уверены, что хотите удалить модуль {name}?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_radio_image(id_radio)
            self.db.delete_radio_station(id_radio)

            row = self.radio_listWidget.row(item)
            self.radio_listWidget.takeItem(row)

            self.search_radios()

        else:
            pass

    def rename_radios(self, item):
        id_radio = item.data(100)
        name = item.text()
        url = self.db.get_radio_url(id_radio)[0]
        current_img_path = self.db.get_image_path(id_radio)[0]

        dialog = RenameRadioDialog(name, url, current_img_path, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, url, action, img_path = dialog.get_inputs()
            if name and url:
                try:
                    if not self.is_stream_url_valid(url):
                        QMessageBox.information(self.window, 'Ошибка', 'Ссылка недействительна.')
                        return

                    self.db.update_radio_station(id_radio, name, url)

                    # Работаем с изображением ТОЛЬКО при изменении
                    if action == "delete":
                        self.delete_radio_image(id_radio)
                        self.db.add_image_radio(id_radio, None)
                    elif action == "new":
                        saved_path = self.save_radio_image(img_path, id_radio)
                        self.db.add_image_radio(id_radio, saved_path)

                    item.setText(name)

                except ValueError as e:
                    QMessageBox.warning(self.window, "Ошибка", str(e))
            else:
                QMessageBox.warning(self.window, "Ошибка", "Название и ссылка не могут быть пустыми")

    def delete_radios(self):
        radios = self.db.get_all_radio_names()
        if not radios:
            QMessageBox.information(self.window, "Информация", "Нет радиостанций для удаления.")
            return

        dialog = DeleteRadioDialog(radios, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_ids = dialog.get_selected_radio_ids()
            if selected_ids:
                for station_id in selected_ids:
                    self.delete_radio_image(station_id)
                    self.db.delete_radio_station(station_id)
                self.upload_words()
                QMessageBox.information(self.window, "Успех", "Радиостанции успешно удалены.")

    def upload_words(self):
        self.radio_listWidget.clear()
        for station_id, name, url in self.db.get_all_radio_stations():
            item = self.radio_listWidget.addItem(name)
            self.radio_listWidget.item(self.radio_listWidget.count() - 1).setData(100, station_id)

    def save_radio_image(self, source_path: str, radio_id: int) -> str:
        if not source_path or source_path == "Изображения нет":
            return None

        if source_path.startswith("radio_img/"):
            return source_path

        img_dir = Path(__file__).parent.parent / "data" / "radio_img"
        img_dir.mkdir(parents=True, exist_ok=True)

        # Проверяем: существует ли файл по указанному пути
        source_file = Path(source_path)
        if not source_file.is_file():
            print(f"Файл не найден: {source_path}")
            return None

        ext = source_file.suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
            ext = ".png"

        dest_name = f"radio_{radio_id}{ext}"
        dest_path = img_dir / dest_name

        shutil.copy2(source_file, dest_path)
        return f"radio_img/{dest_name}"

    def delete_radio_image(self, radio_id: int):
        """Удаляет файл изображения радиостанции с диска"""
        image_path = self.db.get_image_path(radio_id)
        if image_path and image_path[0]:
            full_path = Path(__file__).parent.parent / "data" / image_path[0]
            if full_path.exists():
                try:
                    full_path.unlink()
                    print(f"Изображение удалено: {full_path}")
                except OSError as e:
                    print(f"Ошибка при удалении: {e}")

    def is_stream_url_valid(self, url: str, timeout: int = 100) -> bool:
        """
        Проверяет, доступен ли аудиопоток по URL.
        Возвращает True, если статус 200, иначе False.
        """
        try:
            response = requests.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


class AddRadioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        QMessageBox.information(
            self,
            "Информация",
            "Для того, чтобы работало радио, надо ссылку такого типа:<br>"
            "<i>https://stream.energy.ru/energy.mp3</i><br><br>"
            "Без такой ссылки радио не будет работать."
        )

        self.setWindowTitle("Добавить радиостанцию")
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)
        self.resize(600, 300)

        self.has_img = False

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Ссылка на поток:"))
        self.url_edit = QLineEdit()
        layout.addWidget(self.url_edit)

        self.img_label_text = QLabel('Изображения нет')
        self.img_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_label_text)

        self.delete_img_btn = QPushButton('Удалить изображение')
        layout.addWidget(self.delete_img_btn)
        self.delete_img_btn.hide()
        self.delete_img_btn.clicked.connect(self.delete_img_clicked)

        self.add_img_btn = QPushButton('Добавить изображение')
        layout.addWidget(self.add_img_btn)
        self.add_img_btn.clicked.connect(self.add_img)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def add_img(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Выбрать изображение', '',
                                            'PNG (*.png);; IMG (*.img);; JPG (*.jpg);;'
                                            ' JPEG (*.jpeg);; BMP (*.bmp);; GIF (*.gif)')
        self.img_label_text.setText(fname)
        self.delete_img_btn.show()

    def delete_img_clicked(self):
        self.img_label_text.setText('Изображения нет')
        self.delete_img_btn.hide()

    def get_inputs(self):
        return self.name_edit.text().strip(), self.url_edit.text().strip(), self.img_label_text.text().strip()


class DeleteRadioDialog(QDialog):
    def __init__(self, available_radio, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление радиостанций")
        self.resize(400, 300)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Выберите радисотанции для удаления:"))

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for radio_id, name in available_radio:
            item = self.list_widget.addItem(name)
            self.list_widget.item(self.list_widget.count() - 1).setData(100, radio_id)

        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_selected_radio_ids(self):
        """Возвращает список ID выбранных модулей"""
        selected_items = self.list_widget.selectedItems()
        return [item.data(100) for item in selected_items]


class RenameRadioDialog(QDialog):
    def __init__(self, radio_name: str, url: str, img: str, parent=None):
        super().__init__(parent)
        QMessageBox.information(
            self,
            "Информация",
            "Для того, чтобы работало радио, надо ссылку такого типа:<br>"
            "<i>https://stream.energy.ru/energy.mp3</i><br><br>"
            "Без такой ссылки радио не будет работать."
        )

        self.setWindowTitle("Добавить радиостанцию")
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)
        self.resize(600, 300)

        self.has_img = False

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit(radio_name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Ссылка на поток:"))
        self.url_edit = QLineEdit(url)
        layout.addWidget(self.url_edit)

        if img is None:
            self.img_label_text = QLabel('Изображения нет')

        else:
            self.has_img = True
            self.img_label_text = QLabel(img)

        self.img_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_label_text)

        self.delete_img_btn = QPushButton('Удалить изображение')
        layout.addWidget(self.delete_img_btn)
        if not self.has_img:
            self.delete_img_btn.hide()
        self.delete_img_btn.clicked.connect(self.delete_img_clicked)

        self.add_img_btn = QPushButton('Добавить изображение')
        layout.addWidget(self.add_img_btn)
        self.add_img_btn.clicked.connect(self.add_img)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.original_img_path = img
        self.image_action = "keep"  # "keep", "new", "delete"

    def add_img(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Выбрать изображение', '',
                                                       'PNG (*.png);; IMG (*.img);; JPG (*.jpg);;'
                                                       ' JPEG (*.jpeg);; BMP (*.bmp);; GIF (*.gif)')
        if fname:
            self.img_label_text.setText(fname)
            self.delete_img_btn.show()
            self.image_action = "new"

    def delete_img_clicked(self):
        self.img_label_text.setText('Изображения нет')
        self.delete_img_btn.hide()
        self.image_action = "delete"

    def get_inputs(self):
        name = self.name_edit.text().strip()
        url = self.url_edit.text().strip()
        # Возвращаем действие, а не путь
        return name, url, self.image_action, self.img_label_text.text().strip()


class RadioPlayer(QWidget):
    def __init__(self, radio_stack, parent_window: None):
        super().__init__(parent_window)
        self.resize(400, 200)
        self.radio_stack = radio_stack

        vbox = QVBoxLayout()

        # Создаём аудиовыход
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.5)

        self.back_radio_btn = QPushButton('Назад')
        self.back_radio_btn.clicked.connect(self.back_btn_clicked)
        hb = QHBoxLayout()
        hb.addWidget(self.back_radio_btn)
        hb.addStretch()

        vbox.addLayout(hb)

        # Ползунок громкости
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.change_volume)

        # Метка громкости
        self.volume_label = QLabel()
        self.volume_label.setText('Громкость: 70%')

        hb = QHBoxLayout()
        hb.addWidget(self.volume_slider)
        hb.addWidget(self.volume_label)

        vbox.addLayout(hb)

        self.img_label = ScalableImageLabel()
        vbox.addWidget(self.img_label)

        self.equalizer = FakeEqualizer()
        vbox.addWidget(self.equalizer)

        # Создаём плеер
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        # Кнопка воспроизведения
        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon(resource_path('image/play_radio_icon.png')))
        self.play_btn.setIconSize(QtCore.QSize(100, 100))
        self.play_btn.clicked.connect(self.toggle_play)

        self.play_btn.setFlat(True)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                background: transparent;
            }
            QPushButton:pressed {
                background: transparent;
            }
        """)
        vbox.addWidget(self.play_btn)

        self.setLayout(vbox)

    def back_btn_clicked(self):
        self.player.pause()
        self.play_btn.setIcon(QIcon(resource_path('image/play_radio_icon.png')))
        self.play_btn.setIconSize(QtCore.QSize(100, 100))
        self.radio_stack.setCurrentIndex(0)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setIcon(QIcon(resource_path('image/play_radio_icon.png')))
            self.play_btn.setIconSize(QtCore.QSize(100, 100))
        else:
            self.player.play()
            self.play_btn.setIcon(QIcon(resource_path('image/pause_radio_icon.png')))
            self.play_btn.setIconSize(QtCore.QSize(100, 100))

    def load_url(self, url, img_path):
        self.radio_url = url
        self.player.setSource(QUrl(self.radio_url))
        pixmap = QPixmap(resource_path(img_path))
        self.img_label.setScalablePixmap(pixmap)

    def change_volume(self, value):
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        self.volume_label.setText(f"Громкость: {value}%")


class ScalableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(1, 1)

    def setScalablePixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self._scale_pixmap()
        self.update()

    def _scale_pixmap(self):
        if self._pixmap.isNull():
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_pixmap()


class FakeEqualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = [0] * 20
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_bars)
        self.timer.start(80)
        self.setMinimumSize(300, 80)

    def update_bars(self):
        h = max(10, self.height() - 10)
        self.bars = [random.randint(5, h) for _ in self.bars]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        n = len(self.bars)
        if n == 0:
            return
        bar_width = self.width() / n
        for i, height in enumerate(self.bars):
            x = int(i * bar_width + bar_width / 2)
            painter.setPen(QPen(QColor("#4CAF50"), 3))
            painter.drawLine(x, self.height(), x, self.height() - height)

    def stop(self):
        self.timer.stop()



def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу"""
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent.parent
    return str(base_path / relative_path)