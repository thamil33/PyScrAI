import time

from agno_src.tools import Toolkit
from agno_src.utils.log import log_info


class SleepTools(Toolkit):
    def __init__(self, **kwargs):
        tools = []
        tools.append(self.sleep)

        super().__init__(name="sleep", tools=tools, **kwargs)

    def sleep(self, seconds: int) -> str:
        """Use this function to sleep for a given number of seconds."""
        log_info(f"Sleeping for {seconds} seconds")
        time.sleep(seconds)
        log_info(f"Awake after {seconds} seconds")
        return f"Slept for {seconds} seconds"
