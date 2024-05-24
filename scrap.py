import praw
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')


def fetch_reddit_posts():
    # Define your credentials
    user_agent = "praw_scraper_1.0"
    reddit = praw.Reddit(
        client_id='RQqxWxSFnMxig3sDALEQUg',
        client_secret='_2tiLRR5kJ6j9k_uZ5Dgu_1rcKDCyg',
        user_agent=user_agent
    )

    # Fetch the 10 popular posts from r/popular
    popular_posts = reddit.subreddit('popular').hot(limit=10)

    # Create a list to store post details
    posts = []

    # Initialize VADER sentiment analyzer
    sia = SentimentIntensityAnalyzer()

    # Loop through the posts and add details to the list
    for post in popular_posts:
        # Calculate sentiment for the post title
        post_sentiment = sia.polarity_scores(post.title)['compound']

        # Fetch the top 5 comments
        post.comments.replace_more(limit=0)
        top_comments = post.comments.list()[:5]

        # Calculate sentiment for the top comments
        comment_sentiments = [sia.polarity_scores(comment.body)['compound'] for comment in top_comments]
        if comment_sentiments:
            avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments)
        else:
            avg_comment_sentiment = 0

        # Average the sentiment scores
        overall_sentiment = (post_sentiment + avg_comment_sentiment) / 2

        posts.append({
            'Title': post.title,
            'Score': post.score,
            'Subreddit': post.subreddit.display_name,
            'URL': post.url,
            'Author': str(post.author),
            'Sentiment': overall_sentiment
        })

    # Create a pandas DataFrame
    df = pd.DataFrame(posts)
    return df


def fetch_user_posts(username):
    # Define your credentials
    user_agent = "praw_scraper_1.0"
    reddit = praw.Reddit(
        client_id='RQqxWxSFnMxig3sDALEQUg',
        client_secret='_2tiLRR5kJ6j9k_uZ5Dgu_1rcKDCyg',
        user_agent=user_agent
    )

    # Fetch the 10 latest posts from the user
    user = reddit.redditor(username)
    user_posts = user.submissions.new(limit=10)

    # Create a list to store post details
    posts = []

    # Initialize VADER sentiment analyzer
    sia = SentimentIntensityAnalyzer()

    # Loop through the posts and add details to the list
    for post in user_posts:
        # Calculate sentiment for the post title
        post_sentiment = sia.polarity_scores(post.title)['compound']

        # Fetch the top 5 comments
        post.comments.replace_more(limit=0)
        top_comments = post.comments.list()[:5]

        # Calculate sentiment for the top comments
        comment_sentiments = [sia.polarity_scores(comment.body)['compound'] for comment in top_comments]
        if comment_sentiments:
            avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments)
        else:
            avg_comment_sentiment = 0

        # Average the sentiment scores
        overall_sentiment = (post_sentiment + avg_comment_sentiment) / 2

        posts.append({
            'Title': post.title,
            'Score': post.score,
            'Subreddit': post.subreddit.display_name,
            'URL': post.url,
            'Author': str(post.author),
            'Sentiment': overall_sentiment
        })

    # Create a pandas DataFrame
    df = pd.DataFrame(posts)
    return df
