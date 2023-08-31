import requests
from flask import Flask, request, redirect, render_template
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyDuvG0rE74nAW_IGHf9fYruWret02mpx_0"
youtube = build(api_service_name, api_version, developerKey=api_key)

def get_channel_id(handle):
    try:
        search_response = youtube.search().list(
            q=handle,
            type="channel",
            part="snippet"
        ).execute()

        channel_id = search_response["items"][0]["id"]["channelId"]
        return channel_id

    except HttpError as error:
        print(f"An HTTP error {error.resp.status} occurred: {error.content}")
        return None

@app.route("/")
def index():
    return render_template("credit.html", service_name="YouTube")

@app.route("/api")
def handle_api():
    stream_id = request.args.get("sid")
    res = request.args.get("quality", "auto")

    if not stream_id:
        channel_id = request.args.get("cid")
        if not channel_id:
            channel_id = get_channel_id(request.args.get("handle"))

        channel_num = int(request.args.get("num", 1)) - 1
        live_videos = youtube.search().list(
            part="id",
            channelId=channel_id,
            eventType="live",
            type="video"
        ).execute()

        video_ids = [item["id"]["videoId"] for item in live_videos["items"]]
        youtube_link = f"https://www.youtube.com/watch?v={video_ids[channel_num]}"
    else:
        youtube_link = f"https://www.youtube.com/watch?v={stream_id}"
        print(youtube_link)

    response = requests.get(youtube_link, timeout=15).text
    end = response.find('.m3u8') + 5
    tuner = 100

    while True:
        if 'https://' in response[end - tuner: end]:
            link = response[end - tuner: end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5
            break
        else:
            tuner += 5

    channel_hls = f"{link[start: end]}"
    if res.lower() != "auto":
        stream_list = ["#EXTM3U", "#EXT-X-INDEPENDENT-SEGMENTS"]
        lines = requests.get(channel_hls).text.splitlines()
        for index, line in enumerate(lines):
            if res in line:
                return redirect(lines[index + 1])
        return "\n".join(stream_list)
    else:
        return redirect(channel_hls)

if __name__ == "__main__":
    app.run(debug=True)