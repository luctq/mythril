"""
    Check if an incorrect version of solc is used
"""

import re
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit
from mythril.analysis.warning_issue import WarningIssues
# group:
# 0: ^ > >= < <= (optional)
# 1: ' ' (optional)
# 2: version number
# 3: version number
# 4: version number

# pylint: disable=anomalous-backslash-in-string
PATTERN = re.compile(r"(\^|>|>=|<|<=)?([ ]+)?(\d+)\.(\d+)\.(\d+)")


class OutdateCompilerVersion(DetectionModule):
    """
    Check if an old version of solc is used
    """

    COMPLEX_PRAGMA_TXT = "is too complex"
    OLD_VERSION_TXT = "allows old versions"
    LESS_THAN_TXT = "uses lesser than"

    TOO_RECENT_VERSION_TXT = "necessitates a version too recent to be trusted. Consider deploying with 0.6.12/0.7.6/0.8.16"
    BUGGY_VERSION_TXT = (
        "is known to contain severe issues (https://solidity.readthedocs.io/en/latest/bugs.html)"
    )

    # Indicates the allowed versions. Must be formatted in increasing order.
    ALLOWED_VERSIONS = ["0.5.16", "0.5.17", "0.6.11", "0.6.12", "0.7.5", "0.7.6", "0.8.16"]

    # Indicates the versions that should not be used.
    BUGGY_VERSIONS = [
        "0.4.22",
        "^0.4.22",
        "0.5.5",
        "^0.5.5",
        "0.5.6",
        "^0.5.6",
        "0.5.14",
        "^0.5.14",
        "0.6.9",
        "^0.6.9",
        "0.8.8",
        "^0.8.8",
    ]

    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def _check_version(self, version):
        op = version[0]
        if op and op not in [">", ">=", "^"]:
            return self.LESS_THAN_TXT
        version_number = ".".join(version[2:])
        if version_number in self.BUGGY_VERSIONS:
            return self.BUGGY_VERSION_TXT
        if version_number not in self.ALLOWED_VERSIONS:
            if list(map(int, version[2:])) > list(map(int, self.ALLOWED_VERSIONS[-1].split("."))):
                return self.TOO_RECENT_VERSION_TXT
            return self.OLD_VERSION_TXT
        return None

    def _check_pragma(self, version):
        if version in self.BUGGY_VERSIONS:
            return self.BUGGY_VERSION_TXT
        versions = PATTERN.findall(version)
        if len(versions) == 1:
            version = versions[0]
            return self._check_version(version)
        if len(versions) == 2:
            version_left = versions[0]
            version_right = versions[1]
            # Only allow two elements if the second one is
            # <0.5.0 or <0.6.0
            if version_right not in [
                ("<", "", "0", "5", "0"),
                ("<", "", "0", "6", "0"),
                ("<", "", "0", "7", "0"),
            ]:
                return self.COMPLEX_PRAGMA_TXT
            return self._check_version(version_left)
        return self.COMPLEX_PRAGMA_TXT

    def _execute(self):
        """
        Detects pragma statements that allow for outdated solc versions.
        :return: Returns the relevant JSON data for the findings.
        """
        
        issues = []
        pragma = self.compilation_unit.pragma_directives
        disallowed_pragmas = []

        for p in pragma:
            # Skip any pragma directives which do not refer to version
            if len(p.directive) < 1 or p.directive[0] != "solidity":
                continue

            # This is version, so we test if this is disallowed.
            reason = self._check_pragma(p.version)
            if reason:
                disallowed_pragmas.append((reason, p))

        # If we found any disallowed pragmas, we output our findings.
        if disallowed_pragmas:
            for (reason, p) in disallowed_pragmas:
                info = ["Pragma version", p, f" {reason}\n"]
                print(info)

        if self.compilation_unit.solc_version not in self.ALLOWED_VERSIONS:
            if self.compilation_unit.solc_version in self.BUGGY_VERSIONS:
                issue = WarningIssues(
                        contract=self.compilation_unit.contracts_derived[0].name,
                        swc_id="102",
                        title="OUTDATE COMPILER VERSION",
                        severity="Low",
                        filename=pragma[0].source_mapping.filename.short,
                        description=f"Version {pragma[0].name} is not is not recommended for deployment.\nIt is recommended to use a recent version of the Solidity compiler.",
                        code=pragma[0].source_mapping.code.strip(),
                        lineno=pragma[0].source_mapping.get_lines_str(),
                    )
            else:
                issue = WarningIssues(
                        contract=self.compilation_unit.contracts_derived[0].name,
                        swc_id="SWC-102",
                        title="OUTDATE COMPILER VERSION",
                        severity="Low",
                        filename=pragma[0].source_mapping.filename.short,
                        description=f"Version {pragma[0].name} is not is not recommended for deployment.\nIt is recommended to use a recent version of the Solidity compiler.",
                        code=pragma[0].source_mapping.code.strip(),
                        lineno=pragma[0].source_mapping.get_lines_str(),
                    )
            issues.append(issue)
            
        
        return issues