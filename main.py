import os
import time

import praw

# Determines what subreddit to monitor. Bot must be a moderator on the subreddit.
SUB = os.environ["FLAIRBOT_SUBREDDIT"]
# The footer to add at the bottom of a reply.
REPLY_FOOTER = "\n\n---\n\n^^I'm ^^a ^^bot. ^^| ^^[How&nbsp;to&nbsp;flair](https://vgy.me/ezxQsq.png)"
# How much time should pass before a post is removed for lacking flair. Time is in minutes.
REMOVE_AFTER = 10

# If a post is not flaired within one minute, reply with this.
WARN_MSG = "Your post has not been flaired! Make sure to flair your post or it will automatically be removed in {} minutes.{}".format(
    REMOVE_AFTER, REPLY_FOOTER)
# What to reply with when a post was removed for not having a flair.
REMOVE_MSG = "Your post has been removed for not being flaired after {} minutes. If you believe this was in error, contact the moderators.{}".format(
    REMOVE_AFTER, REPLY_FOOTER)

# Enter the bot's Reddit credentials and the application's info here.
r = praw.Reddit(client_id=os.environ["FLAIRBOT_CLIENT_ID"],
                client_secret=os.environ["FLAIRBOT_CLIENT_SECRET"],
                username=os.environ["FLAIRBOT_USERNAME"],
                password=os.environ["FLAIRBOT_PASSWORD"],
                user_agent="heroku:sbubby-flairbot:1.0.0 (by /u/phxvyper)")

print("Connected to reddit as /u/{}".format(r.user.me().name))

# The subreddit we'll be monitoring.
subreddit = r.subreddit(SUB)
# Store replies our bot makes so we can check and remove them cleanly later.
bot_replies = {}
start_time = time.time()

if r.user.me() not in list(subreddit.moderator()):
    raise Exception(
        "The bot is not a moderator on /r/{}, exiting.".format(SUB))

print("Starting post checker.")
while True:
    for post in subreddit.new(limit=30):
        # If the post was created before the bot was started or the post is distinguished, disregard it.
        if post.created_utc < start_time or post.distinguished:
            continue
        # Checks if post is flaired.
        if post.link_flair_text is None:
            # Gets time difference between now and post creation.
            time_diff = time.time() - post.created_utc

            # If it's been 60 seconds since the post was created, let the author know to flair it.
            if time_diff > 60 and post.id not in bot_replies:
                print("Post '{}' by {} is not flaired yet. Letting them know the rules!".format(
                    post.title, post.author))
                bot_reply = post.reply(WARN_MSG)
                bot_reply.mod.distinguish()
                bot_replies[post.id] = bot_reply.id

            # If post was not flaired in time, reply and remove it.
            elif time_diff > REMOVE_AFTER * 60:
                print("Post '{}' by {} was not flaired after {} minutes, removing.".format(
                    post.title, post.author, REMOVE_AFTER))
                post.reply(REMOVE_MSG).mod.distinguish()
                r.comment(id=bot_replies[post.id]).delete()
                post.mod.remove()

        elif post.id in bot_replies:
            r.comment(id=bot_replies[post.id]).delete()
