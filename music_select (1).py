import os
import random

BASE_DIR = "/home/capstone/Downloads"
desired_mood_file = "/home/capstone/project/want_feeling.txt"
current_mood_file = "/home/capstone/project/current_feeling.txt"

# 가능한 감정 목록
desired_moods = ["healing", "relief", "energy", "love", "focus"]
current_moods = ["happy", "sad", "angry"]

def select_random_music_path():
    try:
        # 원하는 기분 읽기
        with open(desired_mood_file, "r") as f:
            lines = f.readlines()
            desired_mood = lines[-1].strip() if lines else ""

        # 현재 기분 읽기
        with open(current_mood_file, "r") as f:
            lines = f.readlines()
            current_mood = lines[-1].strip() if lines else ""

        # 음악 폴더 경로
        music_dir = os.path.join(BASE_DIR, desired_mood, current_mood)

        # MP3 파일 선택
        music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
        if not music_files:
            raise FileNotFoundError(f"'{music_dir}' 폴더에 MP3 파일이 없습니다.")

        selected_music = os.path.join(music_dir, random.choice(music_files))
        print(f"선택된 음악: {selected_music}")

        # 선택된 음악 경로를 파일에 저장
        with open("/home/capstone/project/selected_music.txt", "w") as f:
            f.write(selected_music)

        return selected_music

    except Exception as e:
        print(f"오류: {e}")
        return None

if __name__ == "__main__":
    select_random_music_path()
