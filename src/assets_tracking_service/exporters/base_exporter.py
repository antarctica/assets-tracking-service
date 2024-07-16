from abc import ABC, abstractmethod


class Exporter(ABC):
    """Abstract base class for exporters."""

    @abstractmethod
    def export(self) -> None:
        """
        Public entrypoint for exporters.

        This method will vary based on the exporter requirements (i.e. writing a file, pushing to a service, etc.)
        """
        pass
