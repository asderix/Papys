import traceback
from typing import Tuple
from papys.request_response import Request, Response


class PAction:
    """
    Class providing a process function to execute any kind of actions.
    There are various implementations of this base class for different standard tasks.
    Feel free to make your own implementations. This base implementation gives you the option of passing your action as a function.
    In many cases, it is therefore not necessary to implement your own class.
    It is usually sufficient to implement the action logic in a function and have it executed with this base class.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        pf (function): The function to execute: func(Request, Response) -> Tuple[int, Request, Response]. It's recommended to use valid http status code for the first value in the response tuple. But you are free to use any integer. Handle it careful in the DAG.
    """

    def __init__(self, name: str = "", pf=None):
        self.name = name
        self.process_function = pf
        self._sub_actions = None

    @property
    def sub_actions(self):
        return self._sub_actions

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            return self.process_function(req, resp)
        except Exception as err:
            req.logger.log_error(
                "PAction function could not processed.", traceback.format_exc(), 120, req
            )
            resp.is_error = True
            resp.error = err            
            return 500, req, resp

    # >>
    def __rshift__(self, other):
        # TODO: Check type. List with Tuple or direct Tuple.
        self._sub_actions = other
        return self
