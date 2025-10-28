
import RPi.GPIO as GPIO
from music_select import select_random_music_path
import subprocess
import time
import threading

# Pin definitions
START_PIN = 17
STOP_PIN = 16
LED_RED_PIN = 21
LED_YELLOW_PIN = 26
LED_GREEN_PIN = 20
LED_emotion_happy = 27 
LED_emotion_sad = 22
LED_emotion_angry = 12

feeling_buttons = {
    5: "healing",
    6: "relief",
    23: "energy",
    24: "focus",
    25: "love"
}

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(LED_RED_PIN,GPIO.OUT)
GPIO.output(LED_RED_PIN, GPIO.LOW)
GPIO.setup(LED_GREEN_PIN,GPIO.OUT)
GPIO.output(LED_GREEN_PIN, GPIO.LOW)
GPIO.setup(LED_YELLOW_PIN,GPIO.OUT)
GPIO.output(LED_YELLOW_PIN, GPIO.LOW)
GPIO.setup(LED_emotion_happy,GPIO.OUT)
GPIO.output(LED_emotion_happy, GPIO.LOW)
GPIO.setup(LED_emotion_sad,GPIO.OUT)
GPIO.output(LED_emotion_sad, GPIO.LOW)
GPIO.setup(LED_emotion_angry,GPIO.OUT)
GPIO.output(LED_emotion_angry, GPIO.LOW)
GPIO.setup(START_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
for pin in feeling_buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Globals
music_process = None
process_lock = threading.Lock()
selected_feeling = None
feeling_selected = threading.Event()
# global label

last_press_time = 0
click_count = 0
paused = False
current_music_path = None
paused_position =0
music_start_time =0

print("Ready. Press START button first, then select a feeling.")

import subprocess

def get_audio_device(prefer="USB"):
    result = subprocess.run("aplay -l", shell=True, capture_output=True, text=True)
    output = result.stdout

    card_number = None

    for line in output.splitlines():
        if "card" in line and "device" in line:
            # 예: card 3: UACDemoV10 [UACDemoV1.0], device 0: USB Audio
            if prefer in line:
                parts = line.split()
                card = parts[1].rstrip(':')
                device = parts[5].rstrip(':')
                return f"hw:{card},{device}"
    print(card_number)
    # fallback - 첫 번째 장치 사용
    for line in output.splitlines():
        if "card" in line and "device" in line:
            parts = line.split()
            card = parts[1].rstrip(':')
            device = parts[5].rstrip(':')
            return f"hw:{card},{device}"

    return None

# Toggle / random change logic on STOP_PIN
def handle_stop_button(channel):
    global last_press_time, click_count, music_process, paused, current_music_path

    now = time.time()
    if now - last_press_time <= 1:
        click_count += 1
    else:
        click_count = 1
    last_press_time = now

    def single_click_action():
        global paused, click_count, music_process, current_music_path, paused_position, music_start_time
        time.sleep(1)
        if click_count == 1:
            with process_lock:
                if music_process and music_process.poll() is None:
                    print("🔇 음악 일시 정지")
                    paused_position = time.time() - music_start_time
                    music_process.terminate()
                    music_process.wait()
                    paused = True
                elif paused and current_music_path:
                    print("▶️ 음악 다시 재생")
                    frame_offset = int(paused_position*38)
                    music_process = subprocess.Popen(["mpg123", "-k", str(frame_offset), "-a", get_audio_device() , current_music_path])
                    music_start_time = time.time() - paused_position
                    paused = False
        elif click_count == 2:
            with process_lock:
                print("🔁 더블 클릭 감지됨 - 새로운 랜덤 음악 재생")
                if music_process and music_process.poll() is None:
                    music_process.terminate()
                    music_process.wait()
                new_path = select_random_music_path()
                if new_path:
                    current_music_path = new_path
                    music_process = subprocess.Popen(["mpg123", "-a", get_audio_device(), current_music_path])
                    music_start_time = time.time()
                    paused_position =0
                    paused = False
                else:
                    print("❌ 랜덤 음악 선택 실패")
        click_count = 0

    threading.Thread(target=single_click_action).start()

# Wait for feeling button press
def wait_for_feeling():
    global selected_feeling
    print("Please press a feeling button...")
    while True:
        for pin, feeling in feeling_buttons.items():
            if GPIO.input(pin) == GPIO.HIGH:
                selected_feeling = feeling
                with open("/home/capstone/project/want_feeling.txt", "w") as f:
                    f.write(f"{feeling}\n")
                print(f"Feeling selected: {feeling}")
                feeling_selected.set()
                return
        time.sleep(0.1)

def read_label_from_file():
    try:
        with open("/home/capstone/project/emotion_label.txt" , "r") as f:
            label = int(f.read().strip())
        return label
    except FileNotFoundError:
        print("Emotion label file not found!")
        return None

# Main emotion/music sequence
def run_emotion_music_sequence():
    global music_process, current_music_path, paused, music_start_time, paused_position
    if music_process:
        music_process.terminate()
        music_process = None
    with process_lock:
        print("START button pressed. Running STT sequence...")
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)

        result1 = subprocess.run(["python3", "/home/capstone/project/record_and_stt.py"])
        if result1.returncode != 0:
            print("record_and_stt.py failed. Aborting.")
            return
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)

        

        GPIO.output(LED_RED_PIN, GPIO.HIGH)

        result2 = subprocess.run(["python3", "/home/capstone/project/koelectra_small.py"])
        if result2.returncode != 0:
            print("koelectra_small.py failed. Aborting.")
            return
        GPIO.output(LED_RED_PIN, GPIO.LOW)
        label = read_label_from_file()
        if label == 0:
            GPIO.output(LED_emotion_happy , GPIO.HIGH)
            time.sleep(2)
            GPIO.output(LED_emotion_happy, GPIO.LOW)
        elif label == 1:
            GPIO.output(LED_emotion_sad , GPIO.HIGH)
            time.sleep(2)
            GPIO.output(LED_emotion_sad, GPIO.LOW)
        elif label == 2:
            GPIO.output(LED_emotion_angry , GPIO.HIGH)
            time.sleep(2)
            GPIO.output(LED_emotion_angry, GPIO.LOW)
               
        GPIO.output(LED_YELLOW_PIN , GPIO.HIGH)
        wait_for_feeling()
        feeling_selected.wait()

        GPIO.output(LED_YELLOW_PIN , GPIO.LOW)
        if music_process and music_process.poll() is None:
            print("Music already playing.")
        else:
            print("Starting music for selected feeling!")
            music_path = select_random_music_path()
            if music_path:
                current_music_path = music_path
                print(get_audio_device())
                music_process = subprocess.Popen(["mpg123", "-a", get_audio_device(), music_path])
                music_start_time = time.time()
                paused_position = 0
                paused = False
            else:
                print("Music selection failed.")

# Register GPIO events
GPIO.add_event_detect(START_PIN, GPIO.RISING, callback=lambda ch: threading.Thread(target=run_emotion_music_sequence).start(), bouncetime=500)
GPIO.add_event_detect(STOP_PIN, GPIO.RISING, callback=handle_stop_button, bouncetime=300)

# Main loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrupted")
finally:
    if music_process and music_process.poll() is None:
        music_process.terminate()
        music_process.wait()

    GPIO.cleanup()

# import RPi.GPIO as GPIO
# from music_select import select_random_music_path
# import subprocess
# import time
# import threading
# import signal

# # Pin definitions
# START_PIN = 17
# STOP_PIN = 16

# feeling_buttons = {
#     5: "healing",
#     6: "relief",
#     23: "energy",
#     24: "focus",
#     25: "love"
# }

# # GPIO setup
# GPIO.setwarnings(False)
# GPIO.setmode(GPIO.BCM)

# GPIO.setup(START_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# GPIO.setup(STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# for pin in feeling_buttons:
#     GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# # Globals
# music_process = None
# process_lock = threading.Lock()
# selected_feeling = None
# feeling_selected = threading.Event()
# last_stop_time = 0

# print("Ready. Press START button first, then select a feeling.")

# # Stop music callback
# def stop_music(channel):
#     global music_process , last_stop_time
#     current_time = time.time()

#     if current_time - last_stop_time < 1:
#         print("Double clik detected. Selecting new music")
#         if music_process and music_process.poll() is None:
#             music_process.terminate()
#             music_process.wait()
#             music_process = None
        
#         music_path = select_random_music_path()
#         if music_path:
#             print("Starting new music : {music_path}")
#             music_process = subprocess.Popen(["mpg123" , "-a" , "hw:4,0" , music_path])
#     else:
#         if music_process and music_process.poll() is None:
#             print("Pausing music play")
#             music_process.send_signal(signal.SIGSTOP)
#         elif music_process and music_process.poll() is not None:
#             print("Resuming music play")
#             music_process = subprocess.Popen(["mpg123" , "-a" , "hw:4,0" , music_path])
#         else:
#             print("No music is playing")

#     last_stop_time = current_time

# # Wait for feeling button press
# def wait_for_feeling():
#     global selected_feeling
#     print("Please press a feeling button...")
#     while True:
#         for pin, feeling in feeling_buttons.items():
#             if GPIO.input(pin) == GPIO.HIGH:
#                 selected_feeling = feeling
#                 with open("/home/capstone/project/want_feeling.txt", "w") as f:
#                     f.write(f"{feeling}\n")
#                 print(f"Feeling selected: {feeling}")
#                 feeling_selected.set()
#                 return
#         time.sleep(0.1)

# # Main emotion/music sequence
# def run_emotion_music_sequence():
#     global music_process
#     with process_lock:
#         print("START button pressed. Running STT sequence...")

#         result1 = subprocess.run(["python3", "/home/capstone/project/record_and_stt.py"])
#         if result1.returncode != 0:
#             print("record_and_stt.py failed. Aborting.")
#             return

#         result2 = subprocess.run(["python3", "/home/capstone/project/koelectra_small.py"])
#         if result2.returncode != 0:
#             print("koelectra_small.py failed. Aborting.")
#             return

#         wait_for_feeling()
#         feeling_selected.wait()

#         if music_process and music_process.poll() is None:
#             print("Music already playing.")
#         else:
#             print("Starting music for selected feeling!")
#             music_path = select_random_music_path()
#             if music_path:
#                 music_process = subprocess.Popen(["mpg123", "-a", "hw:4,0", music_path])
#             else:
#                 print("Music selet fail")

# # Register event detection
# try:
#     GPIO.remove_event_detect(START_PIN)
# except RuntimeError:
#     print(f"START_PIN remove_event_detect error: {e}")
# try:
#     GPIO.remove_event_detect(STOP_PIN)
# except RuntimeError:
#     pass

# print("Setting up GPIO event detection...")

# GPIO.add_event_detect(START_PIN, GPIO.RISING, callback=lambda ch: threading.Thread(target=run_emotion_music_sequence).start(), bouncetime=500)
# GPIO.add_event_detect(STOP_PIN, GPIO.RISING, callback=stop_music, bouncetime=300)

# # Main loop
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     print("Interrupted")
# finally:
#     if music_process and music_process.poll() is None:
#         music_process.terminate()
#         music_process.wait()
#     GPIO.cleanup()