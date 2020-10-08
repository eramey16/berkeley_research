### setup_bench_trial.py: Test code for the AO bench setup protocol, adapted from setup_bench.pro
### This code is not intended to be the finished version; it is to be replaced with a more modular setup later
### Author: Emily Ramey
### Date: 08/11/20

import numpy as np
import pandas as pd
import sys
import time
import enum
import yaml
from transitions import Machine, State
import epics

######################################
######### State Machine ##############
######################################

class setup_bench(Machine):
    
    def __init__(self, data):
        """ Initializes a finite state machine with 'state' as the state variable """
        opsmode = OPSModes(self.data['aoopsmode']).name
        self.ops_machine = Machine(self, model_attribute='aoopsmode', states=OPSModes, 
                         transitions=ops_transitions, initial=opsmode)
        self.sys_machine = Machine(self, model_attribute='system_state', states=SystemStates, transitions=sys_transitions,
                         initial=SystemStates.IDLE)
        
        print(self.aoopsmode)
        print(self.system_state)
        
        self.data = data
        
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
        # Set state based on data
        self.trigger("to_"+OPSModes(self.data['aoopsmode']).name)
        if self.aoopsmode == OPSModes.NGS_STRAP:
            choose_SOD(self.aoopsmode)
        elif self.aoopsmode == OPSModes.NGS:
            self.aoopsmode['lst3pcrg'] = self.data['lst3pcrg']
        
        # Check if down tip-tilt or deformable mirror loop is open
        if dtlp.value != 0 or dmlp.value != 0:
            message("Please open all loops before running setup bench")
            return
        
        # Check r-magnitude (of guide star?) if state is archmode 0 or aoopsmode 1 or 2
        if self.data['rmag'] == 0 and (self.data['archmode']==0 or self.aoopsmode!=OPSModes.NGS):
            message('Please enter a valid R magnitude (not mR=0) and try again!')
            abort_acq(self.data)
            return
        
        # Clear abort flag
        abort_flag.clear()
        
        # Not sure what's happening here (ln 29 in setup_bench.pro)
        if self.aoopsmode==OPSModes.LGS:
            self.data['lgsmode'] = LGSModes.ZERO
            # What are these channels?
            aofmmove.write(0)
            aolpmove.write(0)
            message('Setting M3 to LGS FIXED')
        
        # Set data value to setup value
        self.data['obsdname'] = self.aoopsmode['obsdname']
        
        # Open loops
        message("Opening all loops")
        for loop in loops:
            loop.write(0)
        
        # Set rotator to proper VA (not sure what this means)
        if self.aoopsmode == OPSModes.NGS and self.data['tname']=="LASER ZENITH":
            # System variable dtor not explicitly passed to the function (ln 190 in setup_bench.pro)
            dtor = 1 # stand-in for unknown variable
            if np.abs(float(rotdest.value)/dtor) > 0.1 or rotmode.value!=ROTModes.TWO:
                message('Setting rotator to VA=0.0')
                rotdest.write(0.0*dtor)
                rotmode.write(ROTModes.TWO.value)
        
        # Turn telemetry recording on
        if self.data['simulate'] == 0:
            trsrec.write(7)
        
        # Set TT reference name on instrument
        message('Set AO ref. name for science inst.')
        self.data['tname'].replace('*', ' ')
        
        # Don't know what this spawned process does
        if self.data['instname'] == 'NIRC2':
            message('update object name...')
            message('Connecting to nirc2server to')
            # SPAWN, 'rsh waikoko -l nirc2eng object '+STRING(data.tname), tmp (ln 229)
            # I can't spawn a process from here, anyway
            # But why only NIRC2?
        
        # Write to TT (or AO?) reference name channel
        obptname.write(self.data['tname'])
        
        # reset LBWFS decount and LBWFS RMS WF (ln 234)
        # What does this mean?
        lbtmtocp.write(0.0)
        lgrmswf.write(300.0) # Why 300? Where does this go?
        
        # Set SOD stage
        message('Installing SOD '+self.aoopsmode['obsdname']) # Remember to slew afterward
        sod_stage.write(self.aoopsmode['obsdname'])
        # Set AFM stage
        message('Installing AFM '+self.aoopsmode['obamname'])
        afm_stage.write(self.aoopsmode['obamname'])
        # Set AFS stage
        message('Moving AFS to named position '+self.aoopsmode['obasname'])
        afs_stage.write(self.aoopsmode['obasname'])
        
        # Close WYKO shutter if not in simulate mode
        if wyko_shutter.value != WYKO_CLOSED:
            message('WYKO shutter is not closed')
            if not self.data['simulate']:
                message('Closing WYKO shutter')
                wyko_shutter.write(WYKO_CLOSED)
        else:
            message('WYKO shutter is closed')
        
        # Configure focus manager
        message('Configuring focus manager')
        aofcosoc.write(self.aoopsmode['aofcosoc'])
        aofctroc.write(self.aoopsmode['aofctroc'])
        aofcngct.write(1)
        aofclgct.write(self.aoopsmode['aofclgct'])
        aofclbct.write(0)
        
        # FCS??? Could rewrite this to be handled by a device class
        if obwfdsrc.value != self.aoopsmode['obwfdsrc']:
            message('Switching FCS to tracking or manual')
            obwfdsrc.write(self.aoopsmode['obwfdsrc'])
            obwfmove.write(1)
        
        # Set FCS C0
        # make sure that right '-N' or '-L' or '' is loaded
        # set the FSMs for the instrument
        ### Copies files (ln 307-320 of setup_bench.pro)
        # LOADFSMORI - what does this do???
        
        # set the offsets for the sodium dichroic or beamsplitter
        # these values were derived experimentally as to where the best focus of the FCS appears to be on the sky
        # (for some unexplained reason, this differs from the calibrated value). We don't know whether we have this problem
        # on Keck I or not. If we ever fix this problem, then the offsets should be removed.
        # SCE. Adapted for CLS from K1FST
        if self.data['simulate'] or self.data['telescope']!='Keck II':
            aofcc0so.write(0)
        else: # Keck II
            aofcc0so.write(-0.7 if self.aoopsmode['obsdname']=='sodiumDichroic' else -0.4)
        message('Setting SOD FCS offset to '+str(aofcc0so.value))
        
        ### ln 348 of setup_bench.pro
        message('Setting FCS C0 for '+self.data['instname'])
#         status=SET_FCS_FOR_INST(data.instname+suffix) # what does this do?
        
        # Sets WPS mode (why is there a move keyword if it's just a mode?)
        if obwpdsrc.value != self.aoopsmode['obwpdsrc']:
            message('Switching WPS to tracking or manual')
            obwpdsrc.write(self.aoopsmode['obwpdsrc'])
            obwpmove.write(1)
        
        # Not sure what this does
        if self.aoopsmode != OPSModes.LGS:
            obwpname.write('ngs')
        
        # Set DAR parameters
        # What are these channels?
        if self.data['darmode']>=0:
            message('Setting up DAR')
            guidwave.write(self.aoopsmode['guidwave']) 
            aodrzsim.write(1.0)
            aodrena.write(1.0)
            aotfenb.write(1) #TSSfoc
        
        # set up tss gold numbers
        ### No idea what this does :/
        aotsbsg = named_position(dev='tss', name='optbsstrap')
        aotssdg = named_position(dev='tss', name='optsodstrap')
        # No idea what this does at all
        write_all([aotsbsgx, aotsbsgy, aotsbsgz], -1*np.array(aotsbsg))
        write_all([aotssdgx, aotssdgy, aotssdgz], -1*np.array(aotssdg))
        aotsgold.write(self.aoopsmode['aotsgold'])
        
        ### This loop will take a while to figure out (ln 380)
        # Written by Randy Campbell in the IDL file
        # What do pntTTcur and pntrefcur refer to?
        # Why is setup.fsmset always 1?
        
        if self.data['offAxisFlag']: # Off-Axis observing
            get_TT_pnt(self.data) # Don't know what this does
        
        # Set FSM to different values depending on the mode
        aofm = self.data['pntTTcur'] if (not self.aoopsmode['tssset'] and 
                                         self.data['offAxisFlag']) else self.data['pntrefcur']
        # Set FSM
        message(f"Moving FSMs to (X={aofm[0]}, Y={aofm[1]})")
        aofmx.write(aofm[0]*1e-3)
        aofmy.write(aofm[1]*1e-3)
        aofmgo.write(1)
        
        # Set TSS, if specified
        if self.aoopsmode['tssset']:
            # Different settings for off-axis and on-axis modes
            aots = self.data['pntTTcur'] if self.data['offAxisFlag'] else self.data['pntrefcur']
            
            # Set TSS
            sod_name = 'optsodstrap' if sod_stage.value == 'sodiumDichroic' else 'optbsstrap'
            obtsz = named_position(dev='tss', name=sod_name, axis='z')
            
            # Don't really know what this does
            message(f"Moving TSS to (X={obtsz[0]}, Y={obtsz[1]}, Z={obtsz[2]})")
            aotsx.write(aots[0]*1e-3)
            aotsy.write(aots[1]*1e-3)
            aotsgo.write(1)
        
        # Set laser configuration
        message('Switching LTCS laser configuration ' + dtsensors[self.aoopsmode['dtsensor']])
        lsltlson.write(self.aoopsmode['lsltlson'])
        
        # Set WFO period
        if self.aoopsmode['aofotthr']!=0: # Why can/can't it be 0?
            message(f"Setting WFO period to {self.aoopsmode['aofotthr']}s")
            aofotthr.write(self.aoopsmode['aofotthr'])
        
        # SCE. Adapted for CLS from K1FST (ln 473)
        if self.aoopsmode['lst3pcrg'] != 0:
            message('Configuring M2-M5 integrator')
            lspntrci.write(1) # zero integrator
        
        # DT sensor (down tip-tilt sensor?)
        message('Switching DT sensor to ' + dtsensors[self.aoopsmode['dtsensor']])
        dtsensor.write(self.aoopsmode['dtsensor'])
        # Why does it wait for 1 second here?
        
        self.data['setuprmag'] = self.data['rmag'] # WHY
        # Determine STRAP and WFS equivalent magnitudes
        self.data['wfsrmag'] = effective_rmag(self.data['rmag'],aoopsmode=self.aoopsmode,
                                              obsdname=self.aoopsmode['obsdname'])
        self.data['straprmag'] = effective_rmag(self.data['rmag'],aoopsmode=self.aoopsmode,
                                                obsdname=self.aoopsmode['obsdname'],strap=True)
        
        # Set up STRAP
        if self.aoopsmode['stsetup']:
            message(f"Setting STRAP for effective mR={self.data['straprmag']}")
            if setup_strap(self.data['straprmag']) == -1:
                message('Strap settings not defined for this magnitude')
                return
        else:
            if ststate.value!=0: ststby.write(1)
            obswname.write("BLOCK")
        
        # Not sure what this does
        if self.aoopsmode['obsi'] != 0: # What's with the 1e-3?
            if np.abs(obsi.value*1e-3-self.aoopsmode['obsi']) > 0.01:
                obsi.write(self.aoopsmode['obsi']*1e-3)
        
        # Stop LBWFS? # Why?
        message('Halting LBWFS')
        aolbloop.write(0)
        aolblpstr.write('Halted')
        lblpnfra.write(0)
        aolbsvcg.write(0)
        aofclbct.write(0)
        lbtmtocp.write(0.0)
        
        # Close TTO # Not sure what that is
        txt = 'Closing TTO'
        if self.aoopsmode['aofomode']==1: txt += ', WFO'
        if self.aoopsmode['lst3pcre']==1: txt += ', M2-M5'
        message(txt + ' offload loops')
        
        aottmode.write(self.aoopsmode['aottmode'])
        if self.aoopsmode['aofomode']: aofomode.write(self.aoopsmode['aofomode'])
        if self.aoopsmode['lst3pcre']: lspntrce.write(self.aoopsmode['lst3pcre'])
        
        ### Wait for all the devices to slew here (ln 553)
        wait_for_devices()
        
        # What does this do?
        new_recapsmt='236'
        recapsmt.write(new_recapsmt)
        
        ### Turn off DTT and UTT dithering
        # Is this a flag?
        if dtdst.value==1: dtdst.write(0)
        if utdst.value==1: utdst.write(0)
        
        ### If loading a saved configuration, we are all done
        if self.data['archmode']!=0: return
        
        ### Set up the servos, gains # What do these do?
        dtservo.write([1,0,0,0,-1,0,0])
        utservo.write([1,0,0,0,-1,0,0])
        dmservo.write([1,0,0,0,-0.99,0,0])
        dtclp.write(1)
        utclp.write(1)
        dtgain.write(self.aoopsmode['dtgain'])
        dmgain.write(self.aoopsmode['dmgain'])
        utgain.write(self.aoopsmode['utgain'])
        
        ### Too much if/else logic here
        if self.aoopsmode==OPSModes.LGS:
            new_obpsxfs=0
            set_framerate(self.data['lgsfrrt'],prog=2)
            # Why only for LGS mode?
            message('Moving WND to named position ' + self.aoopsmode['obwnname'])
            obwnname.write(self.aoopsmode['obwnname'])
            
            # What are these variables for?
            binning=2
            prefix='24'
            self.data['guidestar']='LGS'
        else: # Not LGS Mode
            
            ### Need to set the plate scale here depending on the observation
            if data['instname'] in ['IF', 'ASTRA', 'OHANA']:
                binning = 1 if obpsxfs.value==3 else 2
                
                if wssmbin.value!=binning:
                    message('Changing binning mode')
                    set_framerate(wsfrrt.value, binning=binning)
            else:
                new_obpsxfs=0 # WHY
        
            # Determine what the AO settings should be as a function of magnitude          
            message('Setting WFS for effective mR='+data['wfsrmag'])
            # watao (what AO settings?) variable traces the status of the AO config
            data['watao'], data['wfbkgnd'] = ao_settings_vmag(data['wfsrmag'])
            
            # What are the possible AO settings?
            if data['watao']==-1:
                txt = """****Warning****                 
                        The AO settings are wrong      
                        Check the Rmag and B-Vmag      """
                message(txt)
            
            # What is this?
            if obpsxfs.value==2: prefix=10
            elif obpsxfs.value==3: prefix='06'
            else: prefix='24'
            
            ### Something about binning (ln 647)
        
        # What does this do? (ln 655)
        obpsxfs.write(new_obpsxfs)
        
        message('Setting up the lenslet config')
        wfs_config()
        
        # update the centroid gain 
        update_centroid_gain(self.data)
        
        ### Load the cog file (ln 665)
        aoacq_status(self.data)
        message('Bench setup done')
        
            