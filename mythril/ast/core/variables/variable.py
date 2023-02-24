from typing import TYPE_CHECKING, Optional, Union, List

from mythril.ast.core.solidity_types.type import Type
from mythril.ast.core.source_mapping.source_mapping import SourceMapping

class Variable(SourceMapping):
    def __init__(self):
        super().__init__()
        self._name: Optional[str] = None
        self._type: Optional[Type] = None
        self._is_constant = False
        self._is_immutable: bool = False
        self._initialized: Optional[bool] = None
        self._visibility: Optional[str] = None
    

    @property
    def name(self) -> Optional[str]:
        """
        str: variable name
        """
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
    
    @property
    def type(self) -> Optional[Union[Type, List[Type]]]:
        return self._type

    @type.setter
    def type(self, types: Union[Type, List[Type]]):
        self._type = types
    
    @property
    def is_constant(self) -> bool:
        return self._is_constant

    @is_constant.setter
    def is_constant(self, is_cst: bool):
        self._is_constant = is_cst

    @property
    def is_immutable(self) -> bool:
        """
        Return true of the variable is immutable

        :return:
        """
        return self._is_immutable

    @is_immutable.setter
    def is_immutable(self, immutablility: bool) -> None:
        self._is_immutable = immutablility
    
    @property
    def visibility(self) -> Optional[str]:
        """
        str: variable visibility
        """
        return self._visibility

    @visibility.setter
    def visibility(self, v: str) -> None:
        self._visibility = v

    @property
    def initialized(self) -> Optional[bool]:
        """
        boolean: True if the variable is initialized at construction
        """
        return self._initialized

    @initialized.setter
    def initialized(self, is_init: bool):
        self._initialized = is_init    
