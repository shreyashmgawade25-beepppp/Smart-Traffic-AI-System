from ultralytics import YOLO
import cv2
import time
import matplotlib.pyplot as plt
import csv
from datetime import datetime

# ---------------- INITIALIZATION ----------------

model = YOLO("models/yolov8n.pt")
cap = cv2.VideoCapture("dataset/traffic.mp4")

if not cap.isOpened():
    print("Error opening video")
    exit()

current_green_lane = None
countdown_timer = 0
last_switch_time = time.time()

laneA_history = []
laneB_history = []

# -------- CSV FILE SETUP --------
csv_file = open("results/traffic_data.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Time", "Lane_A_Count", "Lane_B_Count", "Green_Lane", "Countdown"])
# --------------------------------

plt.ion()
fig, ax = plt.subplots()

# -----------------------------------------------

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    height, width, _ = frame.shape
    mid_x = width // 2
    roi_y_min = int(height * 0.35)

    lane_A_count = 0
    lane_B_count = 0

    allowed_classes = ["car", "truck", "bus", "motorbike"]

    annotated = frame.copy()

    # ---------------- VEHICLE DETECTION ----------------
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        confidence = float(box.conf[0])

        if label not in allowed_classes:
            continue

        if confidence < 0.5:
            continue

        x1, y1, x2, y2 = box.xyxy[0]
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        if center_y < roi_y_min:
            continue

        if center_x < mid_x:
            lane_A_count += 1
        else:
            lane_B_count += 1

        # Draw only valid vehicle boxes
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated,
            f"{label} {confidence:.2f}",
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    # ---------------- SIGNAL LOGIC ---------------------

    current_time = time.time()

    if countdown_timer <= 0:
        if lane_A_count > lane_B_count:
            current_green_lane = "Lane A (LEFT)"
        else:
            current_green_lane = "Lane B (RIGHT)"

        countdown_timer = 15
        last_switch_time = current_time

    if current_time - last_switch_time >= 1:
        countdown_timer -= 1
        last_switch_time = current_time

    # ---------------------------------------------------

    # -------- SAVE DATA TO CSV --------
    current_time_str = datetime.now().strftime("%H:%M:%S")
    csv_writer.writerow([
        current_time_str,
        lane_A_count,
        lane_B_count,
        current_green_lane,
        countdown_timer
    ])
    # ----------------------------------

    # Lane divider
    cv2.line(annotated, (mid_x, 0), (mid_x, height), (255, 255, 0), 2)

    # ROI divider
    cv2.line(annotated, (0, roi_y_min), (width, roi_y_min), (0, 255, 255), 2)

    # Display text
    cv2.putText(annotated, f"Lane A Count: {lane_A_count}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.putText(annotated, f"Lane B Count: {lane_B_count}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.putText(annotated, f"GREEN: {current_green_lane}",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.putText(annotated, f"Countdown: {countdown_timer} sec",
                (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    cv2.imshow("AI Multi-Lane Smart Traffic System", annotated)

    # ---------------- LIVE GRAPH -----------------------

    laneA_history.append(lane_A_count)
    laneB_history.append(lane_B_count)

    if len(laneA_history) > 50:
        laneA_history.pop(0)
        laneB_history.pop(0)

    ax.clear()
    ax.plot(laneA_history, label="Lane A")
    ax.plot(laneB_history, label="Lane B")
    ax.set_title("Live Traffic Density")
    ax.legend()
    plt.pause(0.001)

    # ---------------------------------------------------

    if cv2.waitKey(1) & 0xFF == 27:
        break

# ---------------- CLEANUP ----------------
cap.release()
cv2.destroyAllWindows()
csv_file.close()
plt.ioff()
plt.show()
# -----------------------------------------