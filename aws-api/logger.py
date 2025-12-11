import logging

class Logger(logging.Logger):
    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.propagate = False

    def get_level_name(self) -> str:
        return logging.getLevelName(self.level)

    def set_level(self, level: str) -> None:
        self.setLevel(level.upper())
        self.console_handler = ConsoleHandler(level)
        self.addHandler(self.console_handler)

class ConsoleHandler(logging.StreamHandler):
    def __init__(self, level: str) -> None:
        super().__init__()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
        )
        self.setFormatter(formatter)
        self.set_level(level)

    def set_level(self, level: str) -> None:
        self.setLevel(level.upper())

logging.basicConfig(level=logging.INFO)

# Set the custom logger class as the default logger class
logging.setLoggerClass(Logger)

# Use the custom logger
logger = logging.getLogger(__name__)