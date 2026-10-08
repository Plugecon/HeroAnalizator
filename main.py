import sys
import os
import datetime
import ctypes
import subprocess
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView,
    QMessageBox, QStatusBar, QMenu, QDialog, QFormLayout, QLineEdit,
    QComboBox, QTimeEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QColor, QAction

def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    """Запрос UAC-прав и перезапуск скрипта"""
    try:
        script = sys.argv[0]
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    except Exception as e:
        print(f"Ошибка повышения прав: {e}")


class TaskScannerThread(QThread):
    """Фоновый поток для сканирования планировщика задач"""
    finished = pyqtSignal(dict)

    def run(self):
        tasks_path = os.path.expandvars(r"%WINDIR%\System32\Tasks")
        now = datetime.datetime.now()
        
        categories = {
            "🔴 Менее 24 часов (Свежие - зона риска!)": [],
            "🟠 От 1 дня до 1 месяца": [],
            "🟡 От 1 месяца до 6 месяцев": [],
            "🟢 От 6 месяцев до 1 года": [],
            "🔵 Более 1 года назад": []
        }

        if not os.path.exists(tasks_path):
            self.finished.emit(categories)
            return

        for root, dirs, files in os.walk(tasks_path):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    creation_time = datetime.datetime.fromtimestamp(os.path.getctime(full_path))
                    age_days = (now - creation_time).days
                    action_command = self.get_task_action(full_path)

                    task_info = {
                        "name": file,
                        "path": full_path,
                        "created": creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "action": action_command
                    }

                    if age_days < 1:
                        categories["🔴 Менее 24 часов (Свежие - зона риска!)"].append(task_info)
                    elif age_days < 30:
                        categories["🟠 От 1 дня до 1 месяца"].append(task_info)
                    elif age_days < 180:
                        categories["🟡 От 1 месяца до 6 месяцев"].append(task_info)
                    elif age_days < 365:
                        categories["🟢 От 6 месяцев до 1 года"].append(task_info)
                    else:
                        categories["🔵 Более 1 года назад"].append(task_info)
                except Exception:
                    continue

        self.finished.emit(categories)

    def get_task_action(self, xml_file):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            
            exec_elem = root.find('.//Exec')
            if exec_elem is not None:
                cmd = exec_elem.find('Command')
                args = exec_elem.find('Arguments')
                cmd_text = cmd.text if cmd is not None and cmd.text else ""
                args_text = args.text if args is not None and args.text else ""
                full_cmd = f"{cmd_text} {args_text}".strip()
                if full_cmd:
                    return full_cmd

            com_elem = root.find('.//ComHandler')
            if com_elem is not None:
                class_id = com_elem.find('ClassId')
                if class_id is not None and class_id.text:
                    return f"[COM Object] {class_id.text}"
        except Exception:
            return "Ошибка чтения XML"
        return "Не удалось определить"


class CreateTaskDialog(QDialog):
    """Окно создания или редактирования задачи в Планировщике"""
    def __init__(self, parent=None, edit_mode=False, task_name="", xml_path=""):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.initial_name = task_name
        self.xml_path = xml_path
        
        self.setWindowTitle("Редактировать задачу" if self.edit_mode else "Создать новую задачу")
        self.resize(500, 320)
        self.init_ui()

        if self.edit_mode and self.xml_path:
            self.load_task_data()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QTimeEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3f3f46;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        if self.edit_mode:
            self.name_input.setReadOnly(True) # Имя существующей задачи менять нельзя (используется как ID)
            self.name_input.setStyleSheet("background-color: #2d2d30; color: #888888;")
        form_layout.addRow("Имя задачи:", self.name_input)

        # Путь к файлу + кнопка обзора
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        browse_btn = QPushButton("📂 Обзор")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        form_layout.addRow("Путь к файлу / Команда:", path_layout)

        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("Например: --silent или /update (необязательно)")
        form_layout.addRow("Аргументы запуска:", self.args_input)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(["При запуске системы (ONSTART)", "При входе пользователя (ONLOGON)", "Ежедневно (DAILY)"])
        self.trigger_combo.currentIndexChanged.connect(self.on_trigger_changed)
        form_layout.addRow("Триггер запуска:", self.trigger_combo)

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit_label = QLabel("Время запуска:")
        form_layout.addRow(self.time_edit_label, self.time_edit)
        
        self.time_edit.setVisible(False)
        self.time_edit_label.setVisible(False)

        layout.addLayout(form_layout)

        # Кнопки сохранения / отмены
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("💾 Сохранить задачу" if self.edit_mode else "✅ Создать задачу")
        save_btn.clicked.connect(self.save_task)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("❌ Отмена")
        cancel_btn.setStyleSheet("background-color: #3f3f46;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите исполняемый файл", "C:\\", "Executables (*.exe);;All Files (*.*)")
        if file_path:
            self.path_input.setText(file_path)

    def on_trigger_changed(self, index):
        is_daily = (index == 2)
        self.time_edit.setVisible(is_daily)
        self.time_edit_label.setVisible(is_daily)

    def load_task_data(self):
        """Загрузка данных существующей задачи из XML для редактирования"""
        try:
            self.name_input.setText(self.initial_name)
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            # Извлекаем команду и аргументы
            exec_elem = root.find('.//Exec')
            if exec_elem is not None:
                cmd = exec_elem.find('Command')
                args = exec_elem.find('Arguments')
                if cmd is not None and cmd.text:
                    self.path_input.setText(cmd.text)
                if args is not None and args.text:
                    self.args_input.setText(args.text)

            # Пытаемся определить триггер
            if root.find('.//BootTrigger') is not None:
                self.trigger_combo.setCurrentIndex(0)
            elif root.find('.//LogonTrigger') is not None:
                self.trigger_combo.setCurrentIndex(1)
            elif root.find('.//CalendarTrigger') is not None:
                self.trigger_combo.setCurrentIndex(2)
                # Попробуем вытащить время
                time_elem = root.find('.//StartBoundary')
                if time_elem is not None and time_elem.text:
                    try:
                        # Время в XML обычно формата YYYY-MM-DDTHH:MM:SS
                        t_part = time_elem.text.split('T')[1][:5]
                        self.time_edit.setTime(QTime.fromString(t_part, "HH:mm"))
                    except:
                        pass
        except Exception as e:
            print(f"Ошибка при разборе XML для редактирования: {e}")

    def save_task(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        args = self.args_input.text().strip()
        trigger_idx = self.trigger_combo.currentIndex()

        if not name or not path:
            QMessageBox.warning(self, "Ошибка", "Имя задачи и путь к файлу обязательны для заполнения!")
            return

        full_tr = f'"{path}"'
        if args:
            full_tr += f' {args}'

        # Флаг /F перезапишет существующую задачу с тем же именем
        cmd = ["schtasks", "/Create", "/TN", name, "/TR", full_tr, "/F"]

        if trigger_idx == 0:
            cmd.extend(["/SC", "ONSTART"])
        elif trigger_idx == 1:
            cmd.extend(["/SC", "ONLOGON"])
        elif trigger_idx == 2:
            time_str = self.time_edit.time().toString("HH:mm")
            cmd.extend(["/SC", "DAILY", "/ST", time_str])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                action_text = "обновлена" if self.edit_mode else "создана"
                QMessageBox.information(self, "Успех", f"Задача '{name}' успешно {action_text}!")
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка Windows", f"Не удалось сохранить задачу:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {e}")


class HeroAnalizatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HeroAnalizator — Windows Security & Forensics")
        self.resize(1050, 650)
        self.init_ui()
        self.start_scanning()

    def init_ui(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 13px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0098ff;
            }
            QTreeWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3f3f46;
                border-radius: 4px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #3f3f46;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        title_label = QLabel("🛡️ Анализатор Планировщика Задач Windows")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()

        self.create_btn = QPushButton("➕ Создать задачу")
        self.create_btn.setStyleSheet("background-color: #28a745;")
        self.create_btn.clicked.connect(self.open_create_dialog)
        top_layout.addWidget(self.create_btn)

        self.refresh_btn = QPushButton("🔄 Пересканировать")
        self.refresh_btn.clicked.connect(self.start_scanning)
        top_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(top_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя задачи / Категория", "Время создания", "Запускаемый файл / Команда"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tree)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе. Права администратора активны.")

    def open_create_dialog(self):
        dialog = CreateTaskDialog(self, edit_mode=False)
        if dialog.exec():
            self.start_scanning()

    def open_edit_dialog(self, item):
        task_name = item.text(0)
        xml_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not xml_path or not os.path.exists(xml_path):
            QMessageBox.warning(self, "Ошибка", "Не удалось найти XML-файл для этой задачи.")
            return

        dialog = CreateTaskDialog(self, edit_mode=True, task_name=task_name, xml_path=xml_path)
        if dialog.exec():
            self.start_scanning()

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item or not item.parent(): 
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3f3f46;
            }
            QMenu::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)

        edit_action = QAction("✏️ Редактировать задачу", self)
        copy_name_action = QAction("📋 Копировать имя задачи", self)
        copy_cmd_action = QAction("📋 Копировать команду", self)
        delete_action = QAction("🗑️ Удалить задачу", self)

        edit_action.triggered.connect(lambda: self.open_edit_dialog(item))
        copy_name_action.triggered.connect(lambda: QApplication.clipboard().setText(item.text(0)))
        copy_cmd_action.triggered.connect(lambda: QApplication.clipboard().setText(item.text(2)))
        delete_action.triggered.connect(lambda: self.delete_task(item))

        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(copy_name_action)
        menu.addAction(copy_cmd_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def delete_task(self, item):
        task_name = item.text(0)
        confirm = QMessageBox.question(
            self, 
            "Подтверждение удаления", 
            f"Вы уверены, что хотите удалить задачу '{task_name}'?\nЭто действие необратимо!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                result = subprocess.run(
                    ["schtasks", "/Delete", "/TN", task_name, "/F"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Успех", f"Задача '{task_name}' успешно удалена!")
                    self.start_scanning()
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить задачу:\n{result.stderr}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {e}")

    def start_scanning(self):
        self.tree.clear()
        self.status_bar.showMessage("⏳ Сканирование планировщика задач...")
        self.refresh_btn.setEnabled(False)
        self.create_btn.setEnabled(False)

        self.scanner_thread = TaskScannerThread()
        self.scanner_thread.finished.connect(self.display_results)
        self.scanner_thread.start()

    def display_results(self, categories):
        total_tasks = 0
        for category_name, tasks in categories.items():
            total_tasks += len(tasks)
            cat_item = QTreeWidgetItem(self.tree, [f"{category_name} (Найдено: {len(tasks)})"])
            cat_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            if "Менее 24 часов" in category_name and len(tasks) > 0:
                cat_item.setForeground(0, QColor("#ff6b6b"))

            for t in tasks:
                task_item = QTreeWidgetItem(cat_item, [t["name"], t["created"], t["action"]])
                # Сохраняем путь к XML файлу задачи для редактирования
                task_item.setData(0, Qt.ItemDataRole.UserRole, t["path"])
                
        self.tree.expandAll()
        self.refresh_btn.setEnabled(True)
        self.create_btn.setEnabled(True)
        self.status_bar.showMessage(f"✅ Сканирование завершено. Всего проанализировано задач: {total_tasks}")


if __name__ == "__main__":
    if not is_admin():
        print("[!] Нет прав администратора. Запрос повышения привилегий...")
        elevate_privileges()
        sys.exit()

    app = QApplication(sys.argv)
    window = HeroAnalizatorWindow()
    window.show()
    sys.exit(app.exec())
