
import time
import os

from pp_utils import Monitor
from pp_omxdriver import OMXDriver
from pp_gpio import PPIO
from Tkinter import *
import Tkinter as tk

class VideoPlayer:

    _CLOSED = "omx_closed"    #probably will not exist
    _STARTING = "omx_starting"  #track is being prepared
    _PLAYING = "omx_playing"  #track is playing to the screen, may be paused
    _ENDING = "omx_ending"  #track is in the process of ending due to quit or end of track


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
            canvas - the canvas onto which the video is to be drawn (not!!)
            cd - configuration dictionary
            track_params - config dictionary for this track overides cd
        """
        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_id=show_id
        self.show_params=show_params       #configuration dictionary for the videoplayer
        self.pp_home=pp_home
        self.canvas = canvas  #canvas onto which video should be played but isn't! Use as widget for alarm
        self.track_params=track_params
        
        # get config from medialist if there.
        if self.track_params['omx-audio']<>"":
            self.omx_audio= self.track_params['omx-audio']
        else:
            self.omx_audio= self.show_params['omx-audio']
        if self.omx_audio<>"": self.omx_audio= "-o "+ self.omx_audio
        
        if self.track_params['omx-volume']<>"":
            self.omx_volume= self.track_params['omx-volume']
        else:
            self.omx_volume= self.show_params['omx-volume']
        if self.omx_volume<>"": self.omx_volume= "--vol "+ str(int(self.omx_volume)*100) + ' '
        self.omx_volume=' '
        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()        
        
        # could put instance generation in play, not sure which is better.
        self.omx=OMXDriver(self.canvas)
        self._tick_timer=None
        self.error=False
        self.terminate_required=False
        self._init_play_state_machine()



    def play(self, track,
                     end_callback,
                     ready_callback,
                     enable_menu=False, 
                     starting_callback=None,
                     playing_callback=None,
                     ending_callback=None):
                         
        #instantiate arguments
        self.ready_callback=ready_callback   #callback when ready to play
        self.end_callback=end_callback         # callback when finished
        self.starting_callback=starting_callback  #callback during starting state
        self.playing_callback=playing_callback    #callback during playing state
        self.ending_callback=ending_callback      # callback during ending state
        # enable_menu is not used by videoplayer
 

        # create animation events
        error_text=self.ppio.animate(self.animate_begin_text,id(self))
        if error_text<>'':
            self.mon.err(self,error_text)
            self.error=True
            self._end()
            
        # and start playing the video.
        if self.play_state == VideoPlayer._CLOSED:
            self.mon.log(self,">play track received")
            self._start_play_state_machine(track)
            return True
        else:
            self.mon.log(self,"!< play track rejected")
            return False


    def key_pressed(self,key_name):
        if key_name=='':
            return
        elif key_name in ('p',' '):
            self._pause()
            return
        elif key_name=='escape':
            self._stop()
            return



    def button_pressed(self,button,edge):
        if button =='pause':
            self._pause()
            return
        elif button=='stop':
            self._stop()
            return


    def terminate(self,reason):
        # circumvents state machine
        self.terminate_required=True
        if self.omx<>None:
            self.mon.log(self,"sent terminate to omxdriver")
            self.omx.terminate(reason)
        else:
            self.mon.log(self,"terminate, omxdriver not running")
            self._end()
            
                

        
# ***************************************
# INTERNAL FUNCTIONS
# ***************************************

    # respond to normal stop
    def _stop(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received")
        self._stop_required_signal=True

    #respond to internal error
    def _error(self):
        self.error=True
        self._stop_required_signal=True

    #toggle pause
    def _pause(self):
        if self.play_state in (VideoPlayer._PLAYING,VideoPlayer._ENDING):
            self.omx.pause()
            return True
        else:
            self.mon.log(self,"!<pause rejected")
            return False
        
    # other control when playing, used?
    def _control(self,char):
        if self.play_state==VideoPlayer._PLAYING:
            self.mon.log(self,"> send control ot omx: "+ char)
            self.omx.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False

    # called to end omxdriver
    def _end(self):
            os.system("xrefresh -display :0")
            if self._tick_timer<>None:
                self.canvas.after_cancel(self._tick_timer)
                self._tick_timer=None
            if self.error==True:
                self.end_callback("error",'error')
                self=None 
            elif self.terminate_required==True:
                self.end_callback("killed",'killed')
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
                    self.end_callback("error",'error')
                    self=None

# ***************************************
# # PLAYING STATE MACHINE
# ***************************************

    """self. play_state controls the playing sequence, it has the following values.
         I am not entirely sure the starting and ending states are required.
         - _closed - the omx process is not running, omx process can be initiated
         - _starting - omx process is running but is not yet able to receive controls
         - _playing - playing a track, controls can be sent
         - _ending - omx is doing its termination, controls cannot be sent
    """

    def _init_play_state_machine(self):
        self._stop_required_signal=False
        self.play_state=VideoPlayer._CLOSED
 
    def _start_play_state_machine(self,track):
        #initialise all the state machine variables
        #self.iteration = 0                             # for debugging
        self._stop_required_signal=False     # signal that user has pressed stop
        self.play_state=VideoPlayer._STARTING
        
        #play the selected track
        options=self.omx_audio+ " " + self.omx_volume + ' ' + self.show_params['omx-other-options']+" "
        self.omx.play(track,options)
        self.mon.log (self,'Playing track from show Id: '+ str(self.show_id))
        # and start polling for state changes
        self._tick_timer=self.canvas.after(50, self._play_state_machine)
 

    def _play_state_machine(self):      
        if self.play_state == VideoPlayer._CLOSED:
            self.mon.log(self,"      State machine: " + self.play_state)
            return 
                
        elif self.play_state == VideoPlayer._STARTING:
            self.mon.log(self,"      State machine: " + self.play_state)
            
            # if omxplayer is playing the track change to play state
            if self.omx.start_play_signal==True:
                self.mon.log(self,"            <start play signal received from omx")
                self.omx.start_play_signal=False
                # callback to the calling object to e.g remove egg timer.
                if self.ready_callback<>None:
                    self.ready_callback()
                self.canvas.config(bg='black')
                self.canvas.delete(ALL)
                self.display_image()
                self.play_state=VideoPlayer._PLAYING
                self.mon.log(self,"      State machine: omx_playing started")
            self._do_starting()
            self._tick_timer=self.canvas.after(50, self._play_state_machine)

        elif self.play_state == VideoPlayer._PLAYING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            # service any queued stop signals
            if self._stop_required_signal==True:
                self.mon.log(self,"      Service stop required signal")
                self._stop_omx()
                self._stop_required_signal=False
                self.play_state = VideoPlayer._ENDING
                
            # omxplayer reports it is terminating so change to ending state
            if self.omx.end_play_signal:                    
                self.mon.log(self,"            <end play signal received")
                self.mon.log(self,"            <end detected at: " + str(self.omx.video_position))
                self.play_state = VideoPlayer._ENDING
                
            self._do_playing()
            self._tick_timer=self.canvas.after(200, self._play_state_machine)

        elif self.play_state == VideoPlayer._ENDING:
            self.mon.log(self,"      State machine: " + self.play_state)
            self._do_ending()
            # if spawned process has closed can change to closed state
            # self.mon.log (self,"      State machine : is omx process running? -  "  + str(self.omx.is_running()))
            if self.omx.is_running() ==False:
                self.mon.log(self,"            <omx process is dead")
                self.play_state = VideoPlayer._CLOSED
                self._end()
            else:
                self._tick_timer=self.canvas.after(200, self._play_state_machine)


    # allow calling object do things in each state by calling the appropriate callback
 
    def _do_playing(self):
        self.video_position=self.omx.video_position
        self.audio_position=self.omx.audio_position
        if self.playing_callback<>None:
                self.playing_callback() 

    def _do_starting(self):
        self.video_position=0.0
        self.audio_position=0.0
        if self.starting_callback<>None:
                self.starting_callback() 

    def _do_ending(self):
        if self.ending_callback<>None:
                self.ending_callback() 

    def _stop_omx(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,"         >stop omx received from state machine")
        if self.play_state==VideoPlayer._PLAYING:
            self.omx.stop()
            return True
        else:
            self.mon.log(self,"!<stop rejected")
            return False
# *****************
# image and text
# *****************
            
    def display_image(self):

        # display track text if enabled
        if self.track_params['track-text']<> '':
            self.canvas.create_text(int(self.track_params['track-text-x']),int(self.track_params['track-text-y']),
                                                    anchor=NW,
                                                  text=self.track_params['track-text'],
                                                  fill=self.track_params['track-text-colour'],
                                                  font=self.track_params['track-text-font'])

        self.mon.log(self,"Displayed  text ")
        
        self.canvas.update_idletasks( )


# *****************
#Test harness follows
# *****************

class Test:
    
    def __init__(self,track,show_params,track_params):
        
        self.track=track
        self.show_params=show_params
        self.track_params = track_params
        self.break_from_loop=False
    
        # create and instance of a Tkinter top level window and refer to it as 'my_window'
        my_window=Tk()
        my_window.title("VideoPlayer Test Harness")
    
        # change the look of the window
        my_window.configure(background='grey')
        window_width=200
        window_height=200
    
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
        canvas.grid(row=1,columnspan=2)
        
        # make sure focus is set on canvas.
        canvas.focus_set()
    
        self.canvas=canvas
        
        self.display_time = tk.StringVar()
        
    # define time/status display for selected track
        time_label = Label(canvas, font=('Comic Sans', 11),
                                fg = 'black', wraplength = 300,
                                textvariable=self.display_time, bg="grey")
        time_label.grid(row=0, column=0, columnspan=1)
    
        my_window.mainloop()
    
    def time_string(self,secs):
        minu = int(secs/60)
        sec = secs-(minu*60)
        return str(minu)+":"+str(int(sec))
    
    #key presses

    def e_terminate(self,event):
        self.terminate()
    
    def play_event(self,event):
        self.vp=VideoPlayer(self.canvas,self.show_params,self.track_params)
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
        self.vp=VideoPlayer(self.canvas,self.show_params)
        self.vp.play(self.track,self.what_next,self,do_ready,False,self.do_starting,self.do_playing,self.do_finishing)
    
    
    def next_event(self,event):
        self.break_from_loop=False
        self.vp.key_pressed('down')
    
    
    def what_next(self,reason,message):
        self.vp=None
        if reason=='killed':
            self._end()
        else:
            if self.break_from_loop==True:
                self.break_from_loop=False
                print "test harness: loop interupted"
                return
            else:
                self.vp=VideoPlayer(self.canvas,self.show_params)
                self.vp.play(self.track,self.what_next,self.do_starting,self.do_playing,self.do_finishing)
        

    
    def on_end(self,reason,message):
        self.vp=None
        print "Test Class: callback from VideoPlayer says: "+ message
        if reason=='killed':
            self._end()
        else:
            return
    
    def do_ready(self):
        print "test class message from Videoplayer: ready to play"
        return
    
    def do_starting(self):
        print "test class message from Videoplayer: do starting"
        return
    
    def do_playing(self):
        self.display_time.set(self.time_string(self.vp.video_position))
        # print "test class message from videoplayer: do playing"
        return
    
    def do_finishing(self):
        print "test class message from videoplayer: do ending"
        return
    
    
    def terminate(self):
        if self.vp ==None:
            self._end()
        else:
            self.vp.terminate('killed')
            return
        # kill the omxplayer if it is still running because window has been closed during a track playing.
            exit()

    def _end(self):
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

    track="/home/pi/pp_home/media/Suits-short.mkv"
    
    #create a dictionary of options and call the test class
    show_params={'omx-other-options' : '',
                             'omx-audio' : '',
                             'speaker' : 'left',
                             'animate-begin' : 'out1 on 1\nout1 off 20',
                             'animate-end' : '',
                             'animate-clear': 'yes'
                            }

    test=Test(track,show_params,show_params)





            
