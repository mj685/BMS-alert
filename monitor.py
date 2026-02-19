import requests
import json
import os
import smtplib
from email.mime.text import MIMEText

EVENT_ID = "ET00474264"
URL = f"https://in.bookmyshow.com/api/le/events/info/{EVENT_ID}"

STATE_FILE = "state.json"

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"alert_sent": False}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def check_availability():
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "x-app-code": "WEB",
        "x-platform-code": "WEB",
        "x-region-code": "BANG",
        "x-region-slug": "bengaluru"
    }

    response = requests.get(URL, headers=headers, timeout=15)

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Non-200 response received")
        return False

    if "application/json" not in response.headers.get("content-type", ""):
        print("Did not receive JSON. Possibly blocked.")
        return False

    data = response.json()

    event_cards = data.get("eventCards", {})

    for venue in event_cards.values():
        for date in venue.values():
            for time in date.values():
                for category in time.values():
                    seats = category.get("minAvailableSeats", 0)
                    if seats and int(seats) > 0:
                        return True

    return False


def send_email():
    subject = "🚨 Tickets LIVE for ET00474264"
    body = f"""
Tickets are now AVAILABLE!

Book here:
https://in.bookmyshow.com/sports/super-8-match-8-icc-men-s-t20-wc-2026/{EVENT_ID}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAILS

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(
        SENDER_EMAIL,
        RECIPIENT_EMAILS.split(","),
        msg.as_string()
    )
    server.quit()

def main():
    state = load_state()

    available = check_availability()

    if available and not state["alert_sent"]:
        send_email()
        state["alert_sent"] = True
        save_state(state)

    if not available:
        state["alert_sent"] = False
        save_state(state)

if __name__ == "__main__":
    main()
