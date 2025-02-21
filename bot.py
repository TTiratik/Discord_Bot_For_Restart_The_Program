import nextcord
from nextcord.ext import commands
import subprocess
import mysql.connector
import os


SERVER_DIR = "path/to/ragemp-server-directory" #directory of your file
SERVER_EXE = "ragemp-server.exe"  # name of your file

db_config = {
    'host': 'yourjost',
    'user': 'youruser',
    'password': 'yourpass',
    'database': 'yourDatabase'
}


server_process = None


def connect_to_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Ошибка подключения к базе данных: {err}")
        return None


def get_all_tables(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables


def search_in_all_tables(conn, search_term):
    tables = get_all_tables(conn)
    results = []

    for table in tables:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"SHOW COLUMNS FROM log_entity")
        columns = [column['Field'] for column in cursor.fetchall()]

     
        query = f"SELECT * FROM log_entity WHERE "
        query += " OR ".join([f"{column} = %s" for column in columns])
        cursor.execute(query, (search_term,) * len(columns))

    
        table_results = cursor.fetchall()
        if table_results:
            results.append((table, table_results))

        cursor.close()

    return results


intents = nextcord.Intents.default()
intents.message_content = True  


bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')


@bot.slash_command(name="start", description="Запустить сервер RAGE MP")
async def start(interaction: nextcord.Interaction):
    global server_process
    if server_process is not None:
        await interaction.response.send_message("Сервер уже запущен.")
        return
    
    try:

        server_process = subprocess.Popen(
            [os.path.join(SERVER_DIR, SERVER_EXE)],  # Полный путь к файлу
            cwd=SERVER_DIR,  # Рабочая директория
            creationflags=subprocess.CREATE_NEW_CONSOLE  # Новое окно консоли
        )
        await interaction.response.send_message("Сервер успешно запущен.")
    except Exception as e:
        await interaction.response.send_message(f"Ошибка при запуске сервера: {e}")


@bot.slash_command(name="stop", description="Остановить сервер RAGE MP")
async def stop(interaction: nextcord.Interaction):
    global server_process
    if server_process is None:
        await interaction.response.send_message("Сервер не запущен.")
        return
    
    try:
        server_process.terminate()
        server_process = None
        await interaction.response.send_message("Сервер успешно остановлен.")
    except Exception as e:
        await interaction.response.send_message(f"Ошибка при остановке сервера: {e}")


@bot.slash_command(name="restart", description="Перезапустить сервер RAGE MP")
async def restart(interaction: nextcord.Interaction):
    global server_process
    if server_process is not None:
        try:
            server_process.terminate()
            server_process = None
            await interaction.response.send_message("Сервер успешно остановлен.")
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при остановке сервера: {e}")
            return
    
    try:
      
        server_process = subprocess.Popen(
            [os.path.join(SERVER_DIR, SERVER_EXE)],  # Полный путь к файлу
            cwd=SERVER_DIR,  # Рабочая директория
            creationflags=subprocess.CREATE_NEW_CONSOLE  # Новое окно консоли
        )
        await interaction.response.send_message("Сервер успешно перезапущен.")
    except Exception as e:
        await interaction.response.send_message(f"Ошибка при запуске сервера: {e}")


@bot.slash_command(name="setup", description="Команда для настройки")
async def setup(interaction: nextcord.Interaction):
    await interaction.response.send_message("Hoffman on top")


@bot.slash_command(name="findplayer", description="Поиск игрока в базе данных")
async def find_player(interaction: nextcord.Interaction, arg1: str):
    conn = connect_to_db()
    if conn is None:
        await interaction.response.send_message("Ошибка подключения к базе данных.")
        return


    results = search_in_all_tables(conn, arg1)

    if results:
        for table_name, table_results in results:
            response = f"**Результаты из таблицы {table_name}:**\n"
            for row in table_results:
                response += ", ".join([f"{key}: {value}" for key, value in row.items()]) + "\n"
            await interaction.followup.send(response)  # Отправляем результаты
    else:
        await interaction.followup.send("Совпадений не найдено.")

    conn.close()


bot.run('your bot token')