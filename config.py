import os
BOT_TOKEN=os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN env variable is not set")
