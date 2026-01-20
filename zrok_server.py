#!/usr/bin/env python3
"""Backward-compatible entrypoint for Kaggle setup."""

import sys

from setup_script import main


if __name__ == "__main__":
    sys.exit(main())
