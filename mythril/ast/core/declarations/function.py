from abc import abstractmethod, ABCMeta
from mythril.ast.core.source_mapping.source_mapping import SourceMapping
class Function(SourceMapping, metaclass=ABCMeta):
    pass
