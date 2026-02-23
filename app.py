from flask import Flask, render_template, request
import os
import cv2
import numpy as np
from datetime import datetime
import json

app = Flask(__name__)
HISTORY_FILE = "history.json"

# Load history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        history_data = json.load(f)
else:
    history_data = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    view_mode = request.form.get("view_mode")
    player_name = request.form.get("player_name")
    gamemode = request.form.get("gamemode")
    weapon = request.form.get("weapon")
    gear = request.form.get("gear")

    if view_mode == "First Person":
        player_name = "N/A"

    file = request.files["video"]
    video_path = "uploaded_video.mp4"
    file.save(video_path)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_skip = 3

    hit_count = 0
    combo_count = 0
    last_hit_time = 0
    combo_timer_threshold = 0.7
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_index += 1
        if frame_index % frame_skip != 0:
            continue

        frame = cv2.resize(frame, (640, 360))
        current_time = frame_index / fps if fps > 0 else 0

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 120, 70])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)

        red_pixels = np.sum(mask > 0)

        if red_pixels > 2000:
            hit_count += 1
            if current_time - last_hit_time < combo_timer_threshold:
                combo_count += 1
            last_hit_time = current_time

    cap.release()
    os.remove(video_path)

    duration = frame_index / fps if fps > 0 else 1
    cps = round(hit_count / duration, 2) if duration > 0 else 0
    accuracy = min(100, hit_count * 2)
    rating = int((cps * 3 + combo_count * 4 + accuracy) / 3)

    recommendations = []

    if cps < 4:
        recommendations.append("Increase click speed consistency.")
    if combo_count < 3:
        recommendations.append("Work on maintaining longer combos.")
    if accuracy < 40:
        recommendations.append("Improve crosshair tracking.")
    if hit_count < 10:
        recommendations.append("Be more aggressive in fights.")
    if not recommendations:
        recommendations.append("Strong performance. Refine micro-adjustments.")

    result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "view_mode": view_mode,
        "player_name": player_name,
        "gamemode": gamemode,
        "weapon": weapon,
        "gear": gear,
        "cps": cps,
        "accuracy": accuracy,
        "combos": combo_count,
        "hits": hit_count,
        "rating": rating,
        "recommendations": recommendations
    }

    history_data.append(result)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history_data, f, indent=4)

    return render_template("result.html", result=result)


@app.route("/history")
def history():
    return render_template("history.html", history=history_data)


@app.route("/premium")
def premium():
    return render_template("premium.html", price_inr=100)


if __name__ == "__main__":
    app.run(debug=True)