import traceback
import requests
from typing import Tuple
from papys.actions.core import PAction
from papys.request_response import Request, Response


class KcAddUserAction(PAction):
    """
    This action creates a user in Keycloak from the information in the body of the request.
    The action logs in to Keycloak as a client using the client credential flow.
    The access data is to be passed to the action as a parameter.
    Make sure that the client used in Keycloak has the necessary rights to create a user.

    Use this action with a POST or PUT (not recommended) request. Send a JSON body with at least the following attributes:

    {
      "username": "<username>",
      "email": "<email address>",
      "password": "<password"
    }

    Args:
        name (str): The argument is only for you to describe the action in the source code. It's optional.
        kc_config (dict): Keycloak access parameter: { client_id: '<YOUR-CLIENT-ID>', client_secret: '<CLIENT-SECRET>', kc_host: '<KEYCLOAK_HOST>', realm: '<realm'}
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        kc_config: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._kc_config = kc_config
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            data = {
                "client_id": self._kc_config.get("client_id", ""),
                "client_secret": self._kc_config.get("client_secret", ""),
                "grant_type": "client_credentials",
            }

            response = requests.post(
                self._kc_config.get("kc_host", "")
                + "/realms/"
                + self._kc_config.get("realm", "")
                + "/protocol/openid-connect/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                access_token = response.json().get("access_token")

                body = req.body_json if req.body_json is not None else {}

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }

                data = {
                    "username": body.get("username", None),
                    "email": body.get("email", None),
                    "enabled": True,
                    "credentials": [
                        {
                            "type": "password",
                            "value": body.get("password", None),
                            "temporary": False,
                        }
                    ],
                }

                response = requests.post(
                    self._kc_config.get("kc_host", "")
                    + "/auth/admin/realms/"
                    + self._kc_config.get("realm", "")
                    + "/users",
                    json=data,
                    headers=headers,
                )

                match response.status_code:
                    case 201:
                        location_header = response.headers.get("Location")
                        if location_header:
                            kc_user_id = location_header.split("/")[-1]
                            kc_user_info = {
                                "kc_user_id": kc_user_id,
                                "username": body.get("username", None),
                                "email": body.get("email", None),
                            }
                            req.process_data["new-kc-user-info"] = kc_user_info
                            req.logger.log_info(
                                f"Keycloak user created. Keycloak user info: {kc_user_info}"
                            )

                    case 409:
                        req.logger.log_warning(
                            "KeycloakAddUserAction could not processed. Status code 409. User already exists.",
                            409,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 900, "message": "User already exists."}
                        return 409, req, resp
                    case 403:
                        req.logger.log_error(
                            "KeycloakAddUserAction could not processed. Status code 403. Access denied.",
                            traceback.format_exc(),
                            403,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 901, "message": "Access denied."}
                        return 403, req, resp
                    case 401:
                        req.logger.log_error(
                            "KeycloakAddUserAction could not processed. Status code 401. Server not authenticated",
                            traceback.format_exc(),
                            401,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {
                            "code": 902,
                            "message": "Server not authenticated.",
                        }
                        return 401, req, resp
                    case 404:
                        req.logger.log_error(
                            "KeycloakAddUserAction could not processed. Status code 404. IdP host not found.",
                            traceback.format_exc(),
                            404,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 903, "message": "IdP service not found."}
                        return 404, req, resp
                    case _:
                        req.logger.log_error(
                            f"KeycloakAddUserAction could not processed. Unknown status code: {response.status_code}.",
                            traceback.format_exc(),
                            999,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 999, "message": response.text}
                        return self._status_codes["error"], req, resp

            else:
                req.logger.log_error(
                    "KeycloakAddUserAction could not processed. Error login to the IdP server.",
                    traceback.format_exc(),
                    999,
                    req,
                )

            return self._status_codes["success"], req, resp
        except Exception as err:
            req.logger.log_error(
                "KeycloakAddUserAction could not processed.",
                traceback.format_exc(),
                160,
                req,
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp


class KcChangePwAction(PAction):
    """
    This action change the password of a user.
    You must use a Keycloak authentication hook and the user must be logged in accordingly (recommended).
    A user can only change their own password. This action reads the calling user from the req.process_data dictionary.
    The action logs in to Keycloak as a client using the client credential flow.
    The access data is to be passed to the action as a parameter.
    Make sure that the client used in Keycloak has the necessary rights to change a user password.

    Use this action with a PUT or POST (not recommended) request. Send a JSON body with at least the following attribute:

    {      
      "password": "<password"
    }

    Args:
        name (str): The argument is only for you to describe the action in the source code. It's optional.
        kc_config (dict): Keycloak access parameter: { client_id: '<YOUR-CLIENT-ID>', client_secret: '<CLIENT-SECRET>', kc_host: '<KEYCLOAK_HOST>', realm: '<realm'}
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        kc_config: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._kc_config = kc_config
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            data = {
                "client_id": self._kc_config.get("client_id", ""),
                "client_secret": self._kc_config.get("client_secret", ""),
                "grant_type": "client_credentials",
            }

            response = requests.post(
                self._kc_config.get("kc_host", "")
                + "/realms/"
                + self._kc_config.get("realm", "")
                + "/protocol/openid-connect/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                access_token = response.json().get("access_token")

                body = req.body_json if req.body_json is not None else {}

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }                

                data = {
                    "type": "password",
                    "value": body.get("password", None),
                    "temporary": False
                }

                response = requests.put(
                    self._kc_config.get("kc_host", "")
                    + "/auth/admin/realms/"
                    + self._kc_config.get("realm", "")
                    + "/users/" + req.user_info.get("sub", "")
                    + "/reset-password",
                    json=data,
                    headers=headers,
                )

                match response.status_code:
                    case 204:
                        pass

                    case 409:
                        req.logger.log_warning(
                            "KcChangePwAction could not processed. Status code 409. User already exists.",
                            409,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 900, "message": "User already exists."}
                        return 409, req, resp
                    case 403:
                        req.logger.log_error(
                            "KcChangePwAction could not processed. Status code 403. Access denied.",
                            traceback.format_exc(),
                            403,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 901, "message": "Access denied."}
                        return 403, req, resp
                    case 401:
                        req.logger.log_error(
                            "KcChangePwAction could not processed. Status code 401. Server not authenticated",
                            traceback.format_exc(),
                            401,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {
                            "code": 902,
                            "message": "Server not authenticated.",
                        }
                        return 401, req, resp
                    case 404:
                        req.logger.log_error(
                            "KcChangePwAction could not processed. Status code 404. IdP host not found.",
                            traceback.format_exc(),
                            404,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 903, "message": "IdP service not found."}
                        return 404, req, resp
                    case _:
                        req.logger.log_error(
                            f"KcChangePwAction could not processed. Unknown status code: {response.status_code}.",
                            traceback.format_exc(),
                            999,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 999, "message": response.text}
                        return self._status_codes["error"], req, resp

            else:
                req.logger.log_error(
                    "KcChangePwAction could not processed. Error login to the IdP server.",
                    traceback.format_exc(),
                    999,
                    req,
                )

            return self._status_codes["success"], req, resp
        except Exception as err:
            req.logger.log_error(
                "KcChangePwAction could not processed.",
                traceback.format_exc(),
                160,
                req,
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp

class KcDeleteUserAction(PAction):
    """
    This action delete a user.
    You must use a Keycloak authentication hook and the user must be logged in accordingly (recommended).
    A user can only delete himself. This action reads the calling user from the req.process_data dictionary.
    The action logs in to Keycloak as a client using the client credential flow.
    The access data is to be passed to the action as a parameter.
    Make sure that the client used in Keycloak has the necessary rights to delete a user.

    Use this action with a GET request. No parameter oder body is required.

    Args:
        name (str): The argument is only for you to describe the action in the source code. It's optional.
        kc_config (dict): Keycloak access parameter: { client_id: '<YOUR-CLIENT-ID>', client_secret: '<CLIENT-SECRET>', kc_host: '<KEYCLOAK_HOST>', realm: '<realm'}
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        kc_config: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._kc_config = kc_config
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            data = {
                "client_id": self._kc_config.get("client_id", ""),
                "client_secret": self._kc_config.get("client_secret", ""),
                "grant_type": "client_credentials",
            }

            response = requests.post(
                self._kc_config.get("kc_host", "")
                + "/realms/"
                + self._kc_config.get("realm", "")
                + "/protocol/openid-connect/token",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 200:
                access_token = response.json().get("access_token")                

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}",
                }                                

                response = requests.delete(
                    self._kc_config.get("kc_host", "")
                    + "/admin/realms/"
                    + self._kc_config.get("realm", "")
                    + "/users/"
                    + req.user_info.get("sub", ""),                    
                    headers=headers,
                )

                match response.status_code:
                    case 204:
                        pass

                    case 409:
                        req.logger.log_warning(
                            "KcDeleteUserAction could not processed. Status code 409. User already exists.",
                            409,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 900, "message": "User already exists."}
                        return 409, req, resp
                    case 403:
                        req.logger.log_error(
                            "KcDeleteUserAction could not processed. Status code 403. Access denied.",
                            traceback.format_exc(),
                            403,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 901, "message": "Access denied."}
                        return 403, req, resp
                    case 401:
                        req.logger.log_error(
                            "KcDeleteUserAction could not processed. Status code 401. Server not authenticated",
                            traceback.format_exc(),
                            401,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {
                            "code": 902,
                            "message": "Server not authenticated.",
                        }
                        return 401, req, resp
                    case 404:
                        req.logger.log_error(
                            "KcDeleteUserAction could not processed. Status code 404. IdP host not found.",
                            traceback.format_exc(),
                            404,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 903, "message": "IdP service not found."}
                        return 404, req, resp
                    case _:
                        req.logger.log_error(
                            f"KcDeleteUserAction could not processed. Unknown status code: {response.status_code}.",
                            traceback.format_exc(),
                            999,
                            req,
                        )
                        resp.is_error = True
                        resp.error = {"code": 999, "message": response.text}
                        return self._status_codes["error"], req, resp

            else:
                req.logger.log_error(
                    "KcDeleteUserAction could not processed. Error login to the IdP server.",
                    traceback.format_exc(),
                    999,
                    req,
                )

            return self._status_codes["success"], req, resp
        except Exception as err:
            req.logger.log_error(
                "KcDeleteUserAction could not processed.",
                traceback.format_exc(),
                160,
                req,
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp
