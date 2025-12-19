import sys
import sqlite3
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QMessageBox, QFrame, QLineEdit,
    QTextEdit, QDateEdit, QScrollArea, QDialog, QComboBox, QSystemTrayIcon,
    QMenu,
    QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QIcon, QAction


class Database:
    def __init__(self, db_file='task_todo.db'):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT    NOT NULL,
                description  TEXT,
                deadline     TEXT    NOT NULL,
                created_date TEXT    NOT NULL,
                is_completed BOOLEAN NOT NULL,
                reminder_time TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_all_tasks(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks')
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'deadline': row[3],
                'created_date': row[4],
                'is_completed': bool(row[5]),
                'reminder_time': row[6] if row[6] else "09:00"
            })
        conn.close()
        return tasks

    def add_task(self, task_data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (title, description, deadline, created_date,
            is_completed, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['created_date'],
            task_data['is_completed'],
            task_data.get('reminder_time', '09:00')
        ))
        conn.commit()
        conn.close()

    def update_task(self, task_data):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks
            SET title=?, description=?, deadline=?, created_date=?,
            is_completed=?,
            reminder_time=?
            WHERE id=?
        ''', (
            task_data['title'],
            task_data['description'],
            task_data['deadline'],
            task_data['created_date'],
            task_data['is_completed'],
            task_data.get('reminder_time', '09:00'),
            task_data['id']
        ))
        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()
        conn.close()


class TaskDialog(QDialog):
    def __init__(self, parent=None, task_data=None):
        super().__init__(parent)
        self.task_data = task_data
        self.is_edit = task_data is not None
        self.setWindowTitle("Редактировать задачу" if self.is_edit else
                            "Новая задача")
        self.setFixedSize(400, 350)
        self.setup_ui()

        if self.is_edit:
            self.load_task_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(QLabel("Название:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название задачи...")
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Описание:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Необязательное описание...")
        layout.addWidget(self.desc_input)

        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Дедлайн:"))
        self.deadline_date = QDateEdit()
        self.deadline_date.setDate(QDate.currentDate().addDays(1))
        deadline_layout.addWidget(self.deadline_date)
        deadline_layout.addStretch()
        layout.addLayout(deadline_layout)

        reminder_layout = QHBoxLayout()
        reminder_layout.addWidget(QLabel("Напоминание:"))
        self.reminder_time = QTimeEdit()
        self.reminder_time.setTime(QTime(9, 0))
        self.reminder_time.setDisplayFormat("HH:mm")
        reminder_layout.addWidget(self.reminder_time)
        reminder_layout.addStretch()
        layout.addLayout(reminder_layout)

        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Отмена")
        self.save_btn = QPushButton("Сохранить" if self.is_edit else "Создать")
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.save_task)

    def load_task_data(self):
        self.title_input.setText(self.task_data['title'])
        self.desc_input.setPlainText(self.task_data.get('description', ''))
        deadline_date = datetime.fromisoformat(self.task_data['deadline']).date()
        self.deadline_date.setDate(QDate(deadline_date.year, deadline_date.month, deadline_date.day))

        reminder_time = self.task_data.get('reminder_time', '09:00')
        if reminder_time:
            hours, minutes = map(int, reminder_time.split(':'))
            self.reminder_time.setTime(QTime(hours, minutes))

    def save_task(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название задачи!")
            return
        self.accept()

    def get_task_data(self):
        deadline = datetime(
            self.deadline_date.date().year(),
            self.deadline_date.date().month(),
            self.deadline_date.date().day(),
            23, 59
        )

        reminder_time_obj = self.reminder_time.time()
        reminder_time_str = f"{reminder_time_obj.hour():02d}:{reminder_time_obj.minute():02d}"

        task_data = {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'deadline': deadline.isoformat(),
            'created_date': datetime.now().isoformat() if not self.is_edit else self.task_data['created_date'],
            'is_completed': self.task_data.get('is_completed', False) if self.is_edit else False,
            'reminder_time': reminder_time_str
        }

        if self.is_edit:
            task_data['id'] = self.task_data['id']

        return task_data


class TaskCard(QFrame):
    def __init__(self, task_data, update_callback, db):
        super().__init__()
        self.task_data = task_data
        self.update_callback = update_callback
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data['is_completed'])
        self.checkbox.stateChanged.connect(self.toggle_complete)

        self.title_label = QLabel(self.task_data['title'])
        self.title_label.setStyleSheet("font-size: 14px;")

        top_layout.addWidget(self.checkbox)
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        edit_btn = QPushButton("Ред.")
        edit_btn.setFixedSize(50, 25)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd;
                color: #1976d2;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)
        edit_btn.clicked.connect(self.edit_task)
        edit_btn.setToolTip("Редактировать")
        top_layout.addWidget(edit_btn)

        layout.addLayout(top_layout)

        if self.task_data['description']:
            desc_label = QLabel(self.task_data['description'])
            desc_label.setStyleSheet("color: #666; font-size: 12px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        bottom_layout = QHBoxLayout()

        deadline = datetime.fromisoformat(self.task_data['deadline'])
        days_left = (deadline.date() - date.today()).days

        if days_left < 0:
            time_text = "Просрочено"
            time_style = "color: #e74c3c; font-size: 11px;"
        elif days_left == 0:
            time_text = "Сегодня"
            time_style = "color: #f39c12; font-size: 11px;"
        elif days_left == 1:
            time_text = "Завтра"
            time_style = "color: #f39c12; font-size: 11px;"
        else:
            time_text = f"Осталось {days_left} дней"
            time_style = "color: #7f8c8d; font-size: 11px;"

        deadline_label = QLabel(time_text)
        deadline_label.setStyleSheet(time_style)
        bottom_layout.addWidget(deadline_label)

        bottom_layout.addStretch()

        delete_btn = QPushButton("Удалить")
        delete_btn.setFixedSize(70, 25)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #dc2626;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        delete_btn.clicked.connect(self.delete_task)
        delete_btn.setToolTip("Удалить задачу")
        bottom_layout.addWidget(delete_btn)

        layout.addLayout(bottom_layout)
        self.update_style()

    def toggle_complete(self):
        self.task_data['is_completed'] = self.checkbox.isChecked()
        self.db.update_task(self.task_data)
        self.update_style()
        self.update_callback()

    def edit_task(self):
        dialog = TaskDialog(self.window(), self.task_data)
        if dialog.exec():
            updated_data = dialog.get_task_data()
            self.db.update_task(updated_data)
            self.task_data.update(updated_data)
            self.update_callback()

    def delete_task(self):
        reply = QMessageBox.question(
            self, "Удаление",
            f"Удалить '{self.task_data['title']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_task(self.task_data['id'])
            self.update_callback()

    def update_style(self):
        if self.task_data['is_completed']:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }
            """)
            self.title_label.setStyleSheet("""
                color: #95a5a6;
                text-decoration: line-through;
                font-size: 14px;
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 4px;
                }
            """)
            self.title_label.setStyleSheet("""
                color: #2c3e50;
                font-size: 14px;
            """)


class SimpleTaskManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("icons8.png"))
        self.db = Database('task_todo.db')
        self.tasks = []
        self.load_tasks()

        self.sent_reminders = set()

        self.setup_tray_icon()

        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)

        self.setup_ui()

        QTimer.singleShot(1000, self.check_reminders)

    def setup_tray_icon(self):
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)
                self.tray_icon.setIcon(QIcon("icons8.png"))
                self.tray_icon.setToolTip("Менеджер задач")

                tray_menu = QMenu()

                show_action = QAction("Показать", self)
                show_action.triggered.connect(self.show_window)
                tray_menu.addAction(show_action)

                hide_action = QAction("Скрыть", self)
                hide_action.triggered.connect(self.hide_window)
                tray_menu.addAction(hide_action)

                tray_menu.addSeparator()

                check_reminders_action = QAction("Проверить напоминания", self)
                check_reminders_action.triggered.connect(self.check_reminders)
                tray_menu.addAction(check_reminders_action)

                tray_menu.addSeparator()

                quit_action = QAction("Выход", self)
                quit_action.triggered.connect(self.quit_application)
                tray_menu.addAction(quit_action)

                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.tray_icon_activated)
                self.tray_icon.show()

        except Exception:
            print("Ошибка")

    def setup_ui(self):
        self.setWindowTitle("Менеджер задач")
        self.setGeometry(100, 100, 500, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel("Задачи")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        control_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")
        self.search_input.textChanged.connect(self.filter_tasks)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Все",
            "Активные",
            "Выполненные",
            "Просроченные",
            "На сегодня",
            "На завтра"
        ])
        self.filter_combo.currentTextChanged.connect(self.filter_tasks)

        self.add_btn = QPushButton("+ Новая")
        self.add_btn.clicked.connect(self.add_task)

        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.filter_combo)
        control_layout.addWidget(self.add_btn)
        layout.addLayout(control_layout)

        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.tasks_layout = QVBoxLayout(self.scroll_widget)
        self.tasks_layout.setSpacing(8)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
        """)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)

        self.apply_styles()
        self.filter_tasks()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #9370DB;
            }
            QPushButton {
                background-color: #9370DB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #9370DB;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border-color: #27ae60;
            }
            QTimeEdit {
                padding: 6px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }
        """)

    def load_tasks(self):
        self.tasks = self.db.get_all_tasks()

    def add_task(self):
        dialog = TaskDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            self.db.add_task(task_data)
            self.load_tasks()
            self.filter_tasks()

            self.check_reminders()

    def filter_tasks(self):
        self.tasks = self.db.get_all_tasks()

        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()

        filtered_tasks = []
        today = date.today()

        for task in self.tasks:
            if search_text and search_text not in task['title'].lower():
                continue

            deadline_date = datetime.fromisoformat(task['deadline']).date()
            days_left = (deadline_date - today).days

            if filter_type == "Активные" and task['is_completed']:
                continue
            elif filter_type == "Выполненные" and not task['is_completed']:
                continue
            elif filter_type == "Просроченные":
                if not (days_left < 0 and not task['is_completed']):
                    continue
            elif filter_type == "На сегодня":
                if not (days_left == 0 and not task['is_completed']):
                    continue
            elif filter_type == "На завтра":
                if not (days_left == 1 and not task['is_completed']):
                    continue

            filtered_tasks.append(task)

        filtered_tasks.sort(key=lambda x: x['created_date'], reverse=True)

        if not filtered_tasks:
            label = QLabel("Задачи не найдены")
            label.setStyleSheet("""
                font-size: 16px;
                color: #bdc3c7;
                text-align: center;
                padding: 40px;
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_layout.addWidget(label)
        else:
            for task in filtered_tasks:
                task_card = TaskCard(task, self.filter_tasks, self.db)
                self.tasks_layout.addWidget(task_card)

        self.update_stats()

    def update_stats(self):
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t['is_completed']])
        active = total - completed

        stats_text = f"Всего: {total} | Актив: {active} | Выпол: {completed}"
        self.stats_label.setText(stats_text)

    def check_reminders(self):
        try:
            if not hasattr(self, 'tray_icon') or not self.tray_icon.isVisible():
                return

            now = datetime.now()
            today = now.date()
            current_time = now.strftime("%H:%M")

            for task in self.db.get_all_tasks():
                if task['is_completed']:
                    continue

                task_id = task['id']
                deadline = datetime.fromisoformat(task['deadline']).date()
                reminder_time = task.get('reminder_time', '09:00')
                days_left = (deadline - today).days

                reminder_key = f"{task_id}_{today}_{reminder_time}"

                if days_left < 0:
                    overdue_key = f"{task_id}_{today}_overdue"
                    if overdue_key not in self.sent_reminders:
                        self.tray_icon.showMessage(
                            "⚠️ Просроченная задача",
                            f"Задача '{task['title']}' просрочена!",
                            QSystemTrayIcon.MessageIcon.Warning,
                            5000
                        )
                        self.sent_reminders.add(overdue_key)

                elif days_left == 0 and current_time == reminder_time:
                    if reminder_key not in self.sent_reminders:
                        self.tray_icon.showMessage(
                            "⏰ Напоминание",
                            f"Сегодня в {reminder_time}: '{task['title']}'",
                            QSystemTrayIcon.MessageIcon.Information,
                            5000
                        )
                        self.sent_reminders.add(reminder_key)

                elif days_left == 1 and current_time == "09:00":
                    tomorrow_key = f"{task_id}_{today}_tomorrow"
                    if tomorrow_key not in self.sent_reminders:
                        self.tray_icon.showMessage(
                            "📅 Задача на завтра",
                            f"Завтра в {reminder_time}: '{task['title']}'",
                            QSystemTrayIcon.MessageIcon.Information,
                            5000
                        )
                        self.sent_reminders.add(tomorrow_key)

            current_keys = list(self.sent_reminders)
            for key in current_keys:
                if str(today) not in key and str(today - date.resolution) not in key:
                    self.sent_reminders.remove(key)

        except Exception as e:
            print(f"Ошибка при проверке напоминаний: {e}")

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        self.hide()

    def quit_application(self):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        self.close()

    def closeEvent(self, event):
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы точно хотите закрыть приложение?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.hide()
                event.accept()
            else:
                self.hide()
                event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = SimpleTaskManager()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
