import pexpect
import re
import sys

from threading import Thread
from time import sleep
from pp_utils import Monitor

"""
 pyomxplayer from https://github.com/jbaiter/pyomxplayer
 extensively modified by KenT

 omxdriver hides the detail of using the omxplayer command  from videoplayer
 This is meant to be used with videoplayer.py
 Its easy to end up with many copies of omxplayer.bin running if this class is not used with care. use pp_videoplayer.py for a safer interface.
 I found overlapping prepare and show did nor completely reduce the gap between tracks. Sometimes, in a test of this, one of my videos ran very fast when it was the second video 

 External commands
 ----------------------------
 __init__ just creates the instance and initialises variables (e.g. omx=OMXPlayer())
 play -  plays a track
 pause  - toggles pause
 control  - sends controls to omxplayer.bin  while track is playing (use stop and pause instead of q and p)
 stop - stops a video that is playing.
 terminate - Stops a video playing. Used when aborting an application.
 
 Advanced:
 prepare  - processes the track up to where it is ready to display, at this time it pauses.
 show  - plays the video from where 'prepare' left off by resuming from the pause.


Signals
----------
 The following signals are produced while a track is playing
         self.start_play_signal = True when a track is ready to be shown
         self.end_play_signal= True when a track has finished due to stop or because it has come to an end
 Also is_running() tests whether the sub-process running omxplayer is present.

"""

class OMXDriver(object):

    _STATUS_REXP = re.compile(r"V :\s*([\d.]+).*")
    _DONE_REXP = re.compile(r"have a nice day.*")

    _LAUNCH_CMD = '/usr/bin/omxplayer -s '  #needs changing if user has installed his own version of omxplayer elsewhere

    def __init__(self,widget):

        self.widget=widget
        
        self.mon=Monitor()
        self.mon.on()
        
        self.paused=None

    def control(self,char):
        self._process.send(char)

    def pause(self):
        self._process.send('p')       
        if not self.paused:
            self.paused = True
        else:
            self.paused=False

    def play(self, track, options):
        self._pp(track, options,False)

    def prepare(self, track, options):
        self._pp(track, options,True)
    
    def show(self):
        # unpause to start playing
        self._process.send('p')
        self.paused = False

    def stop(self):
        self._process.send('q')

    # kill the subprocess (omxplayer.bin). Used for tidy up on exit.
    def terminate(self,reason):
        self.terminate_reason=reason
        self._process.send('q')
        
    def terminate_reason(self):
        return self.terminate_reason
    

   # test of whether _process is running
    def is_running(self):
        return self._process.isalive()     

# ***********************************
# INTERNAL FUNCTIONS
# ************************************

    def _pp(self, track, options,  pause_before_play):
        self.paused=False
        self.start_play_signal = False
        self.end_play_signal=False
        self.terminate_reason=''
        track= "'"+ track.replace("'","'\\''") + "'"
        cmd = OMXDriver._LAUNCH_CMD + options +" " + track
        self.mon.log(self, "Send command to omxplayer: "+ cmd)
        self._process = pexpect.spawn(cmd)

        # uncomment to monitor output to and input from omxplayer.bin (read pexpect manual)
        fout= file('omxlogfile.txt','w')  #uncomment and change sys.stdout to fout to log to a file
        # self._process.logfile_send = sys.stdout  # send just commands to stdout
        self._process.logfile=fout  # send all communications to log file

        if pause_before_play:
            self._process.send('p')
            self.paused = True
            
        #start the thread that is going to monitor sys.stdout. Presumably needs a thread because of blocking
        self._position_thread = Thread(target=self._get_position)
        self._position_thread.start()

    def _get_position(self):
        self.start_play_signal = True  

        self.video_position=0.0
        self.audio_position=0.0
        
        while True:
            index = self._process.expect([OMXDriver._STATUS_REXP,
                                            pexpect.TIMEOUT,
                                            pexpect.EOF,
                                            OMXDriver._DONE_REXP])
            if index == 1:
                continue
            elif index in (2, 3):
                #Have a nice day detected
                self.end_play_signal=True
                break
            else:
                # presumably matches _STATUS_REXP so get video position
                # has a bug, position is not displayed for an audio track (mp3). Need to look at another field in the status, but how to extract it 
                self.video_position = float(self._process.match.group(1))
                self.audio_position = 0.0             
            #sleep is Ok here as it is a seperate thread. self.widget.after has funny effects as its not in the maion thread.
            sleep(0.05)

