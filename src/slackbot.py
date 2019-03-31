from slackclient import SlackClient
from dotenv import load_dotenv
from database import Database
import os
import random
import requests
import re
import json

load_dotenv()

# Slack client
slack_client = SlackClient(os.getenv("API_KEY"))

# Db connection
db = Database()

INTENTS = {
    "hello": ['hello', 'bonjour', 'hey', 'hi', 'sup', 'morning', 'hola', 'ohai', 'yo'],
    "booking": ['booking', 'book', 'reserve', 'go'],
    "information": ['information', 'info', 'details'],
    "user_info": ['my', 'previous']
}

r = requests.get("https://ancient-garden-79606.herokuapp.com/hotel/france")
hotels = r.json()


def parse_bot_commands(slack_events):
    """
    Get information from user and his message
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            message = event["text"]
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

    elif any(g in tokens for g in INTENTS.get("booking")):
        if(db.user_exist(user) <= 0):
            post_message(channel, "You're not registered in the database!")
            db.create_user(user)
        else:
            post_message(
                channel, "Hey {mention}, you're in our database".format(mention=username))
        response, attachments = hotel_process(user, message)
        post_message(channel, response, json.dumps(attachments))

    elif any(g in tokens for g in INTENTS.get("information")):
        test_hotel = re.findall(r"[^^]\b([A-Z][a-z']*)(\s[A-Z][a-z']*)*\b", message)
        hotel = [item for sublist in test_hotel for item in sublist] if test_hotel else None
        response, attachments = hotel_info(hotel)
        post_message(channel, response, json.dumps(attachments))

    elif any(g in tokens for g in INTENTS.get("user_info")):
        bookings = db.get_bookings(user)
        if len(bookings) > 0:
            response = "Here's your bookings:"
            for booking in bookings:
                hotel = list(filter(lambda x: x['id'] == booking['hotel'], hotels))[0]
                response += "\n_"+booking['created_at']+"_: *"\
                    +hotel['name']+"* the _"\
                    +booking['booking_date']\
                    +"_ for *"+booking['price']+"*"
            post_message(channel, response)
        else:
            post_message(channel, "You do not have any booking for now!")

def hotel_process(user, message):
    attachments = None
    test_location = re.search(
        r"\b(in|of|at)\b ((?=\S*['-])([a-zA-Z'-]+)|\w+)", message)
    location = test_location.group(2) if test_location else None
    test_hotel = re.findall(r"[^^]\b([A-Z][a-z']*)(\s[A-Z][a-z']*)*\b", message)
    hotel = [item for sublist in test_hotel for item in sublist] if test_hotel else None
    test_when = re.search(r"on\s(\w+)\s(\d+)", message)
    when = test_when.groups() if test_when else None


    if location:
        available = list(filter(lambda x: x['location']['address']['countryAddress'].lower(
        ) == location.lower(), hotels))
        if(len(available) > 0):
            response = "Here's available hotel in *" + location + "*:"
            for hotel in available:
                response += "\n\t" + \
                    hotel['name'] + " : " + \
                    'https://castle-client.herokuapp.com/h/france/'+hotel['id']
        else:
            response = "There is *no hotel available* in {location}...".format(
                location=location)
    elif hotel:
        hotel_to_book = list(filter(lambda x: all(s in x['name'] for s in hotel), hotels))
        if(len(hotel_to_book) > 0):
            attachments = [{
                "title": hotel_to_book[0]['name'],
                "title_link": 'https://castle-client.herokuapp.com/h/france/'+hotel_to_book[0]['id'],
                "text": "You can have more detail here...",
                "image_url": hotel_to_book[0]['media'],
                "fields": [
                    {
                        "title": "Postal Code",
                        "value": hotel_to_book[0]['location']['address']['postalCode'],
                        "short": "true"
                    },
                    {
                        "title": "MICHELIN",
                        "value": hotel_to_book[0]["restaurant"]["michelin_rating"] + " stars",
                        "short": "true"
                    }
                ],
                "color": "#FFEEFF"
            }]
            if when:
                response, booked = book_hotel(when, hotel_to_book, user)
                if not booked : attachments = None
            else:
                response = hotel_info(hotel_to_book)
        else:
            response = "Sorry this hotel does not exist in our database..."
    else:
        print("list of best hotel")
    return response, attachments

def book_hotel(when, hotel, user_id):
    """
    Process to allow a user to book a hotel if it's available
    TODO Do not allow user to book one hotel on the same day
    """
    response = None
    booked = False
    for attr, obj in hotel[0]['disponibilites'].items():
        if when[0].lower() in obj['name']:
            for attr, value in obj['body'].items():
                if("true" in value and re.findall(r"^\d+", value)[0] == when[1]):
                    response = "You've booked *{hotel}* on *{date}* for *{price}*!!".format(hotel=hotel[0]['name'], date=" ".join(when), price=re.findall(r"(\d*\s€)", value)[0])
                    db.create_booking(user_id, hotel[0]['id'], when[1] + " " + obj['name'], re.findall(r"(\d*\s€)", value)[0])
                    booked = True
                    break
    if not response:
        response = "Sorry, *{hotel}* is not available on *{date}*".format(hotel=hotel[0]['name'], date=" ".join(when))
        response += "\nGet more information by sending: *_info {hotel name}_*"

    return response, booked

def hotel_info(hotel):
    response = "Here's available *booking date*:"
    for attr, obj in hotel[0]['disponibilites'].items():
        response += "\n"+obj['name']+"\n"
        i = 0
        for attr, value in obj['body'].items():
            if("true" in value):
                response += "\t\t• " + re.findall(r"(.*€)", value)[0]
                i += 1
                if i % 4 == 0:
                    response += "\n"
    response += "\n\nIf you want to book this hotel please use this format: _month day_\n"
    return response


def post_message(channel, response, attachments=None):
    """
    Basic sending template to user
    """
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        attachments=attachments,
        text=response,
        mrkdwn="true"
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
