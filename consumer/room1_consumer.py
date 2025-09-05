import sys
import time
import requests
import json

ROOM_NAME = "Room 1"
API_URL = "http://127.0.0.1:8000/api/notifications/"
POLL_INTERVAL = 2  # seconds

def poll_notifications():
    last_seen = None
    while True:
        params = {'room': ROOM_NAME}
        if last_seen:
            params['since'] = last_seen
        try:
            resp = requests.get(API_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                notifications = data.get('notifications', [])
                # Print in chronological order
                for n in reversed(notifications):
                    print(f"[CONSUMER] Notification for {ROOM_NAME}:")
                    print(json.dumps(n, indent=2))
                    last_seen = n['timestamp']
            else:
                print(f"[CONSUMER] Error: {resp.text}")
        except Exception as e:
            print(f"[CONSUMER] Polling error: {e}")
        time.sleep(POLL_INTERVAL)

def main():
    print(f"[CONSUMER] Polling for notifications for {ROOM_NAME}...")
    try:
        poll_notifications()
    except KeyboardInterrupt:
        print("[CONSUMER] Shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    main()
