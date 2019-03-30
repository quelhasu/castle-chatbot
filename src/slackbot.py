from slackclient import SlackClient
from dotenv import load_dotenv
from database import Database
import os
import random

load_dotenv()

# Slack client
slack_client = SlackClient(os.getenv("API_KEY"))

# Db connection
db = Database()

INTENTS = {
    "hello": ['hello', 'bonjour', 'hey', 'hi', 'sup', 'morning', 'hola', 'ohai', 'yo']
}


def parse_bot_commands(slack_events):
    """
    Get information from user and his message
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            message = event["text"].lower()
            return event["channel"], message.strip(), event["user"]
    return None, None, None


def handle_command(channel, message, user):
    """
    Get intents from user and return matching response
    """
    response = None
    username = get_mention(user)
    tokens = [word.lower() for word in message.strip().split()]

    if any(g in tokens for g in INTENTS.get("hello")):
        post_message(channel, random.choice(
            ['Hey, {mention}...', 'Yo!', 'Hola {mention}', 'Bonjour!']).format(mention=username))


def post_message(channel, response):
  """
  Basic sending template to user
  """
  slack_client.api_call(
      "chat.postMessage",
      channel=channel,
      text=response,
  )


def get_mention(user):
  """
  Return good user format for mentioning him
  """
  return '<@{user}>'.format(user=user)


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Castle Bot is running!")
        
        while True:
            try:
                channel, message, user = parse_bot_commands(
                    slack_client.rtm_read())
                if message:
                    handle_command(channel, message, user)
            except Exception as e:
                print("Reconnecting..." + str(e))
                slack_client.rtm_connect(with_team_state=False)
