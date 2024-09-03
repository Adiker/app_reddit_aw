import random
import threading
import time
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from tkinter import font as tkfont

from scrap import fetch_reddit_posts

SUBREDDITS = ['askreddit', 'python', 'learnprogramming', 'datascience', 'technology', 'funny', 'gaming', 'worldnews',
              'todayilearned', 'aww', 'music', 'movies', 'memes', 'science']
POST_TYPES = ['new', 'hot', 'top', 'controversial']
current_subreddit = None
current_post_type = None

def fetch_data():
    global current_subreddit, current_post_type

    status_label.config(text="Pobieranie danych z Reddit...")
    progress_bar.start()
    root.update_idletasks()

    subreddit = current_subreddit if current_subreddit else subreddit_choice.get()
    post_type = current_post_type if current_post_type else post_type_choice.get()
    limit = post_limit.get()

    status_label.config(text=f"Pobieranie {post_type} postów z subreddita: {subreddit} (Limit: {limit})")
    root.update_idletasks()

    try:
        df_subreddit = fetch_reddit_posts(subreddit, limit, post_type)
        print(f"Pobrano {post_type} posty z subreddita: {subreddit}.")
        status_label.config(text=f"Pobrano {post_type} posty z subreddita: {subreddit}.")
    except Exception as e:
        print(f"Błąd podczas pobierania danych: {e}")
        status_label.config(text=f"Błąd podczas pobierania danych: {e}")
    finally:
        progress_bar.stop()
        root.update_idletasks()

def run_schedule():
    global current_subreddit, current_post_type

    while running[0]:
        fetch_data()
        if subreddit_choice.get() == "random":
            current_subreddit = random.choice(SUBREDDITS)
        if post_type_choice.get() == "random":
            current_post_type = random.choice(POST_TYPES)
        time.sleep(3)

def start_fetching_data():
    global current_subreddit, current_post_type

    subreddit = simpledialog.askstring("Wybór subreddita", "Podaj subreddita (lub wpisz 'random' dla losowego):", initialvalue="random")
    if subreddit is None:
        return
    if subreddit == "random":
        current_subreddit = random.choice(SUBREDDITS)  # Zainicjuj losowy subreddit
    else:
        current_subreddit = subreddit
    subreddit_choice.set(subreddit)
    root.update()
    limit = simpledialog.askinteger("Wybór limitu", "Podaj limit postów:", initialvalue=50, minvalue=1)
    if limit is None:
        messagebox.showwarning("Błąd", "Nieprawidłowy limit postów.")
        return
    post_limit.set(limit)
    root.update()
    post_type = simpledialog.askstring("Wybór typu postów", "Podaj typ postów (new, hot, top, controversial) lub 'random' dla losowego:", initialvalue="new")
    if post_type == "random":
        current_post_type = random.choice(POST_TYPES)
    elif post_type in POST_TYPES:
        current_post_type = post_type
    else:
        messagebox.showwarning("Błąd", "Nieprawidłowy typ postów.")
        return
    post_type_choice.set(current_post_type)

    start_button.config(state=tk.DISABLED)
    cancel_button.config(state=tk.NORMAL)
    running[0] = True

    global schedule_thread
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.daemon = True
    schedule_thread.start()

def stop_fetching_data():
    running[0] = False
    if 'schedule_thread' in globals() and schedule_thread.is_alive():
        schedule_thread.join()

    start_button.config(state=tk.NORMAL)
    cancel_button.config(state=tk.DISABLED)
    status_label.config(text="Pobieranie danych zatrzymane.")
    progress_bar.stop()
    root.update_idletasks()

root = tk.Tk()
root.title("Automatyczne Pobieranie Danych z Reddit")

font = tkfont.Font(family="Helvetica", size=12)
large_font = tkfont.Font(family="Helvetica", size=14, weight="bold")

status_label = tk.Label(root, text="Gotowy do pobierania danych...", font=large_font)
status_label.pack(pady=20)

progress_bar = ttk.Progressbar(root, mode='indeterminate')
progress_bar.pack(pady=10)

subreddit_choice = tk.StringVar(value="random")
post_limit = tk.IntVar(value=50)
post_type_choice = tk.StringVar(value="new")

start_button = tk.Button(root, text="Rozpocznij Pobieranie Danych", command=start_fetching_data, font=font, relief="raised")
start_button.pack(pady=10)

cancel_button = tk.Button(root, text="Anuluj", command=stop_fetching_data, font=font, relief="raised", state=tk.DISABLED)
cancel_button.pack(pady=10)

running = [False]

root.mainloop()
