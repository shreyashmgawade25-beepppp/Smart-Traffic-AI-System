from ultralytics import YOLO
import cv2
import time
import csv
import os
from datetime import datetime

# ---------------- INITIALIZATION ----------------

model = YOLO("../models/yolov8n.pt")
cap = cv2.VideoCapture("../dataset/traffic.mp4")

if not cap.isOpened():
    print("Error opening video")
    exit()

# Window setup
cv2.namedWindow("AI Smart Traffic System", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Smart Traffic System", 1280, 720)

current_green_lane = "Lane A (LEFT)"
countdown_timer = 10
last_switch_time = time.time()

laneA_history = []
laneB_history = []

# -------- PARAMETERS --------
MAX_GREEN_TIME = 30

# -------- CSV SETUP (FIXED) --------
csv_path = "../results/traffic_data.csv"
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

file_exists = os.path.isfile(csv_path)

csv_file = open(csv_path, mode="a", newline="")
csv_writer = csv.writer(csv_file)

if not file_exists:
    csv_writer.writerow(["Time", "Lane_A_Count", "Lane_B_Count", "Green_Lane", "Countdown"])

# -----------------------------------------------

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    height, width, _ = frame.shape
    mid_x = width // 2

    # ROI (covers bottom 75%)
    roi_y_min = int(height * 0.25)

    lane_A_count = 0
    lane_B_count = 0

    allowed_classes = ["car", "Truck", "bus", "motorbike"]
    annotated = frame.copy()

    # ---------------- DETECTION ----------------
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        confidence = float(box.conf[0])

        if label not in allowed_classes or confidence < 0.5:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        if center_y < roi_y_min:
            continue

        if center_x < mid_x:
            lane_A_count += 1
        else:
            lane_B_count += 1

        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, f"{label} {confidence:.2f}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 2)

    # ---------------- SMOOTHING ----------------
    laneA_history.append(lane_A_count)
    laneB_history.append(lane_B_count)

    if len(laneA_history) > 10:
        laneA_history.pop(0)
        laneB_history.pop(0)

    avg_A = sum(laneA_history) / len(laneA_history)
    avg_B = sum(laneB_history) / len(laneB_history)

    # ---------------- SIGNAL LOGIC ----------------
    current_time = time.time()

    if countdown_timer <= 0:
        if avg_A > avg_B:
            current_green_lane = "Lane A (LEFT)"
        else:
            current_green_lane = "Lane B (RIGHT)"

        base_time = 10
        extra_time = int(max(avg_A, avg_B) * 2)
        countdown_timer = min(base_time + extra_time, MAX_GREEN_TIME)

    if current_time - last_switch_time >= 1:
        countdown_timer -= 1
        last_switch_time = current_time

    # ---------------- CSV WRITE (FIXED) ----------------
    current_time_str = datetime.now().strftime("%H:%M:%S")

    csv_writer.writerow([
        current_time_str,
        int(avg_A),
        int(avg_B),
        current_green_lane,
        countdown_timer
    ])

    csv_file.flush()  # 🔥 IMPORTANT

    # ---------------- VISUAL ----------------
    cv2.line(annotated, (mid_x, 0), (mid_x, height), (255, 255, 0), 2)
    cv2.line(annotated, (0, roi_y_min), (width, roi_y_min), (0, 255, 255), 2)

    cv2.putText(annotated, f"Lane A: {int(avg_A)}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.putText(annotated, f"Lane B: {int(avg_B)}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.putText(annotated, f"GREEN: {current_green_lane}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.putText(annotated, f"Countdown: {countdown_timer}s", (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    annotated = cv2.resize(annotated, (1280, 720))
    cv2.imshow("AI Smart Traffic System", annotated)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# ---------------- CLEANUP ----------------
cap.release()
cv2.destroyAllWindows()
csv_file.close()