
"""
    Meant for custom NEBULA exceptions
"""


class UnsupportedStage(Exception):
    """
        Exception for unsupported stage number
    """
    def __init__(self, message="Stage unsupported by NEBULA"):
        self.message = message
        super().__init__(self.message)