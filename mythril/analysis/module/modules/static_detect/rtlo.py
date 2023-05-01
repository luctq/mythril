
import re
from mythril.analysis.module.base import DetectionModule, ModuleType
from mythril.solidity.ast.core.compilation_unit import StaticCompilationUnit

class RightToLeftOverride(DetectionModule):
    """
    Detect the usage of a Right-To-Left-Override (U+202E) character
    """
    def __init__(self):
        super().__init__(module_type=ModuleType.STATIC)
    
    def set_up(self, compilation_unit: StaticCompilationUnit):
        self.compilation_unit = compilation_unit

    def _execute(self):
        issues = []
        pattern = re.compile(".*\u202e.*".encode("utf-8"))

        for filename, source in self.compilation_unit.core.source_code.items():
            # Attempt to find all RTLO characters in this source file.
            original_source_encoded = source.encode("utf-8")
            start_index = 0

            # Keep searching all file contents for the character.
            while True:
                source_encoded = original_source_encoded[start_index:]
                result_index = source_encoded.find(self.RTLO_CHARACTER_ENCODED)

                # If we couldn't find the character in the remainder of source, stop.
                if result_index == -1:
                    break

                # We found another instance of the character, define our output
                idx = start_index + result_index

                relative = self.compilation_unit.core.crytic_compile.filename_lookup(filename).relative
                info = f"{relative} contains a unicode right-to-left-override character at byte offset {idx}:\n"

                # We have a patch, so pattern.find will return at least one result

                info += f"\t- {pattern.findall(source_encoded)[0]}\n"


                # Advance the start index for the next iteration
                start_index = idx + 1
