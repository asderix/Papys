import uuid
import email.utils
from datetime import datetime, timezone, timedelta
from papys.utils import PLogger
from papys.config import PConfig

COOKIE_SAME_SITE_STRICT = "Strict"
COOKIE_SAME_SITE_LAX = "Lax"
COOKIE_SAME_SITE_NONE = "None"


class Request:
    """
    A class that holds all information about a request.
    """

    def __init__(self):
        self._path = ""
        self._body_raw = None
        self._body_json = None
        self._body_str = None
        self._body_stream = None
        self._logger: PLogger = PLogger()
        self._path_variables = {}
        self._process_data = {}
        self._start_time = datetime.now(timezone.utc)
        self._process_id = str(uuid.uuid4())
        self._global_config = None
        self._server_name = ""
        self._gateway_interface = ""
        self._server_port = ""
        self._remote_host = ""
        self._content_length = 0
        self._script_name = ""
        self._server_protocol = ""
        self._server_software = ""
        self._request_method = ""
        self._query_string = ""
        self._query_string_dict = {}
        self._remote_addr = ""
        self._content_type = ""
        self._http_host = ""
        self._http_user_agent = ""
        self._http_accept = ""
        self._http_accept_language = ""
        self._http_accept_encoding = ""
        self._http_connection = ""
        self._http_cookie = ""
        self._parsed_cookie: dict | None = None
        self._http_authorization: str | None = None
        self._http_upgrade_insecure_requests = ""
        self._http_sec_fetch_dest = ""
        self._http_sec_fetch_mode = ""
        self._http_sec_fetch_site = ""
        self._http_sec_fetch_user = ""
        self._http_priority = ""
        self._user_info: dict | None = {}
        self._authentication_method: str | None = None

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, value: str):
        self._path = value

    @property
    def body_raw(self) -> str:
        return self._body_raw

    @body_raw.setter
    def body_raw(self, value: str):
        self._body_raw = value

    @property
    def body_json(self) -> str:
        return self._body_json

    @body_json.setter
    def body_json(self, value: str):
        self._body_json = value

    @property
    def body_str(self) -> str:
        return self._body_str

    @body_str.setter
    def body_str(self, value: str):
        self._body_str = value

    @property
    def body_stream(self):
        return self._body_stream

    @body_stream.setter
    def body_stream(self, value):
        self._body_stream = value

    @property
    def logger(self) -> PLogger:
        return self._logger

    @logger.setter
    def logger(self, value: PLogger):
        self._logger = value

    @property
    def path_variables(self) -> dict:
        return self._path_variables

    @path_variables.setter
    def path_variables(self, value: dict):
        self._path_variables = value

    @property
    def process_data(self) -> dict:
        return self._process_data

    @process_data.setter
    def process_data(self, value: dict):
        self._process_data = value

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @start_time.setter
    def start_time(self, value: datetime):
        self._start_time = value

    @property
    def process_id(self) -> str:
        return self._process_id

    @process_id.setter
    def process_id(self, value: str):
        self._process_id = value

    @property
    def global_config(self) -> PConfig:
        return self._global_config

    @global_config.setter
    def global_config(self, value: PConfig):
        self._global_config = value

    @property
    def server_name(self) -> str:
        return self._server_name

    @server_name.setter
    def server_name(self, value: str):
        self._server_name = value

    @property
    def gateway_interface(self) -> str:
        return self._gateway_interface

    @gateway_interface.setter
    def gateway_interface(self, value: str):
        self._gateway_interface = value

    @property
    def server_port(self) -> str:
        return self._server_port

    @server_port.setter
    def server_port(self, value: str):
        self._server_port = value

    @property
    def remote_host(self) -> str:
        return self._remote_host

    @remote_host.setter
    def remote_host(self, value: str):
        self._remote_host = value

    @property
    def content_length(self) -> int:
        return self._content_length

    @content_length.setter
    def content_length(self, value: int):
        self._content_length = value

    @property
    def script_name(self) -> str:
        return self._script_name

    @script_name.setter
    def script_name(self, value: str):
        self._script_name = value

    @property
    def server_protocol(self) -> str:
        return self._server_protocol

    @server_protocol.setter
    def server_protocol(self, value: str):
        self._server_protocol = value

    @property
    def server_software(self) -> str:
        return self._server_software

    @server_software.setter
    def server_software(self, value: str):
        self._server_software = value

    @property
    def request_method(self) -> str:
        return self._request_method

    @request_method.setter
    def request_method(self, value: str):
        self._request_method = value

    @property
    def query_string(self) -> str:
        return self._query_string

    @query_string.setter
    def query_string(self, value: str):
        self._query_string = value

    @property
    def query_string_dict(self) -> dict:
        return self._query_string_dict

    @query_string_dict.setter
    def query_string_dict(self, value: dict):
        self._query_string_dict = value

    @property
    def remote_addr(self) -> str:
        return self._remote_addr

    @remote_addr.setter
    def remote_addr(self, value: str):
        self._remote_addr = value

    @property
    def content_type(self) -> str:
        return self._content_type

    @content_type.setter
    def content_type(self, value: str):
        self._content_type = value

    @property
    def http_host(self) -> str:
        return self._http_host

    @http_host.setter
    def http_host(self, value: str):
        self._http_host = value

    @property
    def http_user_agent(self) -> str:
        return self._http_user_agent

    @http_user_agent.setter
    def http_user_agent(self, value: str):
        self._http_user_agent = value

    @property
    def http_accept(self) -> str:
        return self._http_accept

    @http_accept.setter
    def http_accept(self, value: str):
        self._http_accept = value

    @property
    def http_accept_language(self) -> str:
        return self._http_accept_language

    @http_accept_language.setter
    def http_accept_language(self, value: str):
        self._http_accept_language = value

    @property
    def http_accept_encoding(self) -> str:
        return self._http_accept_encoding

    @http_accept_encoding.setter
    def http_accept_encoding(self, value: str):
        self._http_accept_encoding = value

    @property
    def http_connection(self) -> str:
        return self._http_connection

    @http_connection.setter
    def http_connection(self, value: str):
        self._http_connection = value

    @property
    def http_cookie(self) -> str:
        return self._http_cookie

    @http_cookie.setter
    def http_cookie(self, value: str):
        self._http_cookie = value

    @property
    def parsed_cookie(self) -> dict:
        return self._parsed_cookie

    @parsed_cookie.setter
    def parsed_cookie(self, value: dict):
        self._parsed_cookie = value

    @property
    def authorization_header(self) -> str:
        return self._http_authorization

    @authorization_header.setter
    def authorization_header(self, value: str):
        self._http_authorization = value

    @property
    def http_upgrade_insecure_requests(self) -> str:
        return self._http_upgrade_insecure_requests

    @http_upgrade_insecure_requests.setter
    def http_upgrade_insecure_requests(self, value: str):
        self._http_upgrade_insecure_requests = value

    @property
    def http_sec_fetch_dest(self) -> str:
        return self._http_sec_fetch_dest

    @http_sec_fetch_dest.setter
    def http_sec_fetch_dest(self, value: str):
        self._http_sec_fetch_dest = value

    @property
    def http_sec_fetch_mode(self) -> str:
        return self._http_sec_fetch_mode

    @http_sec_fetch_mode.setter
    def http_sec_fetch_mode(self, value: str):
        self._http_sec_fetch_mode = value

    @property
    def http_sec_fetch_site(self) -> str:
        return self._http_sec_fetch_site

    @http_sec_fetch_site.setter
    def http_sec_fetch_site(self, value: str):
        self._http_sec_fetch_site = value

    @property
    def http_sec_fetch_user(self) -> str:
        return self._http_sec_fetch_user

    @http_sec_fetch_user.setter
    def http_sec_fetch_user(self, value: str):
        self._http_sec_fetch_user = value

    @property
    def http_priority(self) -> str:
        return self._http_priority

    @http_priority.setter
    def http_priority(self, value: str):
        self._http_priority = value

    @property
    def user_info(self) -> dict | None:
        return self._user_info

    @user_info.setter
    def user_info(self, value: dict | None):
        self._user_info = value

    @property
    def authentication_method(self) -> str | None:
        return self._authentication_method

    @authentication_method.setter
    def authentication_method(self, value: str | None):
        self._authentication_method = value

    def get_bearer_token(self) -> str:
        if self.authorization_header:
            parts = self.authorization_header.split()
            return parts[1] if len(parts) > 1 else None
        return None


class Response:
    """
    A class for all information of a response.

    """

    def __init__(self):
        self._status_code = 500
        self._content_type = "application/json"
        self._json = None
        self._to_convert = None
        self._custom_bytearray = None
        self._is_error = False
        self._error = None
        self._headers = {}
        self._cookies = {}

    @property
    def json(self) -> str:
        return self._json

    @json.setter
    def json(self, value: str):
        self._json = value

    @property
    def to_convert(self) -> dict:
        return self._to_convert

    @to_convert.setter
    def to_convert(self, value: dict):
        self._to_convert = value

    @property
    def custom_bytearray(self) -> bytearray:
        return self._custom_bytearray

    @custom_bytearray.setter
    def custom_bytearray(self, value: bytearray):
        self._custom_bytearray = value

    @property
    def status_code(self) -> int:
        return self._status_code

    @status_code.setter
    def status_code(self, value: int):
        self._status_code = value

    @property
    def is_error(self) -> bool:
        return self._is_error

    @is_error.setter
    def is_error(self, value: bool):
        self._is_error = value

    @property
    def error(self) -> object:
        return self._error

    @error.setter
    def error(self, value: object):
        self._error = value

    @property
    def content_type(self) -> str:
        return self._content_type

    @content_type.setter
    def content_type(self, value: str):
        self._content_type = value

    def set_header(self, name: str, value: str):
        self._headers[name] = value

    def list_headers(self) -> list:
        items = self._headers.items()
        headers_list = list(items)
        for key, value in self._cookies.items():
            headers_list.append(("Set-Cookie", f"{key}={value}"))
        return headers_list

    def add_cookie(self, name: str, value: str, attributes: list = []):
        attr_str = "; ".join(attributes)
        self._cookies[name] = value + "; " + attr_str if attr_str else value

    def remove_cookie(self, name: str):
        self._cookies.pop(name)

    def list_cookies(self) -> list:
        items = self._cookies.items()
        return list(items)

    def reset_content(self):
        self.json = None
        self.to_convert = None
        self.custom_bytearray = None

    def create_cookie_attributes(
        self,
        *,
        http_domain: str | None = None,
        expires: datetime | None = None,
        http_only: bool = False,
        max_age: int | None = None,
        partitioned: bool = False,
        path: str | None = None,
        secure: bool | None = None,
        same_site: str | None = None,
    ) -> list:
        """
        A function to create cookie attributes.

        """

        attrs = []
        if http_domain:
            attrs.append(f"Domain={http_domain}")
        if expires:
            attrs.append(f"Expires={email.utils.format_datetime(expires)}")
        if http_only:
            attrs.append("HttpOnly")
        if max_age:
            attrs.append(f"Max-Age={max_age}")
        if partitioned:
            attrs.append("Partitioned")
        if path:
            attrs.append(f"Path={path}")
        if secure:
            attrs.append("Secure")
        if same_site:
            attrs.append(f"SameSite={same_site}")

        return attrs

    def remove_cookie_from_client(self, cookie_name: str):
        self.add_cookie(
            cookie_name,
            "",
            self.create_cookie_attributes(expires=datetime.now() - timedelta(days=2)),
        )
