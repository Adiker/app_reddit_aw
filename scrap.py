import sqlite3
import nltk
import pandas as pd
import praw
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime

nltk.download('vader_lexicon')

def create_tables():
    conn = sqlite3.connect('reddit_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reddit_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            score INTEGER,
            subreddit TEXT,
            url TEXT UNIQUE,
            author TEXT,
            sentiment REAL,
            created_at TIMESTAMP,
            title_length INTEGER,
            hour_of_day INTEGER,
            day_of_week INTEGER,
            is_weekend INTEGER,
            author_post_count INTEGER,
            author_avg_score REAL,
            has_media INTEGER,
            comment_count INTEGER,
            upvote_ratio REAL,
            sentiment_title_interaction REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(posts):
    conn = sqlite3.connect('reddit_data.db')
    cursor = conn.cursor()

    for post in posts:
        created_at = datetime.utcfromtimestamp(post['Created_at']).isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO reddit_posts (
                title, score, subreddit, url, author, sentiment, created_at, title_length, 
                hour_of_day, day_of_week, is_weekend, author_post_count, author_avg_score, 
                has_media, comment_count, upvote_ratio, sentiment_title_interaction
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post['Title'], post['Score'], post['Subreddit'], post['URL'], post['Author'],
            post['Sentiment'], created_at, post['Title_length'], post['Hour_of_day'],
            post['Day_of_week'], post['Is_weekend'], post['Author_post_count'],
            post['Author_avg_score'], post['Has_media'], post['Comment_count'],
            post['Upvote_ratio'], post['Sentiment_title_interaction']
        ))

    conn.commit()
    conn.close()

def fetch_reddit_posts(subreddit, limit, post_type='hot'):
    user_agent = "praw_scraper_1.0"
    reddit = praw.Reddit(
        client_id='RQqxWxSFnMxig3sDALEQUg',
        client_secret='_2tiLRR5kJ6j9k_uZ5Dgu_1rcKDCyg',
        user_agent=user_agent
    )
    if post_type == 'hot':
        posts_generator = reddit.subreddit(subreddit).hot(limit=limit)
    elif post_type == 'new':
        posts_generator = reddit.subreddit(subreddit).new(limit=limit)
    elif post_type == 'top':
        posts_generator = reddit.subreddit(subreddit).top(limit=limit)
    elif post_type == 'controversial':
        posts_generator = reddit.subreddit(subreddit).controversial(limit=limit)
    else:
        raise ValueError("Nieprawidłowy wybór postów. Musi być: 'hot', 'new', 'top', 'controversial'.")
    posts = []
    sia = SentimentIntensityAnalyzer()
    author_stats = {}
    for post in posts_generator:
        post_sentiment = sia.polarity_scores(post.title)['compound']
        post.comments.replace_more(limit=0)
        top_comments = post.comments.list()[:5]
        comment_sentiments = [sia.polarity_scores(comment.body)['compound'] for comment in top_comments]
        avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0
        overall_sentiment = (post_sentiment + avg_comment_sentiment) / 2
        title_length = len(post.title)
        hour_of_day = datetime.utcfromtimestamp(post.created_utc).hour
        day_of_week = datetime.utcfromtimestamp(post.created_utc).weekday()
        is_weekend = int(day_of_week in [5, 6])
        has_media = int(any(media in post.url for media in ['jpg', 'png', 'gif', 'mp4']))
        comment_count = len(post.comments.list())
        upvote_ratio = post.upvote_ratio
        sentiment_title_interaction = post_sentiment * title_length
        author = str(post.author)
        if author not in author_stats:
            author_posts = reddit.redditor(author).submissions.new(limit=100)
            author_df = pd.DataFrame([{
                'score': p.score
            } for p in author_posts])
            avg_author_score = author_df['score'].mean() if not author_df.empty else 0
            author_post_count = len(author_df)
            author_stats[author] = {
                'post_count': author_post_count,
                'avg_score': avg_author_score
            }
        else:
            author_post_count = author_stats[author]['post_count']
            avg_author_score = author_stats[author]['avg_score']

        posts.append({
            'Title': post.title,
            'Score': post.score,
            'Subreddit': post.subreddit.display_name,
            'URL': post.url,
            'Author': author,
            'Sentiment': overall_sentiment,
            'Created_at': post.created_utc,
            'Title_length': title_length,
            'Hour_of_day': hour_of_day,
            'Day_of_week': day_of_week,
            'Is_weekend': is_weekend,
            'Author_post_count': author_post_count,
            'Author_avg_score': avg_author_score,
            'Has_media': has_media,
            'Comment_count': comment_count,
            'Upvote_ratio': upvote_ratio,
            'Sentiment_title_interaction': sentiment_title_interaction
        })

    save_to_db(posts)

    df = pd.DataFrame(posts)
    return df

def fetch_user_posts(username):
    user_agent = "praw_scraper_1.0"
    reddit = praw.Reddit(
        client_id='RQqxWxSFnMxig3sDALEQUg',
        client_secret='_2tiLRR5kJ6j9k_uZ5Dgu_1rcKDCyg',
        user_agent=user_agent
    )

    user = reddit.redditor(username)
    user_posts = user.submissions.new(limit=10)

    posts = []

    sia = SentimentIntensityAnalyzer()

    author_stats = {}

    for post in user_posts:

        post_sentiment = sia.polarity_scores(post.title)['compound']

        post.comments.replace_more(limit=0)
        top_comments = post.comments.list()[:5]

        comment_sentiments = [sia.polarity_scores(comment.body)['compound'] for comment in top_comments]
        avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0

        overall_sentiment = (post_sentiment + avg_comment_sentiment) / 2

        title_length = len(post.title)
        hour_of_day = datetime.utcfromtimestamp(post.created_utc).hour
        day_of_week = datetime.utcfromtimestamp(post.created_utc).weekday()
        is_weekend = int(day_of_week in [5, 6])
        has_media = int(any(media in post.url for media in ['jpg', 'png', 'gif', 'mp4']))
        comment_count = len(post.comments.list())
        upvote_ratio = post.upvote_ratio
        sentiment_title_interaction = post_sentiment * title_length

        author = str(post.author)
        if author not in author_stats:
            author_posts = reddit.redditor(author).submissions.new(limit=100)
            author_df = pd.DataFrame([{
                'score': p.score
            } for p in author_posts])
            avg_author_score = author_df['score'].mean() if not author_df.empty else 0
            author_post_count = len(author_df)
            author_stats[author] = {
                'post_count': author_post_count,
                'avg_score': avg_author_score
            }
        else:
            author_post_count = author_stats[author]['post_count']
            avg_author_score = author_stats[author]['avg_score']

        posts.append({
            'Title': post.title,
            'Score': post.score,
            'Subreddit': post.subreddit.display_name,
            'URL': post.url,
            'Author': author,
            'Sentiment': overall_sentiment,
            'Created_at': post.created_utc,
            'Title_length': title_length,
            'Hour_of_day': hour_of_day,
            'Day_of_week': day_of_week,
            'Is_weekend': is_weekend,
            'Author_post_count': author_post_count,
            'Author_avg_score': avg_author_score,
            'Has_media': has_media,
            'Comment_count': comment_count,
            'Upvote_ratio': upvote_ratio,
            'Sentiment_title_interaction': sentiment_title_interaction
        })

    save_to_db(posts)
    df = pd.DataFrame(posts)
    return df
