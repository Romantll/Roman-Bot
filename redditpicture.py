import asyncpraw
import random
from asyncprawcore.exceptions import NotFound, Redirect

from dotenv import load_dotenv
import os
load_dotenv()


async def get_random_image(subreddit_name: str):

    reddit = asyncpraw.Reddit(
    client_id= os.getenv("REDDIT_CLIENT_ID"),
    client_secret= os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent= os.getenv("REDDIT_USER_AGENT")
    )    


    try:
        subreddit = await reddit.subreddit(subreddit_name, fetch=True)
    except (NotFound, Redirect):
        return None

    posts = []
    async for post in subreddit.hot(limit=50):
        if post.url.endswith((".jpg", ".jpeg", ".png")):
            posts.append(post)
    if not posts:
        return None
    return random.choice(posts)