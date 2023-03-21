class WarningIssues:
    def __init__(
        self,
        contract: str,
        swc_id: str,
        title: str,
        function: str = None,
        severity = None,
        filename: str = None,
        description = "",
        code: str = None,
        lineno: str = None,
    ):
        self.contract = contract
        self.function = function
        self.swc_id = swc_id
        self.title = title
        self.severity = severity
        self.filename = filename
        self.description = description
        self.code = code
        self.lineno = lineno
    
    @property
    def as_dict(self):
        """

        :return:
        """

        issue = {
            "title": self.title,
            "swc-id": self.swc_id,
            "contract": self.contract,
            "function": self.function,
            "title": self.title,
            "severity": self.severity,
            "description": self.description,
            "filename": self.filename,
            "lineno": self.lineno,
            "code": self.code
        }

        return issue
