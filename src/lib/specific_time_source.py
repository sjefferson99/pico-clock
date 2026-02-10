class SpecificTimeSource:

    def __init__(self) -> None:
        pass
        
    def get_time(self) -> tuple:
        """
        Get the current time.
        Returns:
            A tuple with values: year, month, day, hours, minutes, seconds.
        """
        raise NotImplementedError(f"get_time method must be implemented by {self.__class__.__name__}")
    
    def set_time(self, time_tuple: tuple) -> None:
        """ 
        Set the current time.
        Args:
            time_tuple: A tuple with values: year, month, day, hours, minutes, seconds.
        """
        raise NotImplementedError(f"set_time method must be implemented by {self.__class__.__name__}")
    
    def travel_in_time(self, destination:str="Back to the future") -> None:
        """
        Travel in time to the specified destination.
        Args:
            destination: A string describing the time travel destination.
        """
        raise NotImplementedError(f"travel_in_time method must be implemented by {self.__class__.__name__}")