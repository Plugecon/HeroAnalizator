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

# Словарь локализации интерфейса (добавлен русский язык)
TRANSLATIONS = {
    "en": {
        "window_title": "HeroAnalizator — Windows Security & Forensics",
        "scanner_title": "Windows Task Scheduler Auditor",
        "create_task": "Create Task",
        "refresh": "Rescan",
        "headers": ["Task Name / Category", "Creation Time", "Executable / Command"],
        "status_ready": "Ready. Administrator privileges active.",
        "status_scanning": "Scanning task scheduler...",
        "status_done": "Scan complete. Total tasks analyzed: ",
        "cat_fresh": "Less than 24 hours (Fresh - Risk Zone!)",
        "cat_1_month": "1 day to 1 month",
        "cat_6_months": "1 month to 6 months",
        "cat_1_year": "6 months to 1 year",
        "cat_old": "More than 1 year ago",
        "menu_edit": "Edit Task",
        "menu_copy_name": "Copy Task Name",
        "menu_copy_cmd": "Copy Command",
        "menu_delete": "Delete Task",
        "dialog_create_title": "Create New Task",
        "dialog_edit_title": "Edit Task",
        "label_name": "Task Name:",
        "label_path": "Executable Path:",
        "label_args": "Arguments:",
        "label_trigger": "Trigger:",
        "label_time": "Execution Time:",
        "btn_browse": "Browse",
        "btn_save": "Save Task",
        "btn_create": "Create Task",
        "btn_cancel": "Cancel",
        "triggers": ["On System Start (ONSTART)", "On User Logon (ONLOGON)", "Daily (DAILY)"],
        "msg_error": "Error",
        "msg_warning_fields": "Task name and file path are required!",
        "msg_success_create": "Task successfully created!",
        "msg_success_update": "Task successfully updated!",
        "msg_success_delete": "Task successfully deleted!",
        "msg_delete_confirm": "Are you sure you want to delete task",
        "xml_error": "Could not find XML file for this task."
    },
    "ru": {
        "window_title": "HeroAnalizator — Безопасность и форензика Windows",
        "scanner_title": "Аудит планировщика задач Windows",
        "create_task": "Создать задачу",
        "refresh": "Пересканировать",
        "headers": ["Имя задачи / Категория", "Время создания", "Исполняемый файл / Команда"],
        "status_ready": "Готов к работе. Права администратора активны.",
        "status_scanning": "Сканирование планировщика задач...",
        "status_done": "Сканирование завершено. Всего проанализировано задач: ",
        "cat_fresh": "Менее 24 часов (Свежие - зона риска!)",
        "cat_1_month": "От 1 дня до 1 месяца",
        "cat_6_months": "От 1 месяца до 6 месяцев",
        "cat_1_year": "От 6 месяцев до 1 года",
        "cat_old": "Более 1 года назад",
        "menu_edit": "Редактировать задачу",
        "menu_copy_name": "Копировать имя задачи",
        "menu_copy_cmd": "Копировать команду",
        "menu_delete": "Удалить задачу",
        "dialog_create_title": "Создать новую задачу",
        "dialog_edit_title": "Редактировать задачу",
        "label_name": "Имя задачи:",
        "label_path": "Путь к файлу / Команда:",
        "label_args": "Аргументы запуска:",
        "label_trigger": "Триггер запуска:",
        "label_time": "Время запуска:",
        "btn_browse": "Обзор",
        "btn_save": "Сохранить задачу",
        "btn_create": "Создать задачу",
        "btn_cancel": "Отмена",
        "triggers": ["При запуске системы (ONSTART)", "При входе пользователя (ONLOGON)", "Ежедневно (DAILY)"],
        "msg_error": "Ошибка",
        "msg_warning_fields": "Имя задачи и путь к файлу обязательны для заполнения!",
        "msg_success_create": "Задача успешно создана!",
        "msg_success_update": "Задача успешно обновлена!",
        "msg_success_delete": "Задача успешно удалена!",
        "msg_delete_confirm": "Вы уверены, что хотите удалить задачу",
        "xml_error": "Не удалось найти XML-файл для этой задачи."
    },
    "de": {
        "window_title": "HeroAnalizator — Windows Sicherheit & Forensik",
        "scanner_title": "Windows Aufgabenplanung Auditor",
        "create_task": "Aufgabe erstellen",
        "refresh": "Aktualisieren",
        "headers": ["Aufgabenname / Kategorie", "Erstellungszeit", "Ausführbare Datei / Befehl"],
        "status_ready": "Bereit. Administratorrechte aktiv.",
        "status_scanning": "Aufgabenplanung wird gescannt...",
        "status_done": "Scan abgeschlossen. Analysierte Aufgaben gesamt: ",
        "cat_fresh": "Weniger als 24 Stunden (Frisch - Risikobereich!)",
        "cat_1_month": "1 Tag bis 1 Monat",
        "cat_6_months": "1 Monat bis 6 Monate",
        "cat_1_year": "6 Monate bis 1 Jahr",
        "cat_old": "Vor mehr als 1 Jahr",
        "menu_edit": "Aufgabe bearbeiten",
        "menu_copy_name": "Namen kopieren",
        "menu_copy_cmd": "Befehl kopieren",
        "menu_delete": "Aufgabe löschen",
        "dialog_create_title": "Neue Aufgabe erstellen",
        "dialog_edit_title": "Aufgabe bearbeiten",
        "label_name": "Name der Aufgabe:",
        "label_path": "Pfad zur Datei:",
        "label_args": "Argumente:",
        "label_trigger": "Auslöser:",
        "label_time": "Ausführungszeit:",
        "btn_browse": "Durchsuchen",
        "btn_save": "Speichern",
        "btn_create": "Erstellen",
        "btn_cancel": "Abbrechen",
        "triggers": ["Beim Systemstart (ONSTART)", "Bei Anmeldung (ONLOGON)", "Täglich (DAILY)"],
        "msg_error": "Fehler",
        "msg_warning_fields": "Aufgabenname und Dateipfad sind erforderlich!",
        "msg_success_create": "Aufgabe erfolgreich erstellt!",
        "msg_success_update": "Aufgabe erfolgreich aktualisiert!",
        "msg_success_delete": "Aufgabe erfolgreich gelöscht!",
        "msg_delete_confirm": "Möchten Sie die Aufgabe wirklich löschen",
        "xml_error": "XML-Datei für diese Aufgabe nicht gefunden."
    },
    "fr": {
        "window_title": "HeroAnalizator — Sécurité Windows & Forensique",
        "scanner_title": "Auditeur du Planificateur de tâches Windows",
        "create_task": "Créer une tâche",
        "refresh": "Actualiser",
        "headers": ["Nom de la tâche / Catégorie", "Date de création", "Exécutable / Commande"],
        "status_ready": "Prêt. Privilèges administrateur actifs.",
        "status_scanning": "Analyse du planificateur de tâches...",
        "status_done": "Analyse terminée. Total des tâches analysées : ",
        "cat_fresh": "Moins de 24 heures (Récent - Zone à risque !)",
        "cat_1_month": "1 jour à 1 mois",
        "cat_6_months": "1 mois à 6 mois",
        "cat_1_year": "6 mois à 1 an",
        "cat_old": "Il y a plus d'un an",
        "menu_edit": "Modifier la tâche",
        "menu_copy_name": "Copier le nom",
        "menu_copy_cmd": "Copier la commande",
        "menu_delete": "Supprimer la tâche",
        "dialog_create_title": "Créer une nouvelle tâche",
        "dialog_edit_title": "Modifier la tâche",
        "label_name": "Nom de la tâche :",
        "label_path": "Chemin du fichier :",
        "label_args": "Arguments :",
        "label_trigger": "Déclencheur :",
        "label_time": "Heure d'exécution :",
        "btn_browse": "Parcourir",
        "btn_save": "Enregistrer",
        "btn_create": "Créer",
        "btn_cancel": "Annuler",
        "triggers": ["Au démarrage (ONSTART)", "À la connexion (ONLOGON)", "Quotidien (DAILY)"],
        "msg_error": "Erreur",
        "msg_warning_fields": "Le nom de la tâche et le chemin sont obligatoires !",
        "msg_success_create": "Tâche créée avec succès !",
        "msg_success_update": "Tâche mise à jour avec succès !",
        "msg_success_delete": "Tâche supprimée avec succès !",
        "msg_delete_confirm": "Voulez-vous vraiment supprimer la tâche",
        "xml_error": "Fichier XML introuvable pour cette tâche."
    },
    "es": {
        "window_title": "HeroAnalizator — Seguridad de Windows y Forense",
        "scanner_title": "Auditor del Programador de Tareas de Windows",
        "create_task": "Crear tarea",
        "refresh": "Actualizar",
        "headers": ["Nombre de tarea / Categoría", "Fecha de creación", "Ejecutable / Comando"],
        "status_ready": "Listo. Privilegios de administrador activos.",
        "status_scanning": "Analizando programador de tareas...",
        "status_done": "Análisis completo. Total de tareas analizadas: ",
        "cat_fresh": "Menos de 24 horas (¡Reciente - Zona de riesgo!)",
        "cat_1_month": "1 día a 1 mes",
        "cat_6_months": "1 mes a 6 meses",
        "cat_1_year": "6 meses a 1 año",
        "cat_old": "Hace más de 1 año",
        "menu_edit": "Editar tarea",
        "menu_copy_name": "Copiar nombre",
        "menu_copy_cmd": "Copiar comando",
        "menu_delete": "Eliminar tarea",
        "dialog_create_title": "Crear nueva tarea",
        "dialog_edit_title": "Editar tarea",
        "label_name": "Nombre de la tarea:",
        "label_path": "Ruta del archivo:",
        "label_args": "Argumentos:",
        "label_trigger": "Desencadenante:",
        "label_time": "Hora de ejecución:",
        "btn_browse": "Examinar",
        "btn_save": "Guardar tarea",
        "btn_create": "Crear tarea",
        "btn_cancel": "Cancelar",
        "triggers": ["Al iniciar el sistema (ONSTART)", "Al iniciar sesión (ONLOGON)", "Diario (DAILY)"],
        "msg_error": "Error",
        "msg_warning_fields": "¡El nombre y la ruta del archivo son obligatorios!",
        "msg_success_create": "¡Tarea creada con éxito!",
        "msg_success_update": "¡Tarea actualizada con éxito!",
        "msg_success_delete": "¡Tarea eliminada con éxito!",
        "msg_delete_confirm": "¿Está seguro de que desea eliminar la tarea",
        "xml_error": "No se encontró el archivo XML para esta tarea."
    }
}

CURRENT_LANG = "en"  # Язык по умолчанию

def t(key):
    return TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["en"]).get(key, key)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_privileges():
    try:
        script = sys.argv[0]
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    except Exception as e:
        print(f"Error elevating privileges: {e}")


class TaskScannerThread(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        tasks_path = os.path.expandvars(r"%WINDIR%\System32\Tasks")
        now = datetime.datetime.now()
        
        categories = {
            "cat_fresh": [],
            "cat_1_month": [],
            "cat_6_months": [],
            "cat_1_year": [],
            "cat_old": []
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
                        categories["cat_fresh"].append(task_info)
                    elif age_days < 30:
                        categories["cat_1_month"].append(task_info)
                    elif age_days < 180:
                        categories["cat_6_months"].append(task_info)
                    elif age_days < 365:
                        categories["cat_1_year"].append(task_info)
                    else:
                        categories["cat_old"].append(task_info)
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
        except Exception:
            return "XML Read Error"
        return "Unknown"


class CreateTaskDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, task_name="", xml_path=""):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.initial_name = task_name
        self.xml_path = xml_path
        
        self.setWindowTitle(t("dialog_edit_title") if self.edit_mode else t("dialog_create_title"))
        self.resize(500, 320)
        self.init_ui()

        if self.edit_mode and self.xml_path:
            self.load_task_data()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: #d4d4d4; }
            QLabel { color: #d4d4d4; font-size: 12px; }
            QLineEdit, QComboBox, QTimeEdit {
                background-color: #252526; color: #d4d4d4;
                border: 1px solid #3f3f46; padding: 6px; border-radius: 4px;
            }
            QPushButton {
                background-color: #007acc; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #0098ff; }
        """)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        if self.edit_mode:
            self.name_input.setReadOnly(True)
            self.name_input.setStyleSheet("background-color: #2d2d30; color: #888888;")
        form_layout.addRow(t("label_name"), self.name_input)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        browse_btn = QPushButton(t("btn_browse"))
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        form_layout.addRow(t("label_path"), path_layout)

        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("e.g. --silent or /update")
        form_layout.addRow(t("label_args"), self.args_input)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(t("triggers"))
        self.trigger_combo.currentIndexChanged.connect(self.on_trigger_changed)
        form_layout.addRow(t("label_trigger"), self.trigger_combo)

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit_label = QLabel(t("label_time"))
        form_layout.addRow(self.time_edit_label, self.time_edit)
        
        self.time_edit.setVisible(False)
        self.time_edit_label.setVisible(False)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton(t("btn_save") if self.edit_mode else t("btn_create"))
        save_btn.clicked.connect(self.save_task)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton(t("btn_cancel"))
        cancel_btn.setStyleSheet("background-color: #3f3f46;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Executable", "C:\\", "Executables (*.exe);;All Files (*.*)")
        if file_path:
            self.path_input.setText(file_path)

    def on_trigger_changed(self, index):
        is_daily = (index == 2)
        self.time_edit.setVisible(is_daily)
        self.time_edit_label.setVisible(is_daily)

    def load_task_data(self):
        try:
            self.name_input.setText(self.initial_name)
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            exec_elem = root.find('.//Exec')
            if exec_elem is not None:
                cmd = exec_elem.find('Command')
                args = exec_elem.find('Arguments')
                if cmd is not None and cmd.text:
                    self.path_input.setText(cmd.text)
                if args is not None and args.text:
                    self.args_input.setText(args.text)

            if root.find('.//BootTrigger') is not None:
                self.trigger_combo.setCurrentIndex(0)
            elif root.find('.//LogonTrigger') is not None:
                self.trigger_combo.setCurrentIndex(1)
            elif root.find('.//CalendarTrigger') is not None:
                self.trigger_combo.setCurrentIndex(2)
                time_elem = root.find('.//StartBoundary')
                if time_elem is not None and time_elem.text:
                    try:
                        t_part = time_elem.text.split('T')[1][:5]
                        self.time_edit.setTime(QTime.fromString(t_part, "HH:mm"))
                    except:
                        pass
        except Exception as e:
            print(f"Error parsing XML: {e}")

    def save_task(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        args = self.args_input.text().strip()
        trigger_idx = self.trigger_combo.currentIndex()

        if not name or not path:
            QMessageBox.warning(self, t("msg_error"), t("msg_warning_fields"))
            return

        full_tr = f'"{path}"'
        if args:
            full_tr += f' {args}'

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
                msg = t("msg_success_update") if self.edit_mode else t("msg_success_create")
                QMessageBox.information(self, "Success", msg)
                self.accept()
            else:
                QMessageBox.warning(self, t("msg_error"), f"{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, t("msg_error"), str(e))


class HeroAnalizatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_scanning()

    def init_ui(self):
        self.setWindowTitle(t("window_title"))
        self.resize(1050, 650)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QLabel { color: #d4d4d4; font-size: 13px; }
            QPushButton {
                background-color: #007acc; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #0098ff; }
            QComboBox {
                background-color: #252526; color: #d4d4d4;
                border: 1px solid #3f3f46; padding: 4px; border-radius: 4px;
            }
            QTreeWidget {
                background-color: #252526; color: #d4d4d4;
                border: 1px solid #3f3f46; border-radius: 4px; font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2d2d30; color: #ffffff; padding: 6px;
                border: 1px solid #3f3f46; font-weight: bold;
            }
            QStatusBar { background-color: #007acc; color: white; font-weight: bold; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        top_layout = QHBoxLayout()
        self.title_label = QLabel(t("scanner_title"))
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        top_layout.addWidget(self.title_label)
        
        top_layout.addStretch()

        # Выпадающий список языков (включая русский)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "Русский", "Deutsch", "Français", "Español"])
        lang_map = {"en": 0, "ru": 1, "de": 2, "fr": 3, "es": 4}
        self.lang_combo.setCurrentIndex(lang_map.get(CURRENT_LANG, 0))
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        top_layout.addWidget(self.lang_combo)

        self.create_btn = QPushButton(t("create_task"))
        self.create_btn.setStyleSheet("background-color: #28a745;")
        self.create_btn.clicked.connect(self.open_create_dialog)
        top_layout.addWidget(self.create_btn)

        self.refresh_btn = QPushButton(t("refresh"))
        self.refresh_btn.clicked.connect(self.start_scanning)
        top_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(top_layout)

        self.tree = QTreeWidget()
        headers = t("headers")
        self.tree.setHeaderLabels(headers)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.tree)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t("status_ready"))

    def change_language(self, index):
        global CURRENT_LANG
        lang_codes = ["en", "ru", "de", "fr", "es"]
        CURRENT_LANG = lang_codes[index]
        self.init_ui()
        self.start_scanning()

    def open_create_dialog(self):
        dialog = CreateTaskDialog(self, edit_mode=False)
        if dialog.exec():
            self.start_scanning()

    def open_edit_dialog(self, item):
        task_name = item.text(0)
        xml_path = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not xml_path or not os.path.exists(xml_path):
            QMessageBox.warning(self, t("msg_error"), t("xml_error"))
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
            QMenu { background-color: #252526; color: #d4d4d4; border: 1px solid #3f3f46; }
            QMenu::item:selected { background-color: #007acc; color: white; }
        """)

        edit_action = QAction(t("menu_edit"), self)
        copy_name_action = QAction(t("menu_copy_name"), self)
        copy_cmd_action = QAction(t("menu_copy_cmd"), self)
        delete_action = QAction(t("menu_delete"), self)

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
            t("msg_error"), 
            f"{t('msg_delete_confirm')} '{task_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                result = subprocess.run(
                    ["schtasks", "/Delete", "/TN", task_name, "/F"],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    QMessageBox.information(self, "Success", t("msg_success_delete"))
                    self.start_scanning()
                else:
                    QMessageBox.warning(self, t("msg_error"), result.stderr)
            except Exception as e:
                QMessageBox.critical(self, t("msg_error"), str(e))

    def start_scanning(self):
        self.tree.clear()
        self.status_bar.showMessage(t("status_scanning"))
        self.refresh_btn.setEnabled(False)
        self.create_btn.setEnabled(False)

        self.scanner_thread = TaskScannerThread()
        self.scanner_thread.finished.connect(self.display_results)
        self.scanner_thread.start()

    def display_results(self, categories):
        total_tasks = 0
        for cat_key, tasks in categories.items():
            total_tasks += len(tasks)
            category_title = f"{t(cat_key)} (Total: {len(tasks)})"
            cat_item = QTreeWidgetItem(self.tree, [category_title])
            cat_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            if cat_key == "cat_fresh" and len(tasks) > 0:
                cat_item.setForeground(0, QColor("#ff6b6b"))

            for t_data in tasks:
                task_item = QTreeWidgetItem(cat_item, [t_data["name"], t_data["created"], t_data["action"]])
                task_item.setData(0, Qt.ItemDataRole.UserRole, t_data["path"])
                
        self.tree.expandAll()
        self.refresh_btn.setEnabled(True)
        self.create_btn.setEnabled(True)
        self.status_bar.showMessage(f"{t('status_done')}{total_tasks}")


if __name__ == "__main__":
    if not is_admin():
        elevate_privileges()
        sys.exit()

    app = QApplication(sys.argv)
    window = HeroAnalizatorWindow()
    window.show()
    sys.exit(app.exec())
