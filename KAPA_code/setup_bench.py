### setup_bench.py: Contains code for the operation of the setup bench, including states and state functions
### Author: Emily Ramey
### Date: 08/07/2020

### Imports
import enum
from transitions import Machine
import AO_util
import AO_devices
from AO_modes import *

#######################################
########## State functions ############
#######################################

def run_verify():
    # Check if TT and DM AO loops are open
    # Check if star magnitude is valid
    pass

def run_read():
    # Get observing mode
    # if LGS, get laser sub-mode
    # Get hyper mode
    # Get BS/Dichroic settings
    # Get target name
    # This needs more stuff - can't transfer between states
    pass

def run_prepare():
    # Open all AO loops
    # Turn on TRS
    # Open WYKO shutter
    # Set NIRC2 target name keyword
    # Reset LBWFS decount and LBWFS RMS WF error keywords
    # Copy FSM origin file appropriate for the observing mode
    pass

def run_set():
    # If LGS and 'LASER ZENITH', set AO rotator to a specific angle
    # Configure the focus manager
    # Set the FCS mode (tracking or manual) depending on the configuration
    # Set the SOD FCS to offset keyword or 'zero' in simulate mode (revisit this)
    # Set the WPS mode per configuration and set obwpname to 'ngs' for NGS mode
    # Set DAR parameters, including guidestar wavelength
    # Set TSS gold numbers (maybe only for LGS mode?)
    # Set AO bench params for observing mode
    pass

def run_move():
    # Move the SOD, AFS, and AFM stages
    pass

def run_configure():
    # Only for Trick mode?
    # See document for more
    pass

#######################################
######## State definitions ############
#######################################
@enum.unique
class SystemStates(enum.Enum):
    IDLE = "Idle mode"
    VERIFYING = "Verifying system state"
    READING = "Reading AO parameters"
    PREPARING = "Preparing to run setup bench"
    SETTING = "Setting AO Parameters"
    MOVING = "Moving stages"
    CONFIGURING = "Configuring TRICK"
    
    def run(self):
        print("Running state", self.name)
    
    def __init__(self, value):
        pass # TODO

sys_transitions = [
    ['next', SystemStates.IDLE, SystemStates.VERIFYING]
]
ops_transitions = [
    ['to_LGS', '*', OPSModes.LGS]
]

# Setup bench Finite State Machine
class SetupBench(Machine):
    
    def __init__(self, data):
        """ Initializes a finite state machine with 'state' as the state variable """
        self.data = data
        opsmode = OPSModes(self.data['aoopsmode']).name
        
        self.sys_machine = Machine(self, model_attribute='system_state', states=SystemStates, 
                                   transitions=sys_transitions, initial=SystemStates.IDLE)
        
        self.ops_machine = Machine(self, model_attribute='aoopsmode', states=OPSModes, 
                         transitions=ops_transitions, initial=opsmode)
        
        print(self.aoopsmode)
        print(self.system_state)
        
        # Set up callbacks
        for name, state in self.sys_machine.states.items():
            state.on_enter = [state.value.run]
        self.sys_machine.add_ordered_transitions(trigger='next')
    
    def run(self):
        return
        """
        Runs the setup bench code detailed in setup_bench.pro with data input by the user
        As I start to make more use of the FSM functionality, code will migrate from here to 
        other functions/transitions
        """