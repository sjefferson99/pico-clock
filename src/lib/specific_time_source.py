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
    
    def set_time(self, year: int, month: int, day: int, hours: int, minutes: int, seconds: int) -> None:
        """ 
        Set the current time.
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            day: Day (1-31)
            hours: Hours (0-23)
            minutes: Minutes (0-59)
            seconds: Seconds (0-59)
        """
        raise NotImplementedError(f"set_time method must be implemented by {self.__class__.__name__}")
    
    def travel_in_time(self, destination:str="Back to the future") -> None:
        """
        Travel in time to the specified destination.
        Args:
            destination: A string describing the time travel destination.
        """
        raise NotImplementedError(f"travel_in_time method must be implemented by {self.__class__.__name__}")