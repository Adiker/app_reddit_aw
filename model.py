import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from textblob import TextBlob
from xgboost import XGBRegressor


def fetch_data_from_db():
    import sqlite3
    conn = sqlite3.connect('reddit_data.db')
    df = pd.read_sql_query("SELECT * FROM reddit_posts", conn)
    conn.close()
    return df


def create_features(df):
    df['title_length'] = df['title'].apply(len)

    df['title_sentiment'] = df['title'].apply(lambda x: TextBlob(x).sentiment.polarity)

    df['hour_of_day'] = pd.to_datetime(df['created_at']).dt.hour

    df['day_of_week'] = pd.to_datetime(df['created_at']).dt.dayofweek

    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

    df['author_post_count'] = df.groupby('author')['author'].transform('count')

    df['author_avg_score'] = df.groupby('author')['score'].transform('mean')

    df['has_media'] = df['url'].apply(lambda x: 1 if any(media in x for media in ['jpg', 'png', 'gif', 'mp4']) else 0)

    df['title_has_link'] = df['title'].apply(lambda x: 1 if 'http' in x else 0)

    df['comment_count'] = df['comment_count']

    df['upvote_ratio'] = df['upvote_ratio']

    df['comment_upvote_interaction'] = df['comment_count'] * df['upvote_ratio']
    df['sentiment_length_interaction'] = df['title_sentiment'] * df['title_length']

    df = create_topics(df)

    return df


def clean_data(df):
    df = df.dropna()
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    df['score'] = pd.to_numeric(df['score'], errors='coerce')
    df = df.dropna()

    required_columns = ['title_length', 'title_sentiment', 'hour_of_day', 'day_of_week', 'is_weekend',
                        'author_post_count', 'author_avg_score', 'has_media',
                        'title_has_link', 'comment_count', 'upvote_ratio',
                        'comment_upvote_interaction', 'sentiment_length_interaction', 'score']

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    return df


def prepare_data(df):
    df = create_features(df)
    df = clean_data(df)
    features = ['title_length', 'title_sentiment', 'hour_of_day', 'day_of_week', 'is_weekend',
                'author_post_count', 'author_avg_score', 'has_media',
                'title_has_link', 'comment_count', 'upvote_ratio',
                'comment_upvote_interaction', 'sentiment_length_interaction']

    X = df[features]
    y = np.log1p(df['score'])

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    return X_train, X_test, y_train, y_test

def create_topics(df, n_topics=5):
    count_vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
    dtm = count_vectorizer.fit_transform(df['title'])

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(dtm)

    topics = lda.transform(dtm)
    df['dominant_topic'] = topics.argmax(axis=1)

    return df
def train_and_evaluate_models(X_train, y_train, X_test, y_test):
    models = {
        "Ridge Regression": Ridge(),
        "Lasso Regression": Lasso(max_iter=10000),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42)
    }

    best_model_name = None
    best_model = None
    best_score = float('inf')

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"{name} Mean Squared Error: {mse}")

        if mse < best_score:
            best_score = mse
            best_model = model
            best_model_name = name

    return best_model_name, best_model, best_score



def optimize_ridge(X_train, y_train):
    ridge = Ridge()
    parameters = {'alpha': [0.1, 1, 10, 100]}
    ridge_grid_search = GridSearchCV(ridge, parameters, cv=5)
    ridge_grid_search.fit(X_train, y_train)
    return ridge_grid_search.best_estimator_


def optimize_lasso(X_train, y_train):
    lasso = Lasso(max_iter=10000)
    parameters = {'alpha': [0.1, 1, 10, 100]}
    lasso_grid_search = GridSearchCV(lasso, parameters, cv=5)
    lasso_grid_search.fit(X_train, y_train)
    return lasso_grid_search.best_estimator_

def optimize_xgboost(X_train, y_train):
    xgb = XGBRegressor(n_estimators=100, random_state=42)
    parameters = {'learning_rate': [0.01, 0.1, 0.2], 'max_depth': [3, 6, 9]}
    xgb_grid_search = GridSearchCV(xgb, parameters, cv=5)
    xgb_grid_search.fit(X_train, y_train)
    return xgb_grid_search.best_estimator_

def optimize_random_forest(X_train, y_train):
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    parameters = {'max_depth': [10, 20, None], 'min_samples_split': [2, 5, 10]}
    rf_grid_search = GridSearchCV(rf, parameters, cv=5)
    rf_grid_search.fit(X_train, y_train)
    return rf_grid_search.best_estimator_


def save_model(model, filename='reddit_trend_model.pkl'):
    joblib.dump(model, filename)


def load_model(filename='reddit_trend_model.pkl'):
    return joblib.load(filename)


if __name__ == "__main__":
    df = fetch_data_from_db()
    X_train, X_test, y_train, y_test = prepare_data(df)
    best_model_name, best_model, best_mse = train_and_evaluate_models(X_train, y_train, X_test, y_test)

    if isinstance(best_model, Ridge):
        best_model = optimize_ridge(X_train, y_train)
    elif isinstance(best_model, Lasso):
        best_model = optimize_lasso(X_train, y_train)

    save_model(best_model)

    print(f"Najlepszy model: {best_model_name}")
    print(f"{best_model_name} z zapisanym MSE: {best_mse}")

    scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
    print(f"Cross-Validation Scores: {-scores.mean()}")



