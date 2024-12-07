import sys
import sqlite3
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFormLayout, QHBoxLayout, QInputDialog, QMessageBox, QTableWidget, QTableWidgetItem, QColorDialog

class BankApp(QWidget):
    def __init__(self):
        super().__init__()
        self.db_connection = sqlite3.connect('bank_system.db')
        self.db_cursor = self.db_connection.cursor()
        self.setup_db()
        self.init_ui()

    def setup_db(self):
        #Созд таблиц
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                role TEXT,
                rub_balance REAL DEFAULT 0,
                kzt_balance REAL DEFAULT 0,
                usd_balance REAL DEFAULT 0
            );
        ''')
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user TEXT,
                to_user TEXT,
                amount REAL,
                currency TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Если база пустая, создаем администратора
        self.db_cursor.execute('SELECT COUNT(*) FROM users')
        if self.db_cursor.fetchone()[0] == 0:
            self.db_cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', 'qwerty', 'admin'))
            self.db_connection.commit()

    def init_ui(self):
        self.setWindowTitle("Bank System")

        # Устанавливаем фиксированные размеры окна
        self.setFixedSize(600, 400)

        # Добавляем выбор цвета
        self.choose_color()

        # Начальный экран: Логин
        self.login_form = QWidget(self)
        self.login_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_layout.addRow('Ник:', self.username_input)
        self.login_layout.addRow('Пароль:', self.password_input)

        self.login_button = QPushButton('Вход')
        self.login_button.clicked.connect(self.login)
        self.login_layout.addRow(self.login_button)

        self.login_form.setLayout(self.login_layout)
        self.login_form.show()

    def choose_color(self):
        options = {
            "Желтый": "background-color: yellow;",
            "Зеленый": "background-color: green;",
            "Синий": "background-color: blue;",
            "Без изменений": ""
        }
        items = list(options.keys())
        color, ok = QInputDialog.getItem(self, "Выбор цвета", "Выберите цвет интерфейса:", items, 0, False)
        if ok and color:
            self.setStyleSheet(options[color])

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Проверяем наличие пользователя в базе данных
        self.db_cursor.execute('SELECT role FROM users WHERE username = ? AND password = ?', (username, password))
        result = self.db_cursor.fetchone()

        if result:
            role = result[0]
            if role == 'admin':
                print("Переход в админ-панель")  # Отладка
                self.show_admin_dashboard(username)
            elif role == 'client':
                print("Переход в панель клиента")  # Отладка
                self.show_client_dashboard(username)
            else:
                self.show_error("Неизвестная роль")
        else:
            self.show_error('Неверные учетные данные или пользователь не существует')


    def show_admin_dashboard(self, username):
        self.login_form.close()

        self.admin_dashboard = QWidget(self)
        self.admin_dashboard.setWindowTitle("Admin Dashboard")

        layout = QVBoxLayout()

        add_client_button = QPushButton('Добавить клиента')
        add_client_button.clicked.connect(self.add_client)
        layout.addWidget(add_client_button)

        add_balance_button = QPushButton('Пополнить баланс')
        add_balance_button.clicked.connect(self.add_balance)
        layout.addWidget(add_balance_button)

        history_button = QPushButton('Транзакции')
        history_button.clicked.connect(self.view_transaction_history)
        layout.addWidget(history_button)

        back_button = QPushButton('Назад')
        back_button.clicked.connect(self.show_login)
        layout.addWidget(back_button)

        self.admin_dashboard.setLayout(layout)
        self.admin_dashboard.show()

    def add_client(self):
        username, password = self.get_username_password()
        if username and password:
            self.db_cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, 'client'))
            self.db_connection.commit()
            self.show_info(f'Клиент {username} добавлен')

    def add_balance(self):
        username, amount, currency = self.get_balance_info()
        if username and amount and currency:
            self.db_cursor.execute(f'UPDATE users SET {currency}_balance = {currency}_balance + ? WHERE username = ?', (amount, username))
            self.db_connection.commit()
            self.show_info(f'Успешное пополнение для {username}')

    def get_username_password(self):
        username = self.prompt_input('Ник:')
        password = self.prompt_input('Пароль:')
        return username, password

    def get_balance_info(self):
        username = self.prompt_input('Ник пользователя:')
        amount = self.prompt_input('Сколько:', True)
        currency = self.prompt_input('Выберите валюту (rub, kzt, usd):')
        return username, amount, currency

    def prompt_input(self, message, is_number=False):
        value, ok = QInputDialog.getText(self, 'Input', message)
        if ok and value:
            return float(value) if is_number else value
        if not ok:
            self.show_info("Операция отменена")
        return None

    def show_info(self, message):
        QMessageBox.information(self, 'Info', message)

    def show_error(self, message):
        QMessageBox.critical(self, 'Error', message)

    def show_client_dashboard(self, username):
        self.login_form.close()

        self.client_dashboard = QWidget(self)
        self.client_dashboard.setWindowTitle("Client Dashboard")

        layout = QVBoxLayout()

        view_balance_button = QPushButton('Баланс')
        view_balance_button.clicked.connect(lambda: self.view_balance(username))
        layout.addWidget(view_balance_button)

        transfer_button = QPushButton('Перевод денег')
        transfer_button.clicked.connect(lambda: self.transfer_money(username))
        layout.addWidget(transfer_button)

        history_button = QPushButton('Транзакции')
        history_button.clicked.connect(lambda: self.view_transaction_history(username))
        layout.addWidget(history_button)

        back_button = QPushButton('Назад')
        back_button.clicked.connect(self.show_login)
        layout.addWidget(back_button)

        self.client_dashboard.setLayout(layout)
        self.client_dashboard.show()

    def view_balance(self, username):
        self.db_cursor.execute('SELECT rub_balance, kzt_balance, usd_balance FROM users WHERE username = ?', (username,))
        result = self.db_cursor.fetchone()
        if result:
            rub, kzt, usd = result
            self.show_info(f'Баланс:\nRUB: {rub}\nKZT: {kzt}\nUSD: {usd}')

    def transfer_money(self, username):
        to_user = self.prompt_input('Введите ник получателя:')
        if to_user is None:
            return

        amount = self.prompt_input('Введите сумму:', True)
        if amount is None:
            return

        currency = self.prompt_input('Выберите валюту (rub, kzt, usd):')
        if currency is None:
            return

        self.db_cursor.execute('SELECT rub_balance, kzt_balance, usd_balance FROM users WHERE username = ?', (username,))
        user_balance = self.db_cursor.fetchone()

        if user_balance:
            balance_dict = {'rub': user_balance[0], 'kzt': user_balance[1], 'usd': user_balance[2]}
            if balance_dict.get(currency, 0) >= amount:
                try:
                    self.db_cursor.execute(f'UPDATE users SET {currency}_balance = {currency}_balance - ? WHERE username = ?', (amount, username))
                    self.db_cursor.execute(f'UPDATE users SET {currency}_balance = {currency}_balance + ? WHERE username = ?', (amount, to_user))
                    self.db_cursor.execute('INSERT INTO transfers (from_user, to_user, amount, currency) VALUES (?, ?, ?, ?)', (username, to_user, amount, currency))
                    self.db_connection.commit()
                    self.show_info(f'Transfer of {amount} {currency} to {to_user} successful')
                except sqlite3.Error as e:
                    self.show_error(f"Database error: {e}")
            else:
                self.show_error('Недостаточно средств')
        else:
            self.show_error('Неверное имя пользователя или недостаточно средств')

    def view_transaction_history(self, username=None):
        query = 'SELECT * FROM transfers'
        params = ()
        if username:
            query += ' WHERE from_user = ? OR to_user = ?'
            params = (username, username)

        self.db_cursor.execute(query, params)
        transactions = self.db_cursor.fetchall()

        if transactions:
            self.transaction_history = QWidget(self)
            self.transaction_history.setWindowTitle("Transaction History")

            layout = QVBoxLayout()

            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["ID", "From", "To", "Amount", "Currency", "Date"])
            table.setRowCount(len(transactions))

            for row, transaction in enumerate(transactions):
                for col, value in enumerate(transaction):
                    table.setItem(row, col, QTableWidgetItem(str(value)))

            layout.addWidget(table)

            back_button = QPushButton("Назад")
            back_button.clicked.connect(self.transaction_history.close)
            layout.addWidget(back_button)

            self.transaction_history.setLayout(layout)
            self.transaction_history.show()
        else:
            self.show_info('No transactions found')

    def show_login(self):
        # Проверяем, существует ли админская панель, и закрываем её, если она открыта
        if hasattr(self, 'admin_dashboard') and self.admin_dashboard is not None:
            self.admin_dashboard.close()

        # Проверяем, существует ли клиентская панель, и закрываем её, если она открыта
        if hasattr(self, 'client_dashboard') and self.client_dashboard is not None:
            self.client_dashboard.close()
    
        # Открываем форму входа
        self.login_form.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BankApp()
    window.show()
    sys.exit(app.exec())
