#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import confy


def main():
    """Run administrative tasks."""

    dot_env = os.path.join(os.getcwd(), '.env')
    if os.path.exists(dot_env):
            confy.read_environment_file()


    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'queuemanager.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
