# -*- coding: utf-8 -*-
"""Entry point for the SolidFreeCAD alpha.10 standalone shell."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from sfc8 import show_standalone

show_standalone()
