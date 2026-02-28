import argparse
import threading
import time
from datetime import datetime

import ArducamEvkSDK
from ArducamEvkSDK import Camera, Param


width = 4000
height = 3000

running = True
recording = False

raw_file = None
frame_times = []


def keyboard_thread():

    global recording
    global running
    global raw_file
    global frame_times

    while running:

        cmd = input().lower()

        if cmd == "r" and not recording:

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            filename = f"recording_{timestamp}.raw"

            print("Recording RAW:", filename)

            raw_file = open(filename,"wb")

            frame_times = []

            recording = True


        elif cmd == "s" and recording:

            print("Stopping recording")

            recording = False

            raw_file.close()

            if len(frame_times) > 1:

                duration = frame_times[-1] - frame_times[0]

                fps = (len(frame_times)-1)/duration

            else:

                fps = 0

            print("Average FPS:", fps)


        elif cmd == "q":

            running = False
            break



def main(config):

    global recording
    global raw_file
    global running
    global frame_times


    camera = Camera()

    param = Param()
    param.config_file_name = config
    param.bin_config = config.endswith(".bin")

    if not camera.open(param):

        raise Exception(camera.last_error)

    camera.init()
    camera.start()


    print("\nCommands:")
    print("R = Record RAW")
    print("S = Stop")
    print("Q = Quit\n")


    threading.Thread(target=keyboard_thread,daemon=True).start()


    while running:

        frame = camera.capture(1000)

        if frame is None:
            continue


        if recording:

            raw_file.write(frame.data)

            frame_times.append(time.time())


    camera.stop()
    camera.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c",
        "--config",
        required=True
    )

    args = parser.parse_args()

    main(args.config)
