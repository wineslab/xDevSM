from abc import ABC, abstractmethod


class BasexDevSMXapp(ABC):

    @abstractmethod
    def send(self, *args, **kwargs):
        """
        Abstract method to send SM-based messages.
        Must be implemented by subclasses.
        """
        pass
    

    @abstractmethod
    def handle(self, xapp, summary, sbuf):
        """
        Abstract method to handle incoming SM-based messages.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def terminate(self, signum, frame):
        """
        Abstract method for terminating the xApp.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_ran_function_description(self, json_ran_info):
        """
        Abstract method to retrieve the RAN function description.
        Must be implemented by subclasses.
        """
        pass