import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

from scrap import fetch_reddit_posts, fetch_user_posts

import PIL
from PIL import Image, ImageTk

# Funkcje przypisane do przycisków
def fetch_data_1():
    messagebox.showinfo("Pobieranie danych", "Pobieranie danych z źródła 1...")
    df = fetch_reddit_posts()
    display_data(df, "Popular Reddit Posts")

def fetch_data_2():
    username = simpledialog.askstring("Input", "Please enter the Reddit username:")
    if username:
        try:
            df = fetch_user_posts(username)
            display_data(df, f"Latest Posts by {username}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

def display_data(df, title):
    # Create a new window
    data_window = tk.Toplevel(root)
    data_window.title(title)

    # Create a scrolled text widget
    text_area = scrolledtext.ScrolledText(data_window, wrap=tk.WORD, width=100, height=20)
    text_area.pack(padx=10, pady=10)

    # Insert data into the text area
    for index, row in df.iterrows():
        text_area.insert(tk.END, f"Title: {row['Title']}\n")
        text_area.insert(tk.END, f"Score: {row['Score']}\n")
        text_area.insert(tk.END, f"Subreddit: {row['Subreddit']}\n")
        text_area.insert(tk.END, f"URL: {row['URL']}\n")
        text_area.insert(tk.END, f"Author: {row['Author']}\n")
        text_area.insert(tk.END, f"Sentiment Score: {row['Sentiment']}\n")
        text_area.insert(tk.END, "-"*50 + "\n")

# Tworzenie głównego okna
root = tk.Tk()
root.title("Praca Inżynierska")

# Ustawienia wyglądu okna
root.geometry("1000x1000")
root.configure(bg="#f0f0f0")

# Ładowanie i wyświetlanie logo uniwersytetu
logo_image = Image.open("img/logo_up.png")

# Obliczanie nowych wymiarów, zachowując proporcje
max_size = (200, 200)
aspect_ratio = min(max_size[0] / logo_image.width, max_size[1] / logo_image.height)
new_size = (int(logo_image.width * aspect_ratio), int(logo_image.height * aspect_ratio))
logo_image_resized = logo_image.resize(new_size, PIL.Image.Resampling.LANCZOS)

logo_photo = ImageTk.PhotoImage(logo_image_resized)

logo_label = tk.Label(root, image=logo_photo, bg="#f0f0f0")
logo_label.image = logo_photo  # Zachowaj referencję do obrazu
logo_label.pack(pady=10)

# Etykieta nagłówkowa
header_label = tk.Label(root, text="Wybierz źródło danych", font=("Helvetica", 16), bg="#f0f0f0")
header_label.pack(pady=10)

# Przyciski do pobierania danych
button1 = tk.Button(root, text="Źródło 1", command=fetch_data_1, width=20, bg="#4CAF50", fg="white")
button1.pack(pady=5)

button2 = tk.Button(root, text="Źródło 2", command=fetch_data_2, width=20, bg="#2196F3", fg="white")
button2.pack(pady=5)

#button3 = tk.Button(root, text="Źródło 3", command=fetch_data_3, width=20, bg="#f44336", fg="white")
#button3.pack(pady=5)

# Uruchomienie pętli głównej
root.mainloop()
