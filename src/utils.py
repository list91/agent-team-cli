"""
Utility functions shared across the agent system
"""
import time


def get_timestamp() -> str:
    """
    Get formatted timestamp HH:MM:SS

    :return: Current time formatted as HH:MM:SS
    """
    return time.strftime('%H:%M:%S')
