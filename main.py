import re
import sqlite3
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk

import pandas as pd
from PIL import Image, ImageTk

from model import fetch_data_from_db, prepare_data, save_model, train_and_evaluate_models
from scrap import fetch_reddit_posts, fetch_user_posts, create_tables

current_df = pd.DataFrame()


def analyze_trends():
    df = fetch_data_from_db()
    X_train, X_test, y_train, y_test = prepare_data(df)
    best_model_name, best_model, best_mse = train_and_evaluate_models(X_train, y_train, X_test, y_test)
    save_model(best_model)
    messagebox.showinfo("Trendy", f"Mean Squared Error: {best_mse}")


create_tables()


def fetch_data_1():
    subreddit = simpledialog.askstring("Input", "Proszę podać nazwę subreddita (domyślnie: 'r/popular'):",
                                       initialvalue='popular', parent=root)
    if subreddit == "":
        messagebox.showinfo("Anulowanie", "Operacja została anulowana.")
        return
    root.update()
    limit = simpledialog.askinteger("Input", "Proszę podać liczbę postów do przetworzenia (domyślnie 10):",
                                    initialvalue=10, parent=root)
    if limit is None:
        messagebox.showinfo("Anulowanie", "Operacja została anulowana.")
        return

    post_type = simpledialog.askstring("Input",
                                       "Proszę podać typ postów (new, hot, top, controversial) (domyślnie: 'hot'):",
                                       initialvalue='hot', parent=root)
    if post_type == "":
        messagebox.showinfo("Błąd", "Nieprawidłowy typ postów. Wybierz spośród 'new', 'hot', 'top', 'controversial'.")
        return
    root.update()

    messagebox.showinfo("Pobieranie danych", f"Pobieranie danych z r/{subreddit} z limitem {limit} postów...")
    global current_df
    current_df = fetch_reddit_posts(subreddit, limit, post_type)
    display_data(current_df, posts_tree)


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

    col_lower = col.lower()
    if col_lower not in columns:
        print(f"Kolumna '{col}' nie została znaleziona na liście kolumn.")
        return

    col_index = columns.index(col_lower)
    print(f"Sortowanie kolumny '{col}' z indeksem {col_index}.")

    values = [tree.item(item, 'values')[col_index] for item in tree.get_children()]
    is_numeric = True

    for value in values:
        try:
            float(value)
        except (ValueError, TypeError):
            is_numeric = False
            break
    print(f"Kolumna '{col}' jest {'numeryczna' if is_numeric else 'tekstowa'}.")

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
        tree.heading(col, text=col, command=lambda c=col: sort_by_column(db_data_tree, c, False))
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

            regex_pattern = rf'\b{re.escape(search_term)}\b'
            filtered_df = df[df[column].astype(str).str.contains(regex_pattern, case=False, na=False, regex=True)]
            display_data_database(filtered_df, db_data_tree)
        except Exception as e:
            messagebox.showerror("Błąd", f"Wystąpił błąd podczas wyszukiwania: {e}")

    if current_df is None or current_df.empty:
        messagebox.showwarning("Brak danych",
                               "Brak załadowanej bazy danych. Proszę załadować dane przed wyszukiwaniem.")
        return
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
            def convert_timestamp_to_iso(timestamp):
                if pd.notna(timestamp):
                    return datetime.utcfromtimestamp(timestamp).isoformat()
                return None

            source = simpledialog.askstring("Wybór źródła danych",
                                            "Z którego źródła chcesz wyeksportować dane?\n1: Baza danych\n2: Aktualnie pobrane dane")
            if source == '1':
                df_to_export = fetch_data_from_db()
            elif source == '2':
                current_df.columns = current_df.columns.str.lower()
                if 'created_at' in current_df.columns:
                    current_df['created_at'] = current_df['created_at'].apply(
                        lambda x: convert_timestamp_to_iso(x) if not isinstance(x, str) or not re.match(
                            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', x) else x
                    )
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

        format_var = tk.StringVar(value='csv')
        formats = ['csv', 'excel', 'json', 'tsv']
        format_menu = tk.OptionMenu(export_window, format_var, *formats)
        format_menu.config(
            width=15,
            font=("Open Sans", 12),
            relief="solid",
            bg="#ffffff",
            anchor="w"
        )
        format_menu["menu"].config(
            font=("Open Sans", 12),
            bg="#ffffff"
        )
        format_menu.pack(padx=10, pady=10)

        tk.Button(export_window, text="Eksportuj", command=on_export_format_choice, font=("Open Sans", 12),
                  bg="#4CAF50", fg="white", relief="raised").pack(pady=10)

    return export_data


def on_exit():
    result = messagebox.askquestion("Potwierdź wyjście", "Czy na pewno chcesz wyjść z aplikacji?")
    if result == "yes":
        root.quit()


def load_database():
    global current_df

    file_path = filedialog.askopenfilename(title="Wybierz plik bazy danych",
                                           filetypes=[("Pliki SQLite", "*.sqlite;*.db")])

    if not file_path:
        return

    try:

        connection = sqlite3.connect(file_path)
        cursor = connection.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            messagebox.showerror("Błąd", "Brak tabel w wybranej bazie danych.")
            return

        table_names = [table[0] for table in tables]

        selected_table = None
        while not selected_table or selected_table not in table_names:
            selected_table = simpledialog.askstring("Wybór tabeli", "Wybierz tabelę do wczytania danych:",
                                                    initialvalue=table_names[0], parent=root)

            if selected_table is None:

                return
            elif selected_table not in table_names:
                messagebox.showinfo("Informacja", "Nie wybrano prawidłowej tabeli. Proszę spróbować ponownie.")

        cursor.execute(f"SELECT * FROM {selected_table}")
        data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        connection.close()

        current_df = pd.DataFrame(data, columns=columns)

        display_data_in_tab(current_df.values.tolist(), columns)
        notebook.select(database_frame)

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił problem podczas wczytywania bazy danych: {e}")


def display_data_in_tab(data, columns):
    for item in db_data_tree.get_children():
        db_data_tree.delete(item)

    db_data_tree["columns"] = columns
    for col in columns:
        db_data_tree.heading(col, text=col, command=lambda c=col: sort_by_column(db_data_tree, c, False))
        db_data_tree.column(col, width=100, anchor=tk.W)

    for row in data:
        db_data_tree.insert("", "end", values=row)


def save_to_db():
    global current_df

    file_path = filedialog.asksaveasfilename(defaultextension=".db",
                                             filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")])
    if not file_path:
        return

    while True:
        table_name = simpledialog.askstring("Nazwa tabeli", "Wprowadź nazwę tabeli do zapisania:")

        if table_name:
            break
        else:
            messagebox.showwarning("Ostrzeżenie", "Nie wprowadzono nazwy tabeli. Proszę spróbować ponownie.")

    try:

        conn = sqlite3.connect(file_path)

        current_df.to_sql(table_name, conn, if_exists='replace', index=False)

        conn.close()

        messagebox.showinfo("Zapisz", "Baza danych została pomyślnie zapisana!")

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił problem podczas zapisywania bazy danych: {e}")


root = tk.Tk()
root.title("Aplikacja do analizy danych z Reddita")
root.geometry("1200x800")
root.configure(bg="#f5f5f5")

style = ttk.Style()
style.configure('TLabel', font=('Open Sans', 12), background="#f5f5f5")
style.configure('TNotebook.Tab', font=('Open Sans', 12, 'bold'))
style.configure('Treeview.Heading', font=('Open Sans', 10, 'bold'), background="#f5f5f5")
style.configure('Treeview', font=('Open Sans', 10), rowheight=25)

menu_bar = tk.Menu(root)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Wczytaj bazę danych", command=load_database)
file_menu.add_command(label="Zapisz bazę danych", command=save_to_db)
file_menu.add_separator()
file_menu.add_command(label="Wyjście", command=root.quit)
menu_bar.add_cascade(label="Plik", menu=file_menu)
root.config(menu=menu_bar)


def on_tree_click(event):
    global selected_index, active_tree
    active_tree = event.widget
    selected_item = active_tree.focus()
    selected_index = active_tree.index(selected_item)


def copy_record():
    if selected_index is not None and active_tree is not None:

        item = active_tree.get_children()[selected_index]
        copied_record = active_tree.item(item, "values")

        copied_text = '\t'.join(map(str, copied_record))

        root.clipboard_clear()
        root.clipboard_append(copied_text)
        messagebox.showinfo("Kopiowanie", f"Rekord został skopiowany do schowka:\n{copied_text}")
    else:
        messagebox.showwarning("Brak wyboru", "Nie wybrano rekordu do skopiowania.")


def undo_copy():
    root.clipboard_clear()
    root.clipboard_append("")

    messagebox.showinfo("Cofnięto", "Schowek został wyczyszczony.")


edit_menu = tk.Menu(menu_bar, tearoff=0)
edit_menu.add_command(label="Cofnij", command=undo_copy)
edit_menu.add_command(label="Kopiuj", command=copy_record)
menu_bar.add_cascade(label="Edycja", menu=edit_menu)


def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))


def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)


def toggle_sidebar(event=None):
    if side_frame.winfo_ismapped():
        side_frame.grid_forget()
    else:
        side_frame.grid(row=0, column=0, sticky="ns", rowspan=2)


view_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Widok", menu=view_menu)
view_menu.add_command(label="Tryb pełnoekranowy (F11)", command=toggle_fullscreen)
view_menu.add_command(label="Pokaż/Ukryj pasek boczny (F2)", command=toggle_sidebar)


def show_about_info():
    about_window = tk.Toplevel(root)
    about_window.title("O programie")
    about_window.geometry("400x150")
    about_window.configure(bg="#2b2b2b")
    about_window.focus()

    screen_width = about_window.winfo_screenwidth()
    screen_height = about_window.winfo_screenheight()

    x = (screen_width // 2) - (400 // 2)
    y = (screen_height // 2) - (150 // 2)

    about_window.geometry(f'{400}x{150}+{x}+{y}')
    about_text = tk.Label(about_window, text="Stworzone przez Adama Wandelta\nUniwersytet Przyrodniczy w Poznaniu",
                          font=("Open Sans", 12), bg="#2b2b2b", fg="#e0e0e0", justify=tk.CENTER)
    about_text.pack(padx=20, pady=20)

    close_button = tk.Button(about_window, text="Zamknij", command=about_window.destroy,
                             font=("Open Sans", 12), bg="#4CAF50", fg="white", relief="raised")
    close_button.pack(pady=10)


help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="O programie", command=show_about_info)
menu_bar.add_cascade(label="Pomoc", menu=help_menu)

root.config(menu=menu_bar)

original_column_widths = {}


def distribute_columns_evenly(tree):
    global original_column_widths

    if tree not in original_column_widths:
        original_column_widths[tree] = {col: tree.column(col, width=None) for col in tree["columns"]}

        total_width = tree.winfo_width()
        num_columns = len(tree["columns"])
        column_width = int(total_width / num_columns)

        for col in tree["columns"]:
            tree.column(col, width=column_width)

    else:
        for col, width in original_column_widths[tree].items():
            tree.column(col, width=width)

        del original_column_widths[tree]


frame_logo = tk.Frame(root, bg="#f5f5f5")
frame_logo.grid(row=0, column=0, padx=20, pady=20, sticky="n")

logo_image = Image.open("img/logo_up.png")
max_size = (500, 500)
aspect_ratio = min(max_size[0] / logo_image.width, max_size[1] / logo_image.height)
new_size = (int(logo_image.width * aspect_ratio), int(logo_image.height * aspect_ratio))
logo_image_resized = logo_image.resize(new_size, Image.Resampling.LANCZOS)
logo_photo = ImageTk.PhotoImage(logo_image_resized)

# noinspection PyTypeChecker
logo_label = tk.Label(frame_logo, image=logo_photo, bg="#f5f5f5")
logo_label.grid(row=0, column=0)

header_label = ttk.Label(root, text="Aplikacja do Analizy Danych z serwisu Reddit", font=("Open Sans", 24, "bold"))
header_label.grid(row=1, column=0, pady=20, sticky="n")

main_frame = tk.Frame(root, bg="#f5f5f5")
main_frame.grid(row=2, column=0, sticky="nsew")

side_frame = tk.Frame(main_frame, bg="#333333", width=200)
side_frame.grid(row=0, column=0, sticky="ns", rowspan=2)
side_frame.grid_rowconfigure(0, weight=1)
side_frame.grid_columnconfigure(0, weight=1)

buttons_frame = tk.Frame(side_frame, bg="#333333")
buttons_frame.grid(row=0, column=0, padx=10, pady=20, sticky="nsew")
buttons_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
buttons_frame.grid_columnconfigure(0, weight=1)

button1 = tk.Button(buttons_frame, text="Pobierz posty z Subreddita", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=fetch_data_1)
button1.grid(row=0, column=0, padx=5, pady=10, sticky="ew")

button2 = tk.Button(buttons_frame, text="Pobierz posty użytkownika", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=fetch_data_2)
button2.grid(row=1, column=0, padx=5, pady=10, sticky="ew")

button3 = tk.Button(buttons_frame, text="Pokaż porównanie modeli", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=test_model_code)
button3.grid(row=2, column=0, padx=5, pady=10, sticky="ew")

button4 = tk.Button(buttons_frame, text="Wytrenuj model", font=("Open Sans", 14), bg="#666666",
                    fg="white", command=analyze_trends)
button4.grid(row=3, column=0, padx=5, pady=10, sticky="ew")

export_button = tk.Button(buttons_frame, text="Eksportuj dane", font=("Open Sans", 14), bg="#666666",
                          fg="white", command=create_export_button(root, current_df))
export_button.grid(row=4, column=0, padx=5, pady=10, sticky="ew")

notebook = ttk.Notebook(main_frame)
notebook.grid(row=0, column=1, sticky="nsew")

popular_posts_frame = ttk.Frame(notebook)
user_posts_frame = ttk.Frame(notebook)
database_frame = ttk.Frame(notebook)

notebook.add(popular_posts_frame, text="Posty z Subreddita")
notebook.add(user_posts_frame, text="Posty użytkownika")
notebook.add(database_frame, text="Baza danych")

posts_tree = ttk.Treeview(popular_posts_frame, columns=(
    'Title', 'Score', 'Subreddit', 'URL', 'Author', 'Sentiment', 'Created_at',
    'Title_length', 'Hour_of_day', 'Day_of_week', 'Is_weekend', 'Author_post_count', 'Author_avg_score',
    'Has_media', 'Comment_count', 'Upvote_ratio', 'Sentiment_title_interaction'),
                          show='headings', selectmode='browse')

v_scroll_popular = tk.Scrollbar(popular_posts_frame, orient="vertical", command=posts_tree.yview)
v_scroll_popular.grid(row=0, column=1, sticky="ns")
posts_tree.configure(yscrollcommand=v_scroll_popular.set)

h_scroll_popular = tk.Scrollbar(popular_posts_frame, orient="horizontal", command=posts_tree.xview)
h_scroll_popular.grid(row=1, column=0, sticky="ew")
posts_tree.configure(xscrollcommand=h_scroll_popular.set)

for col in posts_tree["columns"]:
    posts_tree.heading(col, text=col, command=lambda c=col: sort_by_column(posts_tree, c, False))
    posts_tree.column(col, anchor=tk.W)

posts_tree.grid(row=0, column=0, sticky="nsew")

user_posts_tree = ttk.Treeview(user_posts_frame, columns=(
    'Title', 'Score', 'Subreddit', 'URL', 'Author', 'Sentiment', 'Created_at',
    'Title_length', 'Hour_of_day', 'Day_of_week', 'Is_weekend', 'Author_post_count', 'Author_avg_score',
    'Has_media', 'Comment_count', 'Upvote_ratio', 'Sentiment_title_interaction'),
                               show='headings', selectmode='browse')

v_scroll_user = tk.Scrollbar(user_posts_frame, orient="vertical", command=user_posts_tree.yview)
v_scroll_user.grid(row=0, column=1, sticky="ns")
user_posts_tree.configure(yscrollcommand=v_scroll_user.set)

h_scroll_user = tk.Scrollbar(user_posts_frame, orient="horizontal", command=user_posts_tree.xview)
h_scroll_user.grid(row=1, column=0, sticky="ew")
user_posts_tree.configure(xscrollcommand=h_scroll_user.set)

for col in user_posts_tree["columns"]:
    user_posts_tree.heading(col, text=col, command=lambda c=col: sort_by_column(user_posts_tree, c, False))
    user_posts_tree.column(col, anchor=tk.W)

user_posts_tree.grid(row=0, column=0, sticky="nsew")

db_data_tree = ttk.Treeview(database_frame, columns=(
    'title', 'score', 'subreddit', 'url', 'author', 'sentiment', 'created_at',
    'title_length', 'hour_of_day', 'day_of_week', 'is_weekend', 'author_post_count', 'author_avg_score',
    'has_media', 'comment_count', 'upvote_ratio', 'sentiment_title_interaction'),
                            show='headings', selectmode='browse')

v_scroll_db = tk.Scrollbar(database_frame, orient="vertical", command=db_data_tree.yview)
v_scroll_db.grid(row=0, column=1, sticky="ns")
db_data_tree.configure(yscrollcommand=v_scroll_db.set)

h_scroll_db = tk.Scrollbar(database_frame, orient="horizontal", command=db_data_tree.xview)
h_scroll_db.grid(row=1, column=0, sticky="ew")
db_data_tree.configure(xscrollcommand=h_scroll_db.set)

for col in db_data_tree["columns"]:
    db_data_tree.heading(col, text=col, command=lambda c=col: sort_by_column(db_data_tree, c, False))
    db_data_tree.column(col, anchor=tk.W)

db_data_tree.grid(row=0, column=0, sticky="nsew")
posts_tree.bind("<ButtonRelease-1>", on_tree_click)
user_posts_tree.bind("<ButtonRelease-1>", on_tree_click)
db_data_tree.bind("<ButtonRelease-1>", on_tree_click)

root.bind("<F11>", toggle_fullscreen)

root.bind("<Escape>", exit_fullscreen)

root.bind("<F2>", toggle_sidebar)

database_buttons_frame = tk.Frame(database_frame)
database_buttons_frame.grid(row=2, column=0, pady=10)

button_style = {
    'font': ("Open Sans", 14),
    'bg': "#4CAF50",
    'fg': "white",
    'relief': "raised",
    'padx': 15,
    'pady': 10,
    'bd': 2
}

fetch_db_button = tk.Button(database_buttons_frame, text="Pobierz dane z bazy", **button_style,
                            command=fetch_data_from_database)
fetch_db_button.grid(row=0, column=0, padx=10)

search_db_button = tk.Button(database_buttons_frame, text="Wyszukaj w bazie", **button_style,
                             command=search_in_database)
search_db_button.grid(row=0, column=1, padx=10)

reset_search_button = tk.Button(database_buttons_frame, text="Resetuj wyszukiwanie", **button_style,
                                command=reset_search)
reset_search_button.grid(row=0, column=2, padx=10)

distribute_button_popular = tk.Button(popular_posts_frame, text="Wyśrodkuj kolumny", **button_style,
                                      command=lambda: distribute_columns_evenly(posts_tree))
distribute_button_popular.grid(row=2, column=0, pady=10)

distribute_button_user = tk.Button(user_posts_frame, text="Wyśrodkuj kolumny", **button_style,
                                   command=lambda: distribute_columns_evenly(user_posts_tree))
distribute_button_user.grid(row=2, column=0, pady=10)

distribute_button_db = tk.Button(database_frame, text="Wyśrodkuj kolumny", **button_style,
                                 command=lambda: distribute_columns_evenly(db_data_tree))
distribute_button_db.grid(row=3, column=0, pady=10)

root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

popular_posts_frame.grid_rowconfigure(0, weight=1)
popular_posts_frame.grid_columnconfigure(0, weight=1)

user_posts_frame.grid_rowconfigure(0, weight=1)
user_posts_frame.grid_columnconfigure(0, weight=1)

database_frame.grid_rowconfigure(0, weight=1)
database_frame.grid_columnconfigure(0, weight=1)

icon = tk.PhotoImage(file='img/reddit-logo.png')

root.iconphoto(True, icon)
root.mainloop()
