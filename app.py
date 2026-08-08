import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
import sqlite3
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="AI Gym Trainer", layout="wide")

# ========== DATABASE ==========
DB_PATH = "workouts.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise TEXT,
            reps INTEGER,
            date TEXT,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_workout(exercise, reps):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now()
    c.execute("INSERT INTO workouts (exercise, reps, date, time) VALUES (?, ?, ?, ?)",
              (exercise, reps, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM workouts ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()

# ========== MEDIAPIPE SETUP ==========
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# ========== ANGLE CALCULATION ==========
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    if angle > 180.0:
        angle = 360-angle
    return angle

# ========== EXERCISE COUNTER ==========
class ExerciseCounter:
    def __init__(self):
        self.counter = 0
        self.stage = None
    
    def reset(self):
        self.counter = 0
        self.stage = None

counter = ExerciseCounter()

# ========== STREAMLIT UI ==========
st.title("AI Gym Trainer")
st.caption("Real-time exercise detection with MediaPipe Pose")

exercise = st.selectbox("Select Exercise", ["Squats", "Push-ups", "Bicep Curls"])

st.subheader("Upload Video or Use Camera")
option = st.radio("Input", ["Upload Video", "Live Camera"], horizontal=True)

if option == "Upload Video":
    video_file = st.file_uploader("Upload workout video", type=['mp4', 'mov', 'avi'])
    
    if video_file:
        tfile = open("temp.mp4", "wb")
        tfile.write(video_file.read())
        cap = cv2.VideoCapture("temp.mp4")
        
        stframe = st.empty()
        counter.reset()
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                if exercise == "Squats":
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    
                    angle = calculate_angle(hip, knee, ankle)
                    
                    if angle > 160:
                        counter.stage = "up"
                    if angle < 90 and counter.stage == "up":
                        counter.stage = "down"
                        counter.counter += 1
                
                elif exercise == "Push-ups":
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    
                    angle = calculate_angle(shoulder, elbow, wrist)
                    
                    if angle > 160:
                        counter.stage = "up"
                    if angle < 90 and counter.stage == "up":
                        counter.stage = "down"
                        counter.counter += 1
                
                elif exercise == "Bicep Curls":
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                    
                    angle = calculate_angle(shoulder, elbow, wrist)
                    
                    if angle > 160:
                        counter.stage = "down"
                    if angle < 30 and counter.stage == "down":
                        counter.stage = "up"
                        counter.counter += 1
                
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            cv2.putText(image, f'Reps: {counter.counter}', (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            
            stframe.image(image, channels="RGB", use_container_width=True)
        
        cap.release()
        os.remove("temp.mp4")
        
        if counter.counter > 0:
            save_workout(exercise, counter.counter)
            st.success(f"Workout saved! {counter.counter} {exercise} completed.")

else:
    st.info("Camera mode works best when running locally. For cloud deploy, use video upload.")

# ========== HISTORY ==========
st.divider()
st.subheader("Workout History")

history = get_history()
if history:
    df = pd.DataFrame(history, columns=["ID", "Exercise", "Reps", "Date", "Time"])
    st.dataframe(df.drop("ID", axis=1), use_container_width=True)
else:
    st.info("No workouts recorded yet.")
