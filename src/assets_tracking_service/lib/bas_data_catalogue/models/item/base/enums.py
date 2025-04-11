from enum import Enum


class AccessType(Enum):
    """
    Item access types.

    Where 'NONE' is a fallback value that should not be needed (as items with no access would not be catalogued).
    """

    NONE: str = "none"
    PUBLIC: str = "public"
    BAS_ALL: str = "bas_all"
