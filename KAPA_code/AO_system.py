### AO_system.py: Contains code for the operation of the AO system and its states
### Author: Emily Ramey
### Date: 08/07/2020

### Imports
import numpy as np
import pandas as pd
import sys
import time
import matplotlib.pyplot as plt
from transitions import Machine
from enum import Enum

class SystemState:
    def __init__(self, name):
        self.name = name
    
    def execute(self):
        print(self.name)

class States(Enum):
    SETTING_UP = SystemState('setting_up')
    RUNNING = SystemState('running')
    STOPPING = SystemState('stopping')
    IDLE = SystemState('idle')
    ERROR = SystemState('error')

class System(Machine):
    transitions = [
        ['next', States.SETTING_UP, States.RUNNING],
        ['next', States.STOPPING, States.IDLE],
        ['start', States.IDLE, States.SETTING_UP],
        ['stop', '*', States.STOPPING]
    ]
    
    def __init__(self):
        Machine.__init__(self, states=States, transitions=self.transitions, 
                         initial=States.IDLE, ignore_invalid_triggers=True)
        self.add_transition('error', '*', States.ERROR, after=self.state.value.execute)
        self.add_ordered_transitions([States.SETTING_UP, States.RUNNING])
        self.add_ordered_transitions([States.STOPPING, States.IDLE])