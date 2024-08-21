#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This software is licensed under GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007

"""The global application data

The app_data instance keeps references to a few global objects.
"""
import queue
import threading
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppData:
    
    # the sub-threads started by the application
    thread_google_bos_gw: Optional[threading.Thread] = None

app_data = AppData()
