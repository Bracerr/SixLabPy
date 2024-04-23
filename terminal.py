import subprocess


# Функция для выполнения команды
def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except Exception as e:
        print("Error:", e)


# Словарь с командами
commands = {
    '1': 'chmod',
    '2': 'chown',
    '3': 'passwd',
    '4': 'sudo',
    '5': 'iptables',
    '6': 'fail2ban',
    '7': 'AppArmor',
    '8': 'SELinux',
    '9': 'auditd',
    '10': 'ufw'
}

# Отображение списка команд
print("Выберите команду:")
for key, value in commands.items():
    print(key + ": " + value)

# Получение выбора пользователя
while True:
    user_choice = input("Введите номер команды (или 'exit' для выхода): ")
    if user_choice.lower() == 'exit':
        break
    elif user_choice in commands:
        command_to_run = commands[user_choice]
        if command_to_run in ['iptables', 'fail2ban', 'AppArmor', 'SELinux', 'auditd', 'ufw']:
            command_to_run = "man " + command_to_run  # Добавление "man" для вывода справки
        run_command(command_to_run)
    else:
        print("Неверный ввод. Пожалуйста, введите номер команды из списка.")
