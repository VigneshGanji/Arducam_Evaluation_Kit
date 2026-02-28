import argparse
import subprocess
import threading
import time
from datetime import datetime
from typing import Optional, cast

import ArducamEvkSDK
from ArducamEvkSDK import Camera, Param, LoggerLevel, Frame


WIDTH = 4000
HEIGHT = 3000


recording = False
running = True
ffmpeg_process = None

fps_counter = 0
fps_timer = time.time()


def log_callback(level, msg):
    print(msg)


# ---------- FFmpeg ----------

def start_ffmpeg(filename):

    global ffmpeg_process

    cmd = [

        "ffmpeg",
        "-y",

        "-f","rawvideo",

        "-pix_fmt","bayer_rggb8",   # change if colors wrong

        "-video_size",f"{WIDTH}x{HEIGHT}",

        "-use_wallclock_as_timestamps","1",

        "-i","-",

        "-vf","format=yuv420p",

        "-c:v","libx264",
        "-preset","ultrafast",

        filename
    ]

    ffmpeg_process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE
    )


def stop_ffmpeg():

    global ffmpeg_process

    if ffmpeg_process is None:
        return

    try:
        ffmpeg_process.stdin.close()
        ffmpeg_process.wait()
    except:
        pass

    ffmpeg_process = None


# ---------- Keyboard ----------

def keyboard_thread():

    global recording
    global running

    while running:

        cmd = input().strip().lower()

        if cmd == "r" and not recording:

            filename = "recording_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"

            print("Recording started:", filename)

            start_ffmpeg(filename)

            recording = True


        elif cmd == "s" and recording:

            print("Recording stopped")

            recording = False

            stop_ffmpeg()


        elif cmd == "q":

            print("Exiting")

            recording = False
            running = False

            stop_ffmpeg()

            return


# ---------- Main ----------

def main(config):

    global recording
    global running
    global fps_counter
    global fps_timer

    print("Arducam SDK:", ArducamEvkSDK.__version__)

    camera = Camera()

    param = Param()
    param.config_file_name = config
    param.bin_config = config.endswith(".bin")

    if not camera.open(param):
        raise Exception("Camera open failed")


    camera.set_message_callback(log_callback)
    camera.log_level = LoggerLevel.Info

    camera.init()
    camera.start()


    print("\nControls:")
    print("r + Enter → Record")
    print("s + Enter → Stop")
    print("q + Enter → Quit\n")


    threading.Thread(
        target=keyboard_thread,
        daemon=True
    ).start()


    try:

        while running:

            frame = cast(Optional[Frame], camera.capture(1000))

            if frame is None:
                continue


            # ---------- FPS Display ----------

            fps_counter += 1

            now = time.time()

            if now - fps_timer >= 1:

                fps = fps_counter / (now - fps_timer)

                print(f"Camera FPS: {fps:.2f}")

                fps_counter = 0
                fps_timer = now


            # ---------- Recording ----------

            if recording and ffmpeg_process:

                try:
                    ffmpeg_process.stdin.write(frame.data)
                except:
                    pass


    finally:

        stop_ffmpeg()

        camera.stop()
        camera.close()

        print("Camera closed")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-c","--config",required=True)

    args = parser.parse_args()

    main(args.config)
