import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import googleapiclient.errors
import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "client_secret_file.json"
scopes = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]


def get_user_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_file.json', scopes)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds


def list_subscriptions(**extra_args):
    subscriptions = []
    params={
        "part": "id,snippet",
        "maxResults": 50
    }
    params.update(extra_args)

    with open("API_TOKEN.txt") as f:
        if "mine" in params:
            credentials = get_user_credentials()
            youtube = googleapiclient.discovery.build(
                api_service_name, api_version, credentials=credentials
            )
        else:
            youtube = googleapiclient.discovery.build(
                api_service_name, api_version, developerKey = f.read()
            )

        while True:
            # Create an API client
            request = youtube.subscriptions().list(
                **params
            )
            response = request.execute()

            subscriptions.extend(response["items"])
            if response.get("nextPageToken"):
                params["pageToken"] = response["nextPageToken"]
            else:
                break
    
    return subscriptions


def batch_subscribe(channels):
    params={
        "part": "snippet"
    }

    # Get credentials and create an API client
    credentials = get_user_credentials()
    youtube = googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
    
    current_subs = set(map(lambda d: d["snippet"]["resourceId"]["channelId"], list_subscriptions(mine=True)))

    for channel in channels:
        channel_title = channel["snippet"]["title"]
        channel_resource_id = channel["snippet"]["resourceId"]
        channel_id = channel_resource_id["channelId"]
        if channel_id not in current_subs:
            params["body"] = {"snippet": {"resourceId": channel_resource_id}}
            request = youtube.subscriptions().insert(**params)

            try:
                response = request.execute()
                print(f"Subscribed to channel {response.get('snippet', {}).get('title')}")
            except googleapiclient.errors.HttpError as e:
                print(f"Error when subscribing to channel {channel_title}")
                print(f"Reason: {e.reason}")


def main():
    print("Type the channel id to export subscriptions from:")
    channel_id = input()
    subs = list_subscriptions(channelId=channel_id)
    print(f"Retrieved {len(subs)} channels from subscription list.")
    with open("subscriptions.json", "w") as f:
        json.dump({"subscriptions": subs}, f)
    
    print("Login to the channel to import subscriptions:")
    batch_subscribe(subs)
    print("Subscribed to all exported channels.")


if __name__ == "__main__":
    main()
