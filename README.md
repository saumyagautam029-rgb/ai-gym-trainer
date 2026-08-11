# AI Gym Trainer

Exercise tracking system with video upload and workout history.

## What It Does
- Upload workout videos (MP4/MOV/AVI)
- Select exercise type (Squats, Push-ups, Bicep Curls)
- Simulated rep counting for cloud deployment
- Workout history with SQLite
- Statistics dashboard

## Status
Cloud deployment uses simulated counting due to MediaPipe dependency 
constraints on free tiers. Local version supports real-time pose 
estimation with MediaPipe 33-landmark detection and angle-based 
rep counting.

## Tech Stack
- Streamlit
- SQLite
- Pandas

## Live Demo
https://ai-gym-trainer-yeorzyufseodbn4ngsn96x.streamlit.app/
