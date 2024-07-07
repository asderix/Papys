import json
import re
import urllib.parse
import traceback
from typing import Tuple, Any
from papys.route import PRoute
from papys.actions.core import PAction
from papys.http_methods import GET, POST, PUT, DELETE
from papys.request_response import Request, Response
from papys.hooks import PHook
from papys.config import PConfig
from papys.utils import PLogger, PathCache


_http_code_mapping = {
    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    203: "203 Non-Authoritative",
    204: "204 No Content",
    205: "205 Reset Content",
    206: "206 Partial Content",
    300: "300 Multiple Choices",
    301: "301 Moved Permanently",
    302: "302 Found (Moved Temporarily)",
    303: "303 See Other",
    304: "304 Not Modified",
    305: "305 Use Proxy",
    307: "307 Temporary Redirect",
    308: "308 Permanent Redirect",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    402: "402 Payment Required",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    406: "406 Not Acceptable",
    407: "407 Proxy Authentication Required",
    408: "408 Request Timeout",
    409: "409 Conflict",
    410: "410 Gone",
    411: "411 Length Required",
    412: "412 Precondition Failed",
    413: "413 Payload Too Large",
    414: "414 URI Too Long",
    415: "415 Unsupported Media Type",
    416: "416 Range Not Satisfiable",
    417: "417 Expectation Failed",
    421: "421 Misdirected Request",
    422: "422 Unprocessable Entity",
    423: "423 Locked",
    424: "424 Failed Dependency",
    425: "425 Too Early",
    426: "426 Upgrade Required",
    428: "428 Precondition Required",
    429: "429 Too Many Requests",
    431: "431 Request Header Fields Too Large",
    451: "451 Unavailable For Legal Reasons",
    500: "500 Internal Server Error",
    501: "501 Not Implemented",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
    504: "504 Gateway Timeout",
    505: "505 HTTP Version not supported",
    506: "506 Variant Also Negotiates",
    507: "507 Insufficient Storage",
    508: "508 Loop Detected",
    509: "509 Bandwidth Limit Exceeded",
    510: "510 Not Extended",
    511: "511 Network Authentication Required",
}

_get_actions = {}
_post_actions = {}
_put_actions = {}
_delete_actions = {}

_config = PConfig()
_logger = PLogger()
_path_cache = PathCache()

_initialize_hook = None
_finalize_hook = None


def _compile_path(path: str):
    pattern = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", path)
    return re.compile(pattern)


def _match_path(look_up: dict, path: str) -> Tuple[bool, PAction, Any, PHook]:
    assert look_up is not None, "Dictionary should not be None."
    for key, value in look_up.items():
        match = key.fullmatch(path)
        if match:
            return True, value[0], match.groupdict(), value[1]

    return False, None, None, None


def _add_actions(path: str, actions: list, hook: PHook = None):
    if actions is not None:
        for action in actions:
            match action[0]:
                case "GET":
                    _get_actions[_compile_path(path)] = action[1], hook
                case "POST":
                    _post_actions[_compile_path(path)] = action[1], hook
                case "PUT":
                    _put_actions[_compile_path(path)] = action[1], hook
                case "DELETE":
                    _delete_actions[_compile_path(path)] = action[1], hook


def _add_action(path: str, action: PAction, hook: PHook = None):
    if action is not None:
        match action[0]:
            case "GET":
                _get_actions[_compile_path(path)] = action[1], hook
            case "POST":
                _post_actions[_compile_path(path)] = action[1], hook
            case "PUT":
                _put_actions[_compile_path(path)] = action[1], hook
            case "DELETE":
                _delete_actions[_compile_path(path)] = action[1], hook


def _add_sub_routes(path: str, routes: list, hook: PHook):
    if routes is not None:
        for route_entry in routes:
            sub_hook = (
                hook >> route_entry.hook if hook is not None else route_entry.hook
            )
            for action_entry in route_entry.actions:
                _add_action(path + route_entry.path, action_entry, sub_hook)
            if route_entry.sub_routes:
                _add_sub_routes(
                    path + route_entry.path, route_entry.sub_routes, sub_hook
                )


def _execute_sub_actions(
    statusCode: int, req: Request, resp: Response, sub_actions: list
) -> Tuple[int, Request, Response]:
    result = statusCode, req, resp
    for sub_action in sub_actions:
        if sub_action[0] == statusCode:
            result = sub_action[1].process(result[1], result[2])
            match sub_action[1].sub_actions:
                case list():
                    result = _execute_sub_actions(
                        result[0], result[1], result[2], sub_action[1].sub_actions
                    )
                case _ if sub_action[1].sub_actions is not None:
                    result = _execute_sub_actions(
                        result[0], result[1], result[2], [sub_action[1].sub_actions]
                    )
    return result


def _execute_action_path(req: Request, resp: Response, action: PAction):
    result = action.process(req, resp)
    match action.sub_actions:
        case list():
            result = _execute_sub_actions(
                result[0], result[1], result[2], action.sub_actions
            )
        case PAction():
            result = _execute_sub_actions(
                result[0], result[1], result[2], [action.sub_actions]
            )
    return result


def _execute_hook(
    hook: PHook, req: Request, resp: Response
) -> Tuple[bool, int, Request, Response]:
    hook_result = hook.process_hook(req, resp)
    if not hook_result[0]:
        return (False,) + hook_result[1:]

    if hook.sub_hook is not None:
        sub_hook_result = _execute_hook(hook.sub_hook, hook_result[2], hook_result[3])
        if not sub_hook_result[0]:
            return (False,) + sub_hook_result[1:]
        else:
            return (True,) + sub_hook_result[1:]
    else:
        return (True,) + hook_result[1:]


def _handle_request(req: Request, resp: Response, actions: dict, alt: list = []):
    cache_result = _path_cache.check(req.request_method, req.path)
    if cache_result[0]:
        action_info = cache_result
    else:
        action_info = _match_path(actions, req.path)

    if not action_info[0]:
        resp.status_code = 404
        for alt_action in alt:
            check_result = _match_path(alt_action, req.path)
            if check_result[0]:
                resp.status_code = 405
        return resp.status_code, req, resp

    if cache_result[0] == False:
        _path_cache.add(req.request_method, req.path, action_info[1:])

    action = action_info[1]
    req.path_variables = action_info[2]
    hook = action_info[3]
    if hook is not None:
        hook_result = _execute_hook(hook, req, resp)
        if hook_result[0] is True:
            result = _execute_action_path(hook_result[2], hook_result[3], action)
        else:
            return hook_result[1:]
    else:
        result = _execute_action_path(req, resp, action)
    return result


def _create_request(environ: dict) -> Request:
    req = Request()
    req.logger = _logger
    req.global_config = _config
    req.path = environ.get("PATH_INFO", "")
    req.server_name = environ.get("SERVER_NAME", "")
    req.gateway_interface = environ.get("GATEWAY_INTERFACE", "")
    req.server_port = environ.get("SERVER_PORT", "")
    req.remote_host = environ.get("REMOTE_HOST", "")
    content_length_str = environ.get("CONTENT_LENGTH", "")
    req.content_length = int(content_length_str) if content_length_str.isdigit() else 0
    req.script_name = environ.get("SCRIPT_NAME", "")
    req.server_protocol = environ.get("SERVER_PROTOCOL", "")
    req.server_software = environ.get("SERVER_SOFTWARE", "")
    req.request_method = environ.get("REQUEST_METHOD", "")
    req.query_string = environ.get("QUERY_STRING", "")
    req.query_string_dict = {
        key: value[0] if len(value) == 1 else value
        for key, value in urllib.parse.parse_qs(req.query_string).items()
    }
    req.remote_addr = environ.get("REMOTE_ADDR", "")
    req.content_type = environ.get("CONTENT_TYPE", "")
    req.http_host = environ.get("HTTP_HOST", "")
    req.http_user_agent = environ.get("HTTP_USER_AGENT", "")
    req.http_accept = environ.get("HTTP_ACCEPT", "")
    req.http_accept_language = environ.get(
        "HTTP_ACCEPT_LANGUAGE", _config.accept_default_lang
    )
    req.http_accept_encoding = environ.get("HTTP_ACCEPT_ENCODING", "")
    req.http_connection = environ.get("HTTP_CONNECTION", "")
    req.http_cookie = environ.get("HTTP_COOKIE", "")

    cookie_dict = {}
    splitted_cookie = req.http_cookie.split(";")
    if splitted_cookie[0] is not "":
        for cookie in splitted_cookie:
            key, value = cookie.split("=")
            cookie_dict[key.strip()] = value

    req.parsed_cookie = cookie_dict

    req.authorization_header = environ.get("HTTP_AUTHORIZATION", None)
    req.http_upgrade_insecure_requests = environ.get(
        "HTTP_UPGRADE_INSECURE_REQUESTS", ""
    )
    req.http_sec_fetch_dest = environ.get("HTTP_SEC_FETCH_DEST", "")
    req.http_sec_fetch_mode = environ.get("HTTP_SEC_FETCH_MODE", "")
    req.http_sec_fetch_site = environ.get("HTTP_SEC_FETCH_SITE", "")
    req.http_sec_fetch_user = environ.get("HTTP_SEC_FETCH_USER", "")
    req.http_priority = environ.get("HTTP_PRIORITY", "")

    try:
        if req.content_length > 0:
            req.body_stream = environ.get("wsgi.input", None)
            if req.body_stream:
                req.body_raw = req.body_stream.read(req.content_length).decode("utf-8")
                req.body_str = str(req.body_raw)                
                req.body_json = json.loads(req.body_raw)
    except json.JSONDecodeError:
        req.body_json = None
    except RecursionError:
        req.body_json = None
    except TypeError:
        req.body_json = None
    except UnicodeDecodeError:
        req.body_raw = None
        req.body_str = None
        req.body_json = None
    except Exception as err:
        print(type(err))
        _logger.log_error(
            "Error creating body from WSGI input.", traceback.format_exc(), 100, req
        )

    return req


def _evaluate_content(resp: Response):
    if resp.json is not None:
        return [resp.json.encode("utf-8")]
    if resp.to_convert is not None:
        return [json.dumps(resp.to_convert).encode("utf-8")]
    if resp.custom_bytearray is not None:
        return [resp.custom_bytearray]
    return []


def set_config(config: PConfig):
    """
    Configer the application.

    Args:
        config (PConfig): Set a new configuration. Only needed if a change is required.
    """
    global _config, _logger
    _config = config
    _logger.log_level = _config.log_level
    _logger.log_info("set_config, config changed", 1)


def set_path_cache(cache: PathCache):
    """
    Define a own path cache implementation.

    Args:
        cache (PathCache): Set a new cache implementation. Only needed if a own implementation is needed.
    """
    global _path_cache
    _path_cache = cache


def set_logger(logger: PLogger):
    """
    Use a own logger.

    Args:
        logger (PLogger): Set a new logger. Only needed if a own logger is required.
    """
    global _logger
    _logger = logger


def set_initialize_hook(hook: PHook):
    """
    Configer the early start of the DAG.

    Args:
        hook (PHook): Set a hook which is processed bevor starting the DAG. You can chain hooks: Hook1 >> Hook2 if you need more than one.
    """
    global _initialize_hook
    _initialize_hook = hook
    _logger.log_info("set_initalize_hook, hook was set.", 2)


def set_finalize_hook(hook: PHook):
    """
    Configer the end of the DAG.

    Args:
        hook (PHook): Set a hook which s processed at the end of the DAG. You can chain hooks: Hook1 >> Hook2 if you need more than one.
    """
    global _finalize_hook
    _finalize_hook = hook
    _logger.log_info("set_finalize_hook, hook was set.", 2)


def list_supported_http_status_codes() -> list:
    """
    Ask for the supported http status codes in Papys.

    Returns:
        list: A list of strings with the supported http status codes.
    """
    return list(_http_code_mapping.keys())


def list_supported_http_methods() -> list:
    """
    Ask for the supported http method codes in Papys.

    Returns:
        list: A list of strings with the supported http methods. Actually: GET, POST, PUT, DELETE.
    """
    return ["GET", "POST", "PUT", "DELETE"]


def add_route(route: PRoute):
    """
    Add a route to the application.

    Args:
        route (PRoute): The route to add to Papys. You can chain routes: Route1 | Route2.

    Raises:
        Exception: If the route can not be added. The exception will also be logged.
    """
    try:
        _logger.log_info("add_route, start adding a route.", 3)
        _add_actions(route.path, route.actions, route.hook)
        _logger.log_info("add_route, _add_actions done.", 4)
        _add_sub_routes(route.path, route.sub_routes, route.hook)
        _logger.log_info("add_route, _add_sub_routes, done.", 5)
    except Exception as err:
        _logger.log_error("Error during adding a route.", traceback.format_exc(), 99)
        raise


def app(environ, start_response):
    """
    The WSGI compatible function which can be given to a WSGI server for the execution.
    See: https://peps.python.org/pep-0333/

    Args:
        environ (dict): Dict with the request information.
        start_response (function): A function which can be called for the response.
    """
    try:
        req = _create_request(environ)
        resp = Response()

        initialize_result = (
            _execute_hook(_initialize_hook, req, resp)
            if _initialize_hook is not None
            else (True, 0, None, None)
        )

        if initialize_result[0]:
            match environ.get("REQUEST_METHOD"):
                case "GET":
                    result = _handle_request(
                        req,
                        resp,
                        _get_actions,
                        [_post_actions, _put_actions, _delete_actions],
                    )
                    resp.status_code = result[0]
                case "POST":
                    result = _handle_request(
                        req,
                        resp,
                        _post_actions,
                        [_get_actions, _put_actions, _delete_actions],
                    )
                    resp.status_code = result[0]
                case "PUT":
                    result = _handle_request(
                        req,
                        resp,
                        _put_actions,
                        [_get_actions, _post_actions, _delete_actions],
                    )
                    resp.status_code = result[0]
                case "DELETE":
                    result = _handle_request(
                        req,
                        resp,
                        _delete_actions,
                        [_get_actions, _post_actions, _put_actions],
                    )
                    resp.status_code = result[0]

            if _finalize_hook:
                finalize_result = _execute_hook(_finalize_hook, req, resp)
                resp.status_code = finalize_result[1]

        else:
            resp.status_code = initialize_result[1]

        resp.set_header("Content-type", resp.content_type)

        match resp.status_code, environ.get("REQUEST_METHOD"), _config.post_convert_201:
            case 200, "POST", True:
                http_status_code = _http_code_mapping.get(
                    201, "500 Internal Server Error"
                )
            case _:
                http_status_code = _http_code_mapping.get(
                    resp.status_code, "500 Internal Server Error"
                )

        start_response(http_status_code, resp.list_headers())

        if 400 <= resp.status_code < 500:
            resp.reset_content()

        match resp.status_code:
            case 500:
                if _config.return_error500_body:
                    return [
                        json.dumps(
                            {
                                "errorCode": resp.status_code,
                                "errorMessage": str(resp.error),
                            }
                        ).encode("utf-8")
                    ]
                else:                    
                    return _evaluate_content(resp)
            case _:                
                return _evaluate_content(resp)

    except Exception as err:
        _logger.log_error(
            "Error during handling a request.", traceback.format_exc(), 101, req
        )
        start_response(_http_code_mapping.get(500, ""), resp.list_headers())
        return []
