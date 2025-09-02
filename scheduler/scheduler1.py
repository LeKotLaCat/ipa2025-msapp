import time

from producer import produce


def scheduler():
    count = 0
    while True:

        now = time.time()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        ms = int((now % 1) * 1000)
        now_str_with_ms = f"{now_str}.{ms:03d}"
        print(f"[{now_str_with_ms}] run #{count}")

        try:
            produce("localhost", "192.168.1.1")
        except Exception as e:
            print(e)
            time.sleep(3)
        count += 1
        time.sleep(10)


if __name__ == "__main__":
    scheduler()
