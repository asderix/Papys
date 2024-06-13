from papys.hooks import PHook


class PRoute:
    """
    A route define a path, maybe holds sub-routes and the given actions mapped to the http method.
    Chain routes with: |. Route('/path') | Route('/sub-path') gets '/path/sub-path'.
    Add the action with >>. Example:
    Route('/path') >> [ ( GET, Action ) ]

    Args:
        path (str): String with the relativ path. Best practise: Start with / and end without. This doesn't get confusing when chaining routes Example. You can use variables with brackets. Example: /user/{user_id}/document/{doc_id}. You can use regular expression too. Variables are accessible with (example) Request.path_variables.get('user_id')
        hook (PHook): Optional a hook which will be processed befor the (sub-) route action will be processed. You cann chain hooks as well with: hook1 >> hook2.
    """

    def __init__(self, path: str = "/", hook: PHook | None = None):
        self._path = path
        self._sub_routes = []
        self._actions = {}
        self._hook = hook

    @property
    def path(self):
        return self._path

    @property
    def sub_routes(self):
        return self._sub_routes

    @property
    def actions(self):
        return self._actions

    @actions.setter
    def actions(self, value):
        self._actions = value

    @property
    def hook(self) -> PHook:
        return self._hook

    # |
    def __or__(self, other):
        if isinstance(other, PRoute):
            self.sub_routes.append(other)
        else:
            raise TypeError("The operand must be an instance of PRoute.")
        return self

    # >>
    def __rshift__(self, other):
        if isinstance(other, list):
            for element in other:
                if not isinstance(element, tuple):
                    raise TypeError(
                        "The operand must be an instance of list with tuple."
                    )
            self.actions = other
            # TODO Expand with method and action check?
        else:
            raise TypeError("The operand must be an instance of list.")
        return self
