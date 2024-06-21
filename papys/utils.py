import uuid
from datetime import datetime, timezone
from typing import Tuple, Any


class PLogger:
    """
    The default logger of Papys. You can implement you own.
    This logger logs JSON formatted logs to the console using print function.

    Args:
        log_level (int): 1: Errors only. 2: Errors and warnings. 3: All incl. information. Default is 2. You can set this level also in the PConfig.
    """

    def __init__(self, log_level: int = 2):
        self._log_level = log_level

    @property
    def log_level(self) -> int:
        return self._log_level

    @log_level.setter
    def log_level(self, value: int):
        self._log_level = value

    def log_error(
        self, message: str, stack: str = "", log_code: int = 0, req=None
    ) -> str:
        """
        Log as an error.

        Args:
            message (str): The error message.
            stack (str): The error stack as string.
            log_code (int): A number you can refer in your code so you know exactly from where in your code the log entry is come from.
            req (Request): The request provided vom Papys. Giving the request, the Request.process_id is automatically logged. This helps to group log entries to the same client request.

        Returns:
            str: A uuid value which is also logged to the console. Using this id you can track and find the exact log output.
        """

        log_id = str(uuid.uuid4())
        print(
            {                
                "date": datetime.now(timezone.utc).isoformat(),
                "severity": "Error",
                "logId": log_id,
                "logCode": log_code,
                "message": message,
                "stack": stack,
                "processId": req.process_id if req is not None else "",
            }
        )
        return log_id

    def log_warning(self, message: str, log_code: int = 0, req=None) -> str:
        """
        Log as a warning.

        Args:
            message (str): The warning message.
            log_code (int): A number you can refer in your code so you know exactly from where in your code the log entry is come from.
            req (Request): The request provided vom Papys. Giving the request, the Request.process_id is automatically logged. This helps to group log entries to the same client request.

        Returns:
            str: A uuid value which is also logged to the console. Using this id you can track and find the exact log output.
        """

        if self.log_level > 1:
            log_id = str(uuid.uuid4())
            print(
                {                    
                    "date": datetime.now(timezone.utc).isoformat(),
                    "severity": "Warning",
                    "logId": log_id,
                    "logCode": log_code,
                    "message": message,
                    "processId": req.process_id if req is not None else "",
                }
            )
            return log_id

    def log_info(self, message: str, log_code: int = 0, req=None) -> str:
        """
        Log as an information.

        Args:
            message (str): The information message.
            log_code (int): A number you can refer in your code so you know exactly from where in your code the log entry is come from.
            req (Request): The request provided vom Papys. Giving the request, the Request.process_id is automatically logged. This helps to group log entries to the same client request.

        Returns:
            str: A uuid value which is also logged to the console. Using this id you can track and find the exact log output.
        """

        if self.log_level > 2:
            log_id = str(uuid.uuid4())
            print(
                {
                    "date": datetime.now(timezone.utc).isoformat(),
                    "severity": "Info",
                    "logId": log_id,
                    "logCode": log_code,
                    "message": message,
                    "processId": req.process_id if req is not None else "",
                }
            )
            return log_id


class PathCache:
    """
    A simple cache implementation for caching the requested pathes incl. variables.
    Important:
    The cache caches only the path, meaning for which path which (first) action incl. hooks has to called.
    In cases of many endpoints and tousends of clients requesting the same path regulary there is a potential
    to getting faster if this paths as not to be calculated every time.
    To shield the memory the max. size of the cache is limited. After reaching the limit the cache will be cleared and begins from zero.

    Args:
        max_size (int): The maximum of stored pathes in the cache before the cache will be cleared. Default is 100,000.
    """

    def __init__(self, max_size=100000):
        self.max_size = max_size
        self.get_cache = {}
        self.post_cache = {}
        self.put_cache = {}
        self.delete_cache = {}

    def check(self, method: str, path: str) -> Tuple[bool, Any, Any, Any]:
        try:
            match method:
                case "GET":
                    cache_result = self.get_cache.get(path, False)
                    if cache_result == False:
                        return False, None, None, None
                    else:
                        return (True,) + cache_result
                case "POST":
                    cache_result = self.post_cache.get(path, False)
                    if cache_result == False:
                        return False, None, None, None
                    else:
                        return (True,) + cache_result
                case "PUT":
                    cache_result = self.put_cache.get(path, False)
                    if cache_result == False:
                        return False, None, None, None
                    else:
                        return (True,) + cache_result
                case "DELETE":
                    cache_result = self.delete_cache.get(path, False)
                    if cache_result == False:
                        return False, None, None, None
                    else:
                        return (True,) + cache_result
        except:
            return False, None, None, None

    def add(self, method: str, path: str, action: Tuple[Any, Any, Any]):
        match method:
            case "GET":
                if len(self.get_cache) >= self.max_size:
                    self.get_cache.clear()
                self.get_cache[path] = action
            case "POST":
                if len(self.get_cache) >= self.max_size:
                    self.get_cache.clear()
                self.post_cache[path] = action
            case "PUT":
                if len(self.get_cache) >= self.max_size:
                    self.get_cache.clear()
                self.put_cache[path] = action
            case "DELETE":
                if len(self.get_cache) >= self.max_size:
                    self.get_cache.clear()
                self.delete_cache[path] = action
