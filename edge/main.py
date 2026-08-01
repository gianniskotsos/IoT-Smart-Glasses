import subprocess
import sys
import time


def main():

    streamer = subprocess.Popen([sys.executable, "py_streamer.py"])

    client = subprocess.Popen([sys.executable, "pi_client.py"])

    try:
        while True:
            if streamer.poll() is not None:
                break
            if client.poll() is not None:
                break

            time.sleep(2)  

    except KeyboardInterrupt:
        print("\n[MAIN] KeyboardInterrupt detected. Terminating subprocesses...")
    finally:
        streamer.terminate()
        client.terminate()
        print("[MAIN] Subprocesses terminated. Exiting main program.")


if __name__ == "__main__":
    main()
