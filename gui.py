from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QFileDialog, QMessageBox
import re
import sys
import os
import requests


class AuthApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация и работа с файлами')
        self.setGeometry(100, 100, 400, 200)

        layout = QVBoxLayout()

        self.role = "user"
        self.access_token = None

        self.user_button = QPushButton('Пользователь')
        self.user_button.clicked.connect(self.set_user_role)
        self.user_button.setStyleSheet("QPushButton { background-color: #007BFF; color: white; }")
        layout.addWidget(self.user_button)

        self.admin_button = QPushButton('Администратор')
        self.admin_button.clicked.connect(self.set_admin_role)
        self.admin_button.setStyleSheet("QPushButton { background-color: #28A745; color: white; }")
        layout.addWidget(self.admin_button)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Логин')
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton('Войти')
        self.login_button.clicked.connect(self.login)
        self.login_button.setStyleSheet("QPushButton { background-color: #007BFF; color: white; }")
        layout.addWidget(self.login_button)

        self.signup_button = QPushButton('Зарегистрироваться')
        self.signup_button.clicked.connect(self.signup)
        self.signup_button.setStyleSheet("QPushButton { background-color: #28A745; color: white; }")
        layout.addWidget(self.signup_button)

        self.message_label = QLabel('')
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def set_user_role(self):
        self.role = "user"
        self.message_label.setText("Выбрана роль: Пользователь")

    def set_admin_role(self):
        self.role = "admin"
        self.message_label.setText("Выбрана роль: Администратор")

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.role == "user":
            endpoint = "/users/signin"
        elif self.role == "admin":
            endpoint = "/users/admin"

        response = requests.post(f"http://127.0.0.1:8000{endpoint}", data={"username": username, "password": password})
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            self.message_label.setText("Вы успешно авторизовались")
            self.open_main_window()

            self.username_input.clear()
            self.password_input.clear()
        else:
            self.message_label.setText("Неверный логин или пароль")

    def signup(self):
        username = self.username_input.text()
        password = self.password_input.text()

        response = requests.post(f"http://127.0.0.1:8000/users/signup",
                                 json={"username": username, "password": password, "role": self.role, "logged": False})
        if response.status_code == 200:
            self.message_label.setText("Пользователь успешно зарегистрирован")
        else:
            self.message_label.setText("Пользователь с таким именем уже существует")

    def open_main_window(self):
        self.hide()
        self.main_window = MainWindow(self.username_input.text(), self.role, self.access_token)
        self.main_window.show()


class MainWindow(QWidget):
    def __init__(self, username, role, access_token):
        super().__init__()
        self.setWindowTitle(f'Добро пожаловать, {username}')
        self.setGeometry(100, 100, 600, 300)

        self.role = role
        self.username = username
        self.access_token = access_token

        layout = QVBoxLayout()

        self.logout_button = QPushButton('Выйти')
        self.logout_button.clicked.connect(self.logout)
        layout.addWidget(self.logout_button)

        self.choose_directory_button = QPushButton('Выбрать каталог')
        self.choose_directory_button.clicked.connect(self.choose_directory)
        layout.addWidget(self.choose_directory_button)

        if self.role == "admin":
            self.create_file_button = QPushButton('Создать файл')
            self.create_file_button.clicked.connect(self.create_file)
            layout.addWidget(self.create_file_button)

        self.message_label = QLabel('')
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def choose_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Выберите каталог')
        if directory:
            file_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])

            if self.role == "user":
                if file_count <= 19:
                    self.message_label.setText(f"Каталог {directory} успешно выбран")

                    # Получаем список файлов в выбранной директории
                    files = os.listdir(directory)

                    # Отображаем содержимое директории пользователю
                    message = '\n'.join(files) if files else 'Папка пуста'
                    self.message_label.setText(f'Содержимое каталога \n{message}')

                else:
                    self.message_label.setText("Превышено максимальное количество файлов в папке (19)")
            else:
                self.message_label.setText(f"Каталог {directory} успешно выбран")

    def create_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Создать файл', '', 'Any (.)')
        if file_name:
            file_extension = os.path.splitext(file_name)[1]

            if file_extension != '.exe':
                with open(file_name, 'w') as file:
                    file.write('')
                self.message_label.setText(f"Файл {file_name} успешно создан")
            else:
                self.message_label.setText("Название файла не должно содержать расширение .exe")

    def logout(self):
        response = requests.post("http://127.0.0.1:8000/logout", headers={"Authorization": f"Bearer {self.access_token}"})
        if response.status_code == 200:
            self.message_label.setText("Вы успешно вышли из аккаунта")
            self.close()
            auth_app.show()
        else:
            self.message_label.setText("Произошла ошибка при выходе из аккаунта")


app = QApplication(sys.argv)
app.setStyleSheet("""
    QWidget {
        background-color: #f0f0f0;
        font-family: Arial;
    }
    QPushButton {
        background-color: #007BFF;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    QLineEdit {
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: 5px;
    }
    QLabel {
        font-size: 16px;
    }
""")
auth_app = AuthApp()
auth_app.show()
sys.exit(app.exec_())
