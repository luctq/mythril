class WarningIssues:
    def __init__(
        self,
        contract: str,
        swc_id: str,
        title: str,
        severity = None,
        filename: str = None,
        descriptions = ""
    ):
        self.contract = contract
        self.swc_id = swc_id
        self.title = title
        self.severity = severity
        self.filename = filename
        self.descriptions = descriptions
    
    @property
    def as_dict(self):
        """

        :return:
        """

        issue = {
            "title": self.title,
            "swc-id": self.swc_id,
            "contract": self.contract,
            "title": self.title,
            "severity": self.severity,
            "descriptions": self.descriptions,
        }

        return issue
