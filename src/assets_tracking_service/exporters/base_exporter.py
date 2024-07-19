from abc import ABC, abstractmethod
from typing import Self


class Exporter(ABC):
    """
    Abstract base class for providers.

    Defines a required interface all exporters must implement to allow operations to be performed across a set of
    exporters without knowledge of how each works.
    """

    @abstractmethod
    def export(self: Self) -> None:
        """
        Public entrypoint for exporters.

        This method will vary based on the exporter requirements (i.e. writing a file, pushing to a service, etc.)
        """
        pass
