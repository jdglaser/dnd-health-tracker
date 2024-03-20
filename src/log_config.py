import datetime
import json
import logging
import traceback

import click
from dateutil import tz

from src import app_config


class ColorFormatter(logging.Formatter):
    level_name_colors = {
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def formatMessage(self, record: logging.LogRecord) -> str:
        # If we have exception and traceback info, let's set it as the record message
        if record.exc_info and record.exc_info[1]:
            record.message = "".join(traceback.format_exception_only(record.exc_info[1]))[0:-1]  # Remove newline at end
        levelname = record.levelname
        color_levelname = self.level_name_colors[record.levelno](levelname)
        seperator = " " * (9 - len(record.levelname))
        record.levelprefix = f"{color_levelname}:{seperator}"
        return super().formatMessage(record)


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        stack_trace = (
            "".join(traceback.format_exception(record.exc_info[1])) if record.exc_info and record.exc_info[1] else None
        )
        formatted_exc = (
            "".join(traceback.format_exception_only(record.exc_info[1]))[0:-1]
            if record.exc_info and record.exc_info[1]
            else None
        )
        is_healthcheck = (
            record.name == "uvicorn.access"
            and hasattr(record, "args")
            and record.args is not None
            and isinstance(record.args, tuple)
            and len(record.args) >= 3
            and record.args[2] == "/health"
        )
        message = formatted_exc if formatted_exc else record.getMessage()
        local_time = datetime.datetime.fromtimestamp(record.created).astimezone()
        utc_time = local_time.astimezone(datetime.UTC)
        cst_time = local_time.astimezone(tz=tz.gettz("America/Chicago"))
        json_log = {
            "time": local_time.isoformat(),
            "utc_time": utc_time.strftime("%Y-%m-%d %I:%M:%S%p"),
            "cst_time": cst_time.strftime("%Y-%m-%d %I:%M:%S%p"),
            "level": record.levelname,
            "message": message,
            "stack_trace": stack_trace,
            "thread_name": record.threadName,
            "thread_id": record.thread,
            "process_id": record.process,
            "process_name": record.processName,
            "is_healthcheck": is_healthcheck,
            "environment": app_config.ENV.value,
        }
        return json.dumps(json_log)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    logger.setLevel(app_config.LOG_LEVEL)

    if app_config.ENV == app_config.Environment.LOCAL_DEV:
        formatter = ColorFormatter("%(levelprefix)s%(message)s")
    else:
        formatter = StructuredFormatter()

    ch = logging.StreamHandler()
    ch.setLevel(app_config.LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
