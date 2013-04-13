
import time
import os

from pp_utils import Monitor
from pp_mplayerdriver import mplayerDriver
from pp_gpio import PPIO

from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

class AudioPlayer:

    _CLOSED = "mplayer_closed"    #probably will not exist
    _STARTING = "mplayer_starting"  #track is being prepared
    _PLAYING = "mplayer_playing"  #track is playing to the screen, may be paused
    _ENDING = "mplayer_ending"  #track is in the process of ending due to quit or end of track
    _WAITING = "wait for timeout" # track has finished but timeout still running

    #_LEFT = "-af channels=2:1:0:0:1:1,resample=48000:1 "
   # _RIGHT = "-af channels=2:1:0:1:1:0,resample=48000:1 "
    #_STEREO = "-af channels=2,resample=48000:1 "

    _LEFT = "channels=2:1:0:0:1:1"
    _RIGHT = "channels=2:1:0:1:1:0"
    _STEREO = "channels=2"

# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                        show_id,
                        canvas,
                         pp_home,
                        show_params,
                        track_params ):
        """       
            canvas - the canvas onto which the background image is to be drawn
            show_params - configuration of show playing the track
            track_params - config dictionary for this track overrides show_params
        """

        self.mon=Monitor()
        self.mon.on()

        
        #instantiate arguments
        self.show_id=show_id
        self.show_params=show_params       #configuration dictionary for the videoplayer
        self.canvas = canvas  #canvas onto which video should be played but isn't! Use as widget for alarm
        self.pp_home=pp_home
        self.track_params=track_params

        # get duration (secs ) from profile
        self.duration= int(self.track_params['duration'])
        self.duration_limit=20*self.duration


        # get background image from profile.
        self.background_file  = self.track_params['background-image']


        # get audio sink from profile.
        if  self.track_params['mplayer-audio']<>"":
            self.mplayer_audio= self.track_params['mplayer-audio']
        else:
            self.mplayer_audio= self.show_params['mplayer-audio']
            
        # get audio volume from profile.
        if  self.track_params['mplayer-volume']<>"":
            self.mplayer_volume= self.track_params['mplayer-volume'].strip()
        else:
            self.mplayer_volume= self.show_params['mplayer-volume'].strip()
        self.volume_option= 'volume=' + self.mplayer_volume


        #get speaker from profile
        if  self.track_params['audio-speaker']<>"":
            self.audio_speaker= self.track_params['audio-speaker']
        else:
            self.audio_speaker= self.show_params['audio-speaker']

        if self.audio_speaker=='left':
            self.speaker_option=AudioPlayer._LEFT
        elif self.audio_speaker=='right':
            self.speaker_option=AudioPlayer._RIGHT
        else:
            self.speaker_option=AudioPlayer._STEREO

        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']


        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()

        # could put instance generation in play, not sure which is better.
        self.mplayer=mplayerDriver(self.canvas)
        self._tick_timer=None
        self.error=False
        self.terminate_me=False
        self._init_play_state_machine()



    def play(self, track,
                     end_callback,
                     ready_callback,
                     enable_menu=False, 
                     starting_callback=None,
                     playing_callback=None,
                     ending_callback=None):

        """
        play - plays the specified track, the first call after __init__
        track - full  path of track to play
        end_callback - callback when track ends (reason,message)
             reason = killed - return from a terminate with reason = killed
                           error - return because player or lower level has generated and runtime error
                           normal - anything else
            message = ant tesxt, used for debugging 
        ready_callback - callback when the track is ready to play, use to stop eggtimer etc.
        enable_menu - True if the track is to have a child show
        starting/playing/ending callback - called repeatedly in each state for show to display status, time etc.

        """
                         
        #instantiate arguments
        self.track=track
        self.ready_callback=ready_callback   #callback when ready to play
        self.enable_menu=enable_menu
        self.end_callback=end_callback         # callback when finished
        self.starting_callback=starting_callback  #callback during starting state
        self.playing_callback=playing_callback    #callback during playing state
        self.ending_callback=ending_callback      # callback during ending state
        # enable_menu is not used by AudioPlayer


        # select the sound sink
        if self.mplayer_audio<>"":
            if self.mplayer_audio=='hdmi':
                os.system("amixer -q -c 0 cset numid=3 2")
            else:
                os.system("amixer -q -c 0 cset numid=3 1")

        # callback to the calling object to e.g remove egg timer.
        if self.ready_callback<>None:
            self.ready_callback()

 
        # display image and text
        self.display_image()

        # create animation events
        error_text=self.ppio.animate(self.animate_begin_text,id(self))
        if error_text<>'':
            self.mon.err(self,error_text)
            self.error=True
            self._end('error',error_text)
 
        # and start playing the track.
        if self.play_state == AudioPlayer._CLOSED:
            self.mon.log(self,">play track received")
            self._start_play_state_machine()
            return True
        else:
            self.mon.log(self,"!< play track rejected")
            return False


    def key_pressed(self,key_name):
        """
        respond to user or system key  presses
        """
        if key_name=='':
            return
        elif key_name in ('p',' '):
            self._pause()
            return
        elif key_name=='escape':
            self._stop()
            return



    def button_pressed(self,button,edge):
        """
        respond to user button  presses
        """
        if button =='pause':
            self._pause()
            return
        elif button=='stop':
            self._stop()
            return


    def terminate(self,reason):
        """
        terminate the  player in special circumstances
        normal user termination if by key_pressed 'escape'
        reason will be killed or error
        """
        # circumvents state machine to terminate lower level and then itself.
        self.terminate_me=True
        if self.mplayer<>None:
            self.mon.log(self,"sent terminate to mplayerdriver")
            self.mplayer.terminate(reason)
            self._end('killed',' end without waiting') # end without waiting
        else:
            self.mon.log(self,"terminate, mplayerdriver not running")
            self._end('killed','terminate, mplayerdriver not running')
            
                

        
# ***************************************
# INTERNAL FUNCTIONS
# ***************************************

    #toggle pause
    def _pause(self):
        if self.play_state in (AudioPlayer._PLAYING,AudioPlayer._ENDING) and self.track<>'':
            self.mplayer.pause()
            return True
        else:
            self.mon.log(self,"!<pause rejected")
            return False
        
    # other control when playing, not currently used
    def _control(self,char):
        if self.play_state==AudioPlayer._PLAYING and self.track<>'':
            self.mon.log(self,"> send control to mplayer: "+ char)
            self.mplayer.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False

    # respond to normal stop
    def _stop(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received")
        self._stop_required_signal=True

    #respond to internal error by setting flags to cause state machine to stop player
    #use this rather than end if the driver and its spawned process might still be running
    def _error(self):
        self.error=True
        self._stop_required_signal=True


    # tidy up and end AudioPlayer.
    def _end(self,reason,message):
            # self.canvas.delete(ALL)
            # abort the timer
            if self._tick_timer<>None:
                self.canvas.after_cancel(self._tick_timer)
                self._tick_timer=None
            
            if self.error==True or reason=='error':
                self.end_callback("error",message)
                self=None
                
            elif self.terminate_me==True:
                self.end_callback("killed",message)
                self=None
            else:
               # clear events list for this track
                if self.track_params['animate-clear']=='yes':
                    self.ppio.clear_events_list(id(self))
                # create animation events for ending
                error_text=self.ppio.animate(self.animate_end_text,id(self))
                if error_text=='':
                    self.end_callback('normal',"track has terminated or quit")
                    self=None
                else:
                    self.mon.err(self,error_text)
                    self.end_callback("error",error_text)
                    self=None
                
      
# ***************************************
# # PLAYING STATE MACHINE
# ***************************************

    """self. play_state controls the playing sequence, it has the following values.
         I am not entirely sure the starting and ending states are required.
         - _closed - the mplayer process is not running, mplayer process can be initiated
         - _starting - mplayer process is running but is not yet able to receive controls
         - _playing - playing a track, controls can be sent
         - _ending - mplayer is doing its termination, controls cannot be sent
    """

    def _init_play_state_machine(self):
        self._stop_required_signal=False
        self.play_state=AudioPlayer._CLOSED
 
    def _start_play_state_machine(self):
        #initialise all the state machine variables
        self.duration_count = 0
        self._stop_required_signal=False     # signal that user has pressed stop

        #play the track

        options = self.show_params['mplayer-other-options'] + '-af '+ self.speaker_option+','+self.volume_option + ' '
        if self.track<>'':
            self.mplayer.play(self.track,options)
            self.mon.log (self,'Playing track from show Id: '+ str(self.show_id))
            self.play_state=AudioPlayer._STARTING
        else:
            self.play_state=AudioPlayer._PLAYING
        # and start polling for state changes and count duration
        self._tick_timer=self.canvas.after(50, self._play_state_machine)
 

    def _play_state_machine(self):
        self.duration_count+=1
           
        if self.play_state == AudioPlayer._CLOSED:
            self.mon.log(self,"      State machine: " + self.play_state)
            return 
                
        elif self.play_state == AudioPlayer._STARTING:
            self.mon.log(self,"      State machine: " + self.play_state)
            
            # if mplayer is playing the track change to play state
            if self.mplayer.start_play_signal==True:
                self.mon.log(self,"            <start play signal received from mplayer")
                self.mplayer.start_play_signal=False
                self.play_state=AudioPlayer._PLAYING
                self.mon.log(self,"      State machine: mplayer_playing started")
            self._do_starting()
            self._tick_timer=self.canvas.after(50, self._play_state_machine)

        elif self.play_state == AudioPlayer._PLAYING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            # service any queued stop signals
            if self._stop_required_signal==True or (self.duration_limit<>0 and self.duration_count>self.duration_limit):
                self.mon.log(self,"      Service stop required signa or timeout")
                # self._stop_required_signal=False
                if self.track<>'':
                    self._stop_mplayer()
                    self.play_state = AudioPlayer._ENDING
                else:
                    self.play_state = AudioPlayer._CLOSED
                    self._end('normal','stop required signa or timeout')

            # mplayer reports it is terminating so change to ending state
            if self.track<>'' and self.mplayer.end_play_signal:                    
                self.mon.log(self,"            <end play signal received")
                self.mon.log(self,"            <end detected at: " + str(self.mplayer.audio_position))
                self.play_state = AudioPlayer._ENDING
            self._do_playing()
            self._tick_timer=self.canvas.after(50, self._play_state_machine)

        elif self.play_state == AudioPlayer._ENDING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            self._do_ending()
            # if spawned process has closed can change to closed state
            # self.mon.log (self,"      State machine : is mplayer process running? -  "  + str(self.mplayer.is_running()))
            if self.mplayer.is_running() ==False:
                self.mon.log(self,"            <mplayer process is dead")
                if self._stop_required_signal==True:
                    self._stop_required_signal=False
                    self.play_state = AudioPlayer._CLOSED
                    self._end('normal','mplayer dead')
                elif self.duration_limit<>0 and self.duration_count<self.duration_limit:
                    self.play_state= AudioPlayer._WAITING
                    self._tick_timer=self.canvas.after(50, self._play_state_machine)
                else:
                    self.play_state = AudioPlayer._CLOSED
                    self._end('normal','mplayer dead')
            else:
                self._tick_timer=self.canvas.after(50, self._play_state_machine)
                
        elif self.play_state == AudioPlayer._WAITING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            if self._stop_required_signal==True or (self.duration_limit<>0 and self.duration_count>self.duration_limit):
                self.mon.log(self,"      Service stop required signal or timeout from wait")
                self._stop_required_signal=False
                self.play_state = AudioPlayer._CLOSED
                self._end('normal','mplayer dead')
            else:
                self._tick_timer=self.canvas.after(50, self._play_state_machine)
                    



    # allow calling object do things in each state by calling the appropriate callback
 
    def _do_playing(self):
        if self.track<>'':
            self.audio_position=self.mplayer.audio_position
        if self.playing_callback<>None:
                self.playing_callback() 

    def _do_starting(self):
        self.audio_position=0.0
        if self.starting_callback<>None:
                self.starting_callback() 

    def _do_ending(self):
        if self.ending_callback<>None:
                self.ending_callback() 

    def _stop_mplayer(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,"         >stop mplayer received from state machine")
        if self.play_state==AudioPlayer._PLAYING:
            self.mplayer.stop()
            return True
        else:
            self.mon.log(self,"!<stop rejected")
            return False

# *****************
# image and text
# *****************
            
    def display_image(self):
        self.canvas.config(bg='black')
        if self.background_file<>'' or self.show_params['show-text']<> '' or self.track_params['track-text']<> '' or self.enable_menu== True or self.track_params['clear-screen']=='yes':
            self.canvas.delete(ALL)
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Audio background file not found: "+ self.background_img_file)
                self._end('error',"Audio background file not found")
            else:
                pil_background_img=PIL.Image.open(self.background_img_file)
                self.background = PIL.ImageTk.PhotoImage(pil_background_img)
                self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                              image=self.background,
                                              anchor=CENTER)
                
        # display hint text if enabled
       
        if self.enable_menu== True:
            self.canvas.create_text(int(self.canvas['width'])/2, int(self.canvas['height']) - int(self.show_params['hint-y']),
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                font=self.show_params['hint-font'])

            
        # display show text if enabled
        if self.show_params['show-text']<> '':
            self.canvas.create_text(int(self.show_params['show-text-x']),int(self.show_params['show-text-y']),
                                                    anchor=NW,
                                                  text=self.show_params['show-text'],
                                                  fill=self.show_params['show-text-colour'],
                                                  font=self.show_params['show-text-font'])
            
        # display track text if enabled
        if self.track_params['track-text']<> '':
            self.canvas.create_text(int(self.track_params['track-text-x']),int(self.track_params['track-text-y']),
                                                    anchor=NW,
                                                  text=self.track_params['track-text'],
                                                  fill=self.track_params['track-text-colour'],
                                                  font=self.track_params['track-text-font'])

        self.mon.log(self,"Displayed background and text ")
        
        self.canvas.update_idletasks( )

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file     
            


# *****************
#Test harness follows
# *****************

class Test:
    
    def __init__(self,track,pp_dir,pp_home,show_params,ct):
        
        self.track=track
        self.show_params=show_params
        self.pp_home=pp_home
        self.ct = ct
        self.break_from_loop=False


        # create and instance of a Tkinter top level window and refer to it as 'my_window'
        my_window=Tk()
        my_window.title("AudioPlayer Test Harness")
    
        # change the look of the window
        my_window.configure(background='grey')
        window_width=1500
        window_height=900
    
        canvas_height=window_height
        canvas_width=window_width
    

        #defne response to main window closing
        my_window.protocol ("WM_DELETE_WINDOW", self.terminate)
        
        my_window.geometry("%dx%d+200+20" %(window_width,window_height))

        # Always use CTRL-Break key to close the program as a get out of jail
        my_window.bind("<Break>",self.e_terminate)
    
        my_window.bind("s", self.play_event)
        my_window.bind("p", self.pause_event)
        my_window.bind("q", self.stop_event)
        my_window.bind("l", self.loop_event)
        my_window.bind("n", self.next_event)
        
        #setup a canvas onto which will not be drawn the video!!
        canvas = Canvas(my_window, bg='black')
        canvas.config(height=canvas_height, width=canvas_width)
        canvas.pack()
        # make sure focus is set on canvas.
        canvas.focus_set()
        self.canvas=canvas

        #create an instance of PPIO and start polling
        self.ppio= PPIO()	
        self.ppio.init(pp_dir,pp_home,self.canvas,50,self.callback)
        self.ppio.poll()
         
        my_window.mainloop()

    
    def callback(self,index,name,edge):
        print name,  edge
        
    #key presses

    def e_terminate(self,event):
        self.terminate()
    
    def play_event(self,event):
        self.vp=AudioPlayer(self.canvas,self.pp_home,self.show_params,self.ct)
        self.vp.play(self.track,self.on_end,self.do_ready,False,self.do_starting,self.do_playing,self.do_finishing)
    
    # toggles pause
    def pause_event(self,event):
        self.vp.key_pressed('p')

    def stop_event(self,event):
        self.break_from_loop=True
        self.vp.key_pressed('escape')
    
    
    def loop_event(self,event):
      #just kick off the first track, callback decides what to do next
        self.break_from_loop=False
        self.vp=AudioPlayer(self.canvas,self.pp_home,self.show_params)
        self.vp.play(self.track,self.what_next,self,do_ready,False,self.do_starting,self.do_playing,self.do_finishing)
    
    
    def next_event(self,event):
        self.break_from_loop=False
        self.vp.key_pressed('down')
    
    
    def what_next(self,reason,message):
        self.vp=None
        if reason in ('killed','error'):
            self._end(reason,message)
        else:
            if self.break_from_loop==True:
                self.break_from_loop=False
                print "test harness: loop interupted"
                return
            else:
                self.vp=AudioPlayer(self.canvas,self.show_params)
                self.vp.play(self.track,self.what_next,self.do_starting,self.do_playing,self.do_finishing)
        

    
    def on_end(self,reason,message):
        self.vp=None
        print "Test Class: callback from AudioPlayer says: "+ message
        if reason in('killed','error'):
            self._end(reason,message)
        else:
            return
    
    def do_ready(self):
        print "test class message from AudioPlayer: ready to play"
        return
    
    def do_starting(self):
        print "test class message from AudioPlayer: do starting"
        return
    
    def do_playing(self):
        #self.display_time.set(self.time_string(self.vp.audio_position))
        # print "test class message from AudioPlayer: do playing"
        return
    
    def do_finishing(self):
        print "test class message from AudioPlayer: do ending"
        return
    
    
    def terminate(self):
        if self.vp ==None:
            self._end('killled','killled')
        else:
            self.vp.terminate('killed')
            return


    def _end(self,reason,message):
        self.ppio.terminate()
        exit()


# end of Test Class


if __name__ == '__main__':

    pp_dir=sys.path[0]
    if not os.path.exists(pp_dir+"/pipresents.py"):
        tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
        exit()

    #Initialise logging
    Monitor.log_path=pp_dir
    Monitor.global_enable=True

    track="/home/pi/pp_home/media/match0.wav"
    # track="/home/pi/pp_home/media/01.MP3"
    #track = ''
    home="/home/pi"
    
    #create a dictionary of options and call the test class
    show_params={'mplayer-other-options' : '',
                            'mplayer-audio' : 'local',
                             'audio-speaker' : 'stereo',
                             'duration' : '10',
                             'background-image' : '/home/pi/pp_home/media/sunset.gif',
                             'show-text': 'show text',
                             'show-text-font': 'arial 20 bold',
                             'show-text-colour': 'white',
                             'show-text-x': '400',
                             'show-text-y' : '100',
                             'track-text': 'track text',
                             'track-text-font': 'arial 20 bold',
                             'track-text-colour': 'white',
                             'track-text-x': '600',
                             'track-text-y' : '700',
                             'animate-begin' : 'out1 on 1\nout1 off 20',
                             'animate-end' : '',
                             'animate-clear': 'yes'
                             }
     
    test=Test(track, pp_dir, home,show_params,show_params)



                                            




   

