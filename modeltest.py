import matplotlib.pyplot as plt
from xgboost import XGBRegressor

from model import fetch_data_from_db, prepare_data, train_and_evaluate_models, load_model
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

df = fetch_data_from_db()

print(f"Liczba rekordów w całym zbiorze danych: {len(df)}")

X_train, X_test, y_train, y_test = prepare_data(df)

best_model_name, best_model, best_mse = train_and_evaluate_models(X_train, y_train, X_test, y_test)

model = load_model()

predictions = model.predict(X_test)

mse = mean_squared_error(y_test, predictions)
print(f"Mean Squared Error na zbiorze testowym: {mse}")

min_y = min(y_test.min(), predictions.min())
max_y = max(y_test.max(), predictions.max())

plt.figure(figsize=(36, 18))

indices = range(len(y_test))

plt.subplot(2, 3, 1)
plt.plot(indices, y_test.values, label="Rzeczywiste wartości", color='blue', marker='o', markersize=3)
plt.plot(indices, predictions, label="Przewidywane wartości (Najlepszy model)", color='red', linestyle='--', marker='x', markersize=3)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.title("Porównanie rzeczywistych i przewidywanych wartości - Najlepszy model")
plt.xlabel("Indeks próby")
plt.ylabel("Score")
plt.grid(True)
plt.ylim(min_y, max_y)

models = {
    "Ridge Regression": Ridge(),
    "Lasso Regression": Lasso(max_iter=10000),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=100, random_state=42)
}

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


for i, (name, result) in enumerate(model_results.items(), 2):
    plt.subplot(2, 3, i)
    plt.plot(indices, y_test.values, label="Rzeczywiste wartości", color='blue', marker='o', markersize=3)
    plt.plot(indices, result['predictions'], label=f"Przewidywane wartości ({name})", color='red', linestyle='--', marker='x', markersize=3)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.title(f"Porównanie rzeczywistych i przewidywanych wartości - {name}")
    plt.xlabel("Indeks próby")
    plt.ylabel("Score")
    plt.grid(True)
    plt.ylim(min_y, max_y)

plt.tight_layout(pad=10.0)
plt.show()
