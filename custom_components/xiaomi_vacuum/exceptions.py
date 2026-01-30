"""Exceptions used by the Dreame 1C MIIO protocol."""

class DeviceException(Exception):
    """Base exception for device communication errors."""
    pass


class DeviceError(DeviceException):
    """Exception raised when the device returns an error response."""
    def __init__(self, error):
        super().__init__(f"Device returned error: {error}")
        self.error = error


class RecoverableError(DeviceException):
    """Exception raised for recoverable MIIO errors (e.g. retry needed)."""
    def __init__(self, error):
        super().__init__(f"Recoverable error: {error}")
        self.error = error
