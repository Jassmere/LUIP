import threading
import time

from app.scheduler.discovery_scheduler import run_discovery
from app.scheduler.scoring_scheduler import run_scoring
from app.scheduler.outreach_scheduler import run_outreach


class Scheduler:

    running = False

    @classmethod
    def start(cls):

        if cls.running:
            return

        cls.running = True

        print("")
        print("======================================")
        print("LUIP Automation Scheduler Started")
        print("======================================")
        print("")

        threading.Thread(
            target=cls.discovery_loop,
            daemon=True,
        ).start()

        threading.Thread(
            target=cls.scoring_loop,
            daemon=True,
        ).start()

        threading.Thread(
            target=cls.outreach_loop,
            daemon=True,
        ).start()

    @classmethod
    def shutdown(cls):

        cls.running = False

        print("")
        print("======================================")
        print("LUIP Scheduler Stopped")
        print("======================================")
        print("")

    @staticmethod
    def discovery_loop():

        while Scheduler.running:

            run_discovery()

            # every 30 minutes
            time.sleep(1800)

    @staticmethod
    def scoring_loop():

        while Scheduler.running:

            run_scoring()

            # every 15 minutes
            time.sleep(900)

    @staticmethod
    def outreach_loop():

        while Scheduler.running:

            run_outreach()

            # every 5 minutes
            time.sleep(300)