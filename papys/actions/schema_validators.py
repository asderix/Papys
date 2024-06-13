import json
import jsonschema
from typing import Tuple
from jsonschema import validate
from actions.core import PAction
from request_response import Request, Response


class JsonRespValidatorAction(PAction):
    """
    Class providing a default JSON schema validation.
    This implementation uses the JSON schema validation of the standard library to check a JSON body against a JSON schema.
    It is recommended that both incoming and outgoing content is validated.
    This ensures that no unwanted information is sent out and minimizes the risk of incorrect or dangerous information being processed.
    This implementation checks the content of Response.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        schema (dict) : The JSON schema to validate against. See more: https://json-schema.org/
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        schema: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._schema = schema
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            content = (
                resp.to_convert
                if resp.to_convert is not None
                else json.loads(resp.json)
            )
            validate(instance=content, schema=self._schema)
            resp.status_code = self._status_codes["success"]
            return self._status_codes["success"], req, resp
        except jsonschema.exceptions.ValidationError as format_error:
            resp.is_error = True
            resp.error = format_error
            resp.status_code = self._status_codes["error"]
            return self._status_codes["error"], req, resp
        except Exception as err:
            req.logger.log_error(
                "JsonRespValidatorAction could not processed.", str(err), 123, req
            )
            resp.is_error = True
            resp.error = err
            resp.status_code = self._status_codes["error"]
            return self._status_codes["error"], req, resp


class JsonReqValidatorAction(PAction):
    """
    Class providing a default JSON schema validation.
    This implementation uses the JSON schema validation of the standard library to check a JSON body against a JSON schema.
    It is recommended that both incoming and outgoing content is validated.
    This ensures that no unwanted information is sent out and minimizes the risk of incorrect or dangerous information being processed.
    This implementation checks the content of Request.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        schema (dict) : The JSON schema to validate against. See more: https://json-schema.org/
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        schema: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._schema = schema
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            content = req.body_json
            validate(instance=content, schema=self._schema)
            resp.status_code = self._status_codes["success"]
            return self._status_codes["success"], req, resp
        except jsonschema.exceptions.ValidationError as format_error:
            resp.is_error = True
            resp.error = format_error
            resp.status_code = self._status_codes["error"]
            return self._status_codes["error"], req, resp
        except Exception as err:
            req.logger.log_error(
                "JsonReqValidatorAction could not processed.", str(err), 124, req
            )
            resp.is_error = True
            resp.error = err
            resp.status_code = self._status_codes["error"]
            return self._status_codes["error"], req, resp
