import re
import sqlite3
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk

import PIL
import pandas as pd
from PIL import Image, ImageTk

from model import fetch_data_from_db, prepare_data, save_model, train_and_evaluate_models
from scrap import fetch_reddit_posts, fetch_user_posts, create_tables

current_df = pd.DataFrame()



# Function to analyze trends with Machine Learning model
def analyze_trends():
    df = fetch_data_from_db()
    X_train, X_test, y_train, y_test = prepare_data(df)
    best_model, best_mse = train_and_evaluate_models(X_train, y_train, X_test, y_test)
    save_model(best_model)
    messagebox.showinfo("Trendy", f"Mean Squared Error: {best_mse}")


create_tables()


def fetch_data_1():
    subreddit = simpledialog.askstring("Input", "Proszę podać nazwę subreddita (domyślnie: 'r/popular'):", initialvalue='popular',parent=root)
    if subreddit == "":
        messagebox.showinfo("Anulowanie", "Operacja została anulowana.")
        return
    root.update()
    limit = simpledialog.askinteger("Input", "Proszę podać liczbę postów do przetworzenia (domyślnie 10):",
                                    initialvalue=10, parent=root)
    if limit is None:
        messagebox.showinfo("Anulowanie", "Operacja została anulowana.")
        return

    messagebox.showinfo("Pobieranie danych", f"Pobieranie danych z r/{subreddit} z limitem {limit} postów...")
    global current_df
    current_df = fetch_reddit_posts(subreddit, limit)
    display_data(current_df, popular_posts_tree)


def fetch_data_2():
    username = simpledialog.askstring("Input", "Proszę podać nazwę użytkownika na Reddicie:")
    if username:
        try:
            global current_df
            current_df = fetch_user_posts(username)
            display_data(current_df, user_posts_tree)
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd: {e}")


def display_data(df, tree):
    tree.delete(*tree.get_children())
    for _, row in df.iterrows():
        created_at = datetime.utcfromtimestamp(row['Created_at']).isoformat()
        tree.insert('', tk.END, values=[
            row['Title'],
            row['Score'],
            row['Subreddit'],
            row['URL'],
            row['Author'],
            row['Sentiment'],
            created_at,
            row.get('Title_length', ''),
            row.get('Hour_of_day', ''),
            row.get('Day_of_week', ''),
            row.get('Is_weekend', ''),
            row.get('Author_post_count', ''),
            row.get('Author_avg_score', ''),
            row.get('Has_media', ''),
            row.get('Comment_count', ''),
            row.get('Upvote_ratio', ''),
            row.get('Sentiment_title_interaction', '')
        ])


def test_model_code():
    def target():
        try:
            python_executable = r'.venv/Scripts/python.exe'
            subprocess.run([python_executable, "modeltest.py"], check=True)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Błąd wykonywania", f"Wystąpił błąd: {e.stderr}")
        except FileNotFoundError as e:
            messagebox.showerror("Plik nie został znaleziony", f"Wskazany plik nie został znaleziony: {e}")
        except Exception as e:
            messagebox.showerror("Błąd wykonywania", f"Wystąpił błąd: {e}")

    thread = threading.Thread(target=target)
    thread.start()


def sort_by_column(tree, col, reverse):
    columns = [c.lower() for c in tree["columns"]]
    numeric_columns = ['score', 'sentiment', 'title_length', 'hour_of_day', 'day_of_week', 'is_weekend',
                       'author_post_count', 'author_avg_score', 'comment_count', 'upvote_ratio',
                       'sentiment_title_interaction']

    col_lower = col.lower()
    is_numeric = col_lower in numeric_columns

    if col_lower not in columns:
        print(f"Kolumna '{col}' nie została znaleziona na liście kolumn.")
        return

    col_index = columns.index(col_lower)
    print(f"Sortowanie kolumny '{col}' z indeksem {col_index}. Czy jest numeryczna: {is_numeric}")

    data = []
    for item in tree.get_children():
        values = tree.item(item, 'values')
        value = values[col_index]

        if is_numeric:
            try:
                value = float(value)
            except ValueError:
                value = float('-inf')
        else:
            value = str(value).lower()

        data.append((value, item))

    data.sort(key=lambda x: x[0], reverse=reverse)

    for index, (value, item) in enumerate(data):
        tree.move(item, '', index)

    tree.heading(col, command=lambda c=col: sort_by_column(tree, c, not reverse))
    print(f"Posortowano kolumnę: '{col}' w {'malejącej' if reverse else 'rosnącej'} kolejności.")

def display_data_database(df, tree):

    tree["columns"] = []
    tree.delete(*tree.get_children())

    columns = [
        'title', 'score', 'subreddit', 'url', 'author', 'sentiment',
        'created_at', 'title_length', 'hour_of_day', 'day_of_week',
        'is_weekend', 'author_post_count', 'author_avg_score', 'has_media',
        'comment_count', 'upvote_ratio', 'sentiment_title_interaction'
    ]

    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="w")

    for _, row in df.iterrows():
        created_at = row['created_at']
        if pd.notna(created_at):
            if isinstance(created_at, str):
                created_at = pd.to_datetime(created_at, errors='coerce')
            created_at = created_at.isoformat()
        else:
            created_at = ''

        tree.insert('', tk.END, values=[
            row.get('title', ''),
            row.get('score', ''),
            row.get('subreddit', ''),
            row.get('url', ''),
            row.get('author', ''),
            row.get('sentiment', ''),
            created_at,
            row.get('title_length', ''),
            row.get('hour_of_day', ''),
            row.get('day_of_week', ''),
            row.get('is_weekend', ''),
            row.get('author_post_count', ''),
            row.get('author_avg_score', ''),
            row.get('has_media', ''),
            row.get('comment_count', ''),
            row.get('upvote_ratio', ''),
            row.get('sentiment_title_interaction', '')
        ])



def fetch_data_from_database():
    try:
        global current_df
        current_df = fetch_data_from_db()
        display_data_database(current_df, db_data_tree)
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas pobierania danych: {e}")
        print(f"Błąd: {e}")


def search_in_database():
    def select_column_and_search():
        column = column_var.get()
        search_term = search_term_var.get()

        if not search_term:
            messagebox.showwarning("Brak słowa kluczowego", "Podaj słowo kluczowe do wyszukiwania.")
            return

        if column not in df.columns:
            messagebox.showerror("Błąd", f"Kolumna '{column}' nie istnieje w DataFrame.")
            return

        try:
            # Wyszukiwanie w wybranej kolumnie
            regex_pattern = rf'\b{re.escape(search_term)}\b'
            filtered_df = df[df[column].astype(str).str.contains(regex_pattern, case=False, na=False, regex=True)]
            display_data_database(filtered_df, db_data_tree)
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyszukiwania: {e}")

    search_dialog = tk.Toplevel(root)
    search_dialog.title("Wyszukiwanie")
    search_dialog.configure(bg="#f5f5f5")
    dialog_width = 400
    dialog_height = 300
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    x = root_x + (root_width // 2) - (dialog_width // 2)
    y = root_y + (root_height // 2) - (dialog_height // 2)
    search_dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
    search_dialog.focus_set()
    search_dialog.grab_set()

    tk.Label(search_dialog, text="Wybierz kolumnę do wyszukiwania:", bg="#f5f5f5").pack(padx=10, pady=5)

    column_var = tk.StringVar()
    column_menu = tk.OptionMenu(search_dialog, column_var, *current_df.columns)
    column_menu.config(width=20, font=("Open Sans", 12), relief="solid", bg="#ffffff")
    column_menu.pack(padx=10, pady=5)

    tk.Label(search_dialog, text="Podaj słowo kluczowe do wyszukiwania:", bg="#f5f5f5").pack(padx=10, pady=5)

    search_term_var = tk.StringVar()
    search_entry = tk.Entry(search_dialog, textvariable=search_term_var, font=("Open Sans", 12))
    search_entry.pack(padx=10, pady=5)

    search_button = tk.Button(search_dialog, text="Szukaj", command=select_column_and_search, font=("Open Sans", 12),
                              bg="#4CAF50", fg="white", relief="raised")
    search_button.pack(pady=10)

    def bind_enter_to_button(widget, func):
        widget.bind("<Return>", lambda event: func())
    bind_enter_to_button(search_entry, select_column_and_search)

    search_dialog.protocol("WM_DELETE_WINDOW", search_dialog.destroy)

    try:
        df = fetch_data_from_db()
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas pobierania danych: {e}")
        return


def reset_search():
    try:
        df = fetch_data_from_db()
        display_data_database(df, db_data_tree)
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas resetowania wyszukiwania: {e}")


def create_export_button(root, df):
    def export_data():
        if current_df.empty:
            messagebox.showwarning("Brak danych", "Brak aktualnych danych do eksportu.")
            return
        else:
            available_columns = current_df.columns.tolist()
            messagebox.showinfo("Dostępne kolumny", f"Dostępne kolumny:\n{', '.join(available_columns)}")
            def convert_timestamp_to_iso(timestamp):
                if pd.notna(timestamp):
                    return datetime.utcfromtimestamp(timestamp).isoformat()
                return None
            current_df['Created_at'] = current_df['Created_at'].apply(convert_timestamp_to_iso)
            source = simpledialog.askstring("Wybór źródła danych",
                                            "Z którego źródła chcesz wyeksportować dane?\n1: Baza danych\n2: Aktualnie pobrane dane")
            if source == '1':
                df_to_export = fetch_data_from_db()
            elif source == '2':
                df_to_export = current_df
            else:
                messagebox.showerror("Błąd", "Nieprawidłowy wybór źródła danych.")
                return
        def on_export_format_choice():
            selected_format = format_var.get()
            if selected_format == 'csv':
                file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                         filetypes=[("CSV files", "*.csv")])
                if file_path:
                    df_to_export.to_csv(file_path, index=False)
                    messagebox.showinfo("Eksport", f"Dane zostały wyeksportowane do pliku {file_path}.")
            elif selected_format == 'excel':
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                         filetypes=[("Excel files", "*.xlsx")])
                if file_path:
                    df_to_export.to_excel(file_path, index=False)
                    messagebox.showinfo("Eksport", f"Dane zostały wyeksportowane do pliku {file_path}.")
            elif selected_format == 'json':
                file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                         filetypes=[("JSON files", "*.json")])
                if file_path:
                    df_to_export.to_json(file_path, orient='records', lines=True)
                    messagebox.showinfo("Eksport", f"Dane zostały wyeksportowane do pliku {file_path}.")
            elif selected_format == 'tsv':
                file_path = filedialog.asksaveasfilename(defaultextension=".tsv",
                                                         filetypes=[("TSV files", "*.tsv")])
                if file_path:
                    df_to_export.to_csv(file_path, sep='\t', index=False)
                    messagebox.showinfo("Eksport", f"Dane zostały wyeksportowane do pliku {file_path}.")
            else:
                messagebox.showerror("Błąd", "Nieobsługiwany format pliku.")
            export_window.destroy()

        export_window = tk.Toplevel(root)
        export_window.title("Wybór formatu pliku")
        export_window.configure(bg="#f5f5f5")
        tk.Label(export_window, text="Wybierz format pliku do eksportu:").pack(padx=10, pady=10)

        format_var = tk.StringVar(value='csv')  # Ustawienie domyślnego formatu na 'csv'
        formats = ['csv', 'excel', 'json', 'tsv']
        format_menu = tk.OptionMenu(export_window, format_var, *formats)
        format_menu.config(
            width=15,  # Szerokość menu
            font=("Open Sans", 12),  # Font menu
            relief="solid",  # Obramowanie
            bg="#ffffff",  # Tło menu
            anchor="w"  # Wyrównanie tekstu
        )
        format_menu["menu"].config(
            font=("Open Sans", 12),  # Font opcji menu
            bg="#ffffff"  # Tło opcji
        )
        format_menu.pack(padx=10, pady=10)

        tk.Button(export_window, text="Eksportuj", command=on_export_format_choice, font=("Open Sans", 12),
                  bg="#4CAF50", fg="white", relief="raised").pack(pady=10)

    return export_data

def on_exit():
    result = messagebox.askquestion("Potwierdź wyjście", "Czy na pewno chcesz wyjść z aplikacji?")
    if result == "yes":
        root.quit()
#def toggle_dark_mode():

def load_database():
    global current_df
    # Otwórz dialog do wyboru pliku bazy danych
    file_path = filedialog.askopenfilename(title="Wybierz plik bazy danych",
                                           filetypes=[("Pliki SQLite", "*.sqlite;*.db")])

    # Sprawdź, czy wybrano plik
    if not file_path:
        return  # Anulowano wybór pliku, nie robimy nic

    try:
        # Połącz się z bazą danych
        connection = sqlite3.connect(file_path)
        cursor = connection.cursor()

        # Pobierz listę tabel w bazie danych
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Sprawdź, czy są jakieś tabele
        if not tables:
            messagebox.showerror("Błąd", "Brak tabel w wybranej bazie danych.")
            return

        # Przekonwertuj listę tabel na prostą listę stringów
        table_names = [table[0] for table in tables]

        selected_table = None
        while not selected_table or selected_table not in table_names:
            selected_table = simpledialog.askstring("Wybór tabeli", "Wybierz tabelę do wczytania danych:",
                                                    initialvalue=table_names[0], parent=root)

            if selected_table is None:
                # Jeśli użytkownik naciśnie "Anuluj" lub zamknie okno dialogowe, przerywamy działanie
                return
            elif selected_table not in table_names:
                messagebox.showinfo("Informacja", "Nie wybrano prawidłowej tabeli. Proszę spróbować ponownie.")

        # Wczytaj dane z wybranej tabeli
        cursor.execute(f"SELECT * FROM {selected_table}")
        data = cursor.fetchall()  # Zapisz dane jako listę krotek
        columns = [description[0] for description in cursor.description]  # Pobierz nazwy kolumn

        connection.close()

        # Konwersja danych do DataFrame
        current_df = pd.DataFrame(data, columns=columns)

        # Wyświetl dane w zakładce "Baza danych"
        display_data_in_tab(current_df.values.tolist(), columns)
        notebook.select(database_frame)

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił problem podczas wczytywania bazy danych: {e}")




def display_data_in_tab(data, columns):
    # Usuń wszystkie istniejące dane w drzewie (jeśli są)
    for item in db_data_tree.get_children():
        db_data_tree.delete(item)

    # Ustaw nagłówki kolumn
    db_data_tree["columns"] = columns
    for col in columns:
        db_data_tree.heading(col, text=col)
        db_data_tree.column(col, width=100, anchor=tk.W)

    # Dodaj wiersze danych
    for row in data:
        db_data_tree.insert("", "end", values=row)

root = tk.Tk()
root.title("Aplikacja do analizy danych z Reddita")
root.geometry("1200x800")
root.configure(bg="#f5f5f5")

style = ttk.Style()
style.configure('TLabel', font=('Open Sans', 12), background="#f5f5f5")
style.configure('TNotebook.Tab', font=('Open Sans', 12, 'bold'))
style.configure('Treeview.Heading', font=('Open Sans', 10, 'bold'), background="#f5f5f5")
style.configure('Treeview', font=('Open Sans', 10), rowheight=25)

# Pasek menu
menu_bar = tk.Menu(root)

#Menu Plik
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Nowy")
file_menu.add_command(label="Otwórz")
file_menu.add_command(label="Wczytaj bazę danych", command=load_database)
file_menu.add_command(label="Zapisz")
file_menu.add_separator()
file_menu.add_command(label="Wyjście", command=root.quit)
menu_bar.add_cascade(label="Plik", menu=file_menu)
root.config(menu=menu_bar)

# Menu Edycja
edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Cofnij")
edit_menu.add_command(label="Ponów")
edit_menu.add_separator()
edit_menu.add_command(label="Wytnij")
edit_menu.add_command(label="Kopiuj")
edit_menu.add_command(label="Wklej")
menu_bar.add_cascade(label="Edycja", menu=edit_menu)

# Menu Widok
view_menu = tk.Menu(menu_bar, tearoff=0)
#view_menu.add_command(label="Ciemny tryb", command=toggle_dark_mode)
menu_bar.add_cascade(label="Widok", menu=view_menu)

# Function to display the help information
def show_about_info():
    about_window = tk.Toplevel(root)
    about_window.title("O Programie")
    about_window.geometry("400x150")
    about_window.configure(bg="#2b2b2b")  # Dark background for the about window

    # Adding text to the about window
    about_text = tk.Label(about_window, text="Stworzone przez Adama Wandelta\nUniwersytet Przyrodniczy w Poznaniu",
                          font=("Open Sans", 12), bg="#2b2b2b", fg="#e0e0e0", justify=tk.CENTER)
    about_text.pack(padx=20, pady=20)

    # Adding a button to close the about window
    close_button = tk.Button(about_window, text="Zamknij", command=about_window.destroy,
                             font=("Open Sans", 12), bg="#4CAF50", fg="white", relief="raised")
    close_button.pack(pady=10)

# Menu Pomoc
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="O programie", command=show_about_info)
menu_bar.add_cascade(label="Pomoc", menu=help_menu)

root.config(menu=menu_bar)

# Logo Frame
frame_logo = tk.Frame(root, bg="#f5f5f5")
frame_logo.pack(side=tk.TOP, pady=20)

logo_image = Image.open("img/logo_up.png")
max_size = (500, 500)
aspect_ratio = min(max_size[0] / logo_image.width, max_size[1] / logo_image.height)
new_size = (int(logo_image.width * aspect_ratio), int(logo_image.height * aspect_ratio))
logo_image_resized = logo_image.resize(new_size, PIL.Image.Resampling.LANCZOS)

logo_photo = ImageTk.PhotoImage(logo_image_resized)
# noinspection PyTypeChecker
logo_label = tk.Label(frame_logo, image=logo_photo, bg="#f5f5f5")
logo_label.pack()

header_label = ttk.Label(root, text="Aplikacja do Analizy Danych z serwisu Reddit", font=("Open Sans", 24, "bold"))
header_label.pack(pady=20)

main_frame = tk.Frame(root, bg="#f5f5f5")
main_frame.pack(fill=tk.BOTH, expand=True)

side_frame = tk.Frame(main_frame, bg="#333333", width=200)
side_frame.pack(side=tk.LEFT, fill=tk.Y)

buttons_frame = tk.Frame(side_frame, bg="#333333")
buttons_frame.pack(pady=20, side=tk.LEFT)

button1 = tk.Button(buttons_frame, text="Pobierz posty z Subreddita", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=fetch_data_1)
button1.pack(fill=tk.X, pady=10)

button2 = tk.Button(buttons_frame, text="Pobierz posty użytkownika", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=fetch_data_2)
button2.pack(fill=tk.X, pady=10)

button3 = tk.Button(buttons_frame, text="Pokaż porównanie modeli", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=test_model_code)
button3.pack(fill=tk.X, pady=10)

button4 = tk.Button(buttons_frame, text="Wytrenuj model", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=analyze_trends)
button4.pack(fill=tk.X, pady=10)

export_button = tk.Button(buttons_frame, text="Eksportuj dane", font=("Open Sans", 14), bg="#666666",
                          fg="white", command=create_export_button(root, current_df))
export_button.pack(fill=tk.X, pady=10)

notebook = ttk.Notebook(main_frame)
notebook.pack(fill=tk.BOTH, expand=True)

popular_posts_frame = ttk.Frame(notebook)
user_posts_frame = ttk.Frame(notebook)
database_frame = ttk.Frame(notebook)

notebook.add(popular_posts_frame, text="Posty z Subreddita")
notebook.add(user_posts_frame, text="Posty użytkownika")
notebook.add(database_frame, text="Baza danych")

popular_posts_tree = ttk.Treeview(popular_posts_frame, columns=(
    'Title', 'Score', 'Subreddit', 'URL', 'Author', 'Sentiment', 'Created_at',
    'Title_length', 'Hour_of_day', 'Day_of_week', 'Is_weekend', 'Author_post_count', 'Author_avg_score',
    'Has_media', 'Comment_count', 'Upvote_ratio', 'Sentiment_title_interaction'),
                                  show='headings', selectmode='browse')

v_scroll_popular = tk.Scrollbar(popular_posts_frame, orient="vertical", command=popular_posts_tree.yview)
v_scroll_popular.pack(side="right", fill="y")
popular_posts_tree.configure(yscrollcommand=v_scroll_popular.set)

h_scroll_popular = tk.Scrollbar(popular_posts_frame, orient="horizontal", command=popular_posts_tree.xview)
h_scroll_popular.pack(side="bottom", fill="x")
popular_posts_tree.configure(xscrollcommand=h_scroll_popular.set)

for col in popular_posts_tree["columns"]:
    popular_posts_tree.heading(col, text=col, command=lambda c=col: sort_by_column(popular_posts_tree, c, False))
    popular_posts_tree.column(col, anchor=tk.W)

popular_posts_tree.pack(fill=tk.BOTH, expand=True)

user_posts_tree = ttk.Treeview(user_posts_frame, columns=(
    'Title', 'Score', 'Subreddit', 'URL', 'Author', 'Sentiment', 'Created_at',
    'Title_length', 'Hour_of_day', 'Day_of_week', 'Is_weekend', 'Author_post_count', 'Author_avg_score',
    'Has_media', 'Comment_count', 'Upvote_ratio', 'Sentiment_title_interaction'),
                               show='headings', selectmode='browse')

# Dodanie pionowego paska przewijania
v_scroll_user = tk.Scrollbar(user_posts_frame, orient="vertical", command=user_posts_tree.yview)
v_scroll_user.pack(side="right", fill="y")
user_posts_tree.configure(yscrollcommand=v_scroll_user.set)

# Dodanie poziomego paska przewijania
h_scroll_user = tk.Scrollbar(user_posts_frame, orient="horizontal", command=user_posts_tree.xview)
h_scroll_user.pack(side="bottom", fill="x")
user_posts_tree.configure(xscrollcommand=h_scroll_user.set)

for col in user_posts_tree["columns"]:
    user_posts_tree.heading(col, text=col, command=lambda c=col: sort_by_column(user_posts_tree, c, False))
    user_posts_tree.column(col, anchor=tk.W)

user_posts_tree.pack(fill=tk.BOTH, expand=True)

db_data_tree = ttk.Treeview(database_frame, columns=(
    'title', 'score', 'subreddit', 'url', 'author', 'sentiment', 'created_at',
    'title_length', 'hour_of_day', 'day_of_week', 'is_weekend', 'author_post_count', 'author_avg_score',
    'has_media', 'comment_count', 'upvote_ratio', 'sentiment_title_interaction'),
                            show='headings', selectmode='browse')

# Dodanie pionowego paska przewijania
v_scroll_db = tk.Scrollbar(database_frame, orient="vertical", command=db_data_tree.yview)
v_scroll_db.pack(side="right", fill="y")
db_data_tree.configure(yscrollcommand=v_scroll_db.set)

# Dodanie poziomego paska przewijania
h_scroll_db = tk.Scrollbar(database_frame, orient="horizontal", command=db_data_tree.xview)
h_scroll_db.pack(side="bottom", fill="x")
db_data_tree.configure(xscrollcommand=h_scroll_db.set)

for col in db_data_tree["columns"]:
    db_data_tree.heading(col, text=col, command=lambda c=col: sort_by_column(db_data_tree, c, False))
    db_data_tree.column(col, anchor=tk.W)

db_data_tree.pack(fill=tk.BOTH, expand=True)

database_buttons_frame = tk.Frame(database_frame)
database_buttons_frame.pack(pady=10)

# Stylowanie przycisków
button_style = {
    'font': ("Open Sans", 14),
    'bg': "#4CAF50",  # Kolor tła przycisków
    'fg': "white",  # Kolor tekstu
    'relief': "raised",  # Efekt obramowania
    'padx': 15,  # Wewnętrzny odstęp poziomy
    'pady': 10,  # Wewnętrzny odstęp pionowy
    'bd': 2  # Grubość obramowania
}

# Przycisk Pobierz dane z bazy
fetch_db_button = tk.Button(database_buttons_frame, text="Pobierz dane z bazy", **button_style,
                            command=fetch_data_from_database)
fetch_db_button.pack(side=tk.LEFT, padx=10)

# Przycisk Wyszukaj w bazie
search_db_button = tk.Button(database_buttons_frame, text="Wyszukaj w bazie", **button_style,
                             command=search_in_database)
search_db_button.pack(side=tk.LEFT, padx=10)

# Przycisk Resetuj wyszukiwanie
reset_search_button = tk.Button(database_buttons_frame, text="Resetuj wyszukiwanie", **button_style,
                                command=reset_search)
reset_search_button.pack(side=tk.LEFT, padx=10)
root.mainloop()
