import matplotlib.pyplot as plt
from model import fetch_data_from_db, prepare_data, train_and_evaluate_models, load_model
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Załaduj dane z bazy danych
df = fetch_data_from_db()

# Sprawdź rozmiar całego zbioru danych
print(f"Liczba rekordów w całym zbiorze danych: {len(df)}")

# Podziel dane na zbiór treningowy i testowy
X_train, X_test, y_train, y_test = prepare_data(df)

# Trenuj i oceniaj modele
best_model, best_mse = train_and_evaluate_models(X_train, y_train, X_test, y_test)

# Załaduj zapisany model
model = load_model()

# Dokonaj przewidywań na zbiorze testowym
predictions = model.predict(X_test)

# Oblicz MSE dla najlepszego modelu
mse = mean_squared_error(y_test, predictions)
print(f"Mean Squared Error na zbiorze testowym: {mse}")

# Przygotowanie zakresu osi Y
min_y = min(y_test.min(), predictions.min())
max_y = max(y_test.max(), predictions.max())

# Wykres
plt.figure(figsize=(18, 12))  # Ustaw rozmiar wykresu

# Indeksy jako liczby całkowite
indices = range(len(y_test))

# Dodaj wykresy dla najlepszego modelu
plt.subplot(2, 2, 1)
plt.plot(indices, y_test.values, label="Rzeczywiste wartości", color='blue', marker='o', markersize=3)
plt.plot(indices, predictions, label="Przewidywane wartości (Najlepszy model)", color='red', linestyle='--', marker='x', markersize=3)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  # Przesuń legendę, aby nie zasłaniała wykresu
plt.title("Porównanie rzeczywistych i przewidywanych wartości - Najlepszy model")
plt.xlabel("Indeks próby")
plt.ylabel("Score")
plt.grid(True)
plt.ylim(min_y, max_y)  # Ustaw zakres osi Y

# Załaduj wyniki dla wszystkich modeli
models = {
    "Ridge Regression": Ridge(),
    "Lasso Regression": Lasso(max_iter=10000),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42)
}

# Wytrenuj i oceń modele
model_results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    model_results[name] = {
        'predictions': predictions,
        'mse': mse
    }
    print(f"{name} Mean Squared Error: {mse}")

# Wykresy dla każdego modelu
for i, (name, result) in enumerate(model_results.items(), 2):
    plt.subplot(2, 2, i)
    plt.plot(indices, y_test.values, label="Rzeczywiste wartości", color='blue', marker='o', markersize=3)
    plt.plot(indices, result['predictions'], label=f"Przewidywane wartości ({name})", color='red', linestyle='--', marker='x', markersize=3)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))  # Przesuń legendę, aby nie zasłaniała wykresu
    plt.title(f"Porównanie rzeczywistych i przewidywanych wartości - {name}")
    plt.xlabel("Indeks próby")
    plt.ylabel("Score")
    plt.grid(True)
    plt.ylim(min_y, max_y)  # Ustaw zakres osi Y

plt.tight_layout()  # Dopasuj layout
plt.show()
