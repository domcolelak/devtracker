#!/usr/bin/env python
"""DJANGO COMMAND-LINE UTILITY FOR ADMINISTRATIVE TASKS."""

import os
import sys


def main() -> None:
    """RUN ADMINISTRATIVE TASKS."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "COULD NOT IMPORT DJANGO. IS IT INSTALLED AND AVAILABLE ON YOUR PYTHONPATH "
            "ENVIRONMENT VARIABLE? DID YOU FORGET TO ACTIVATE A VIRTUAL ENVIRONMENT?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
