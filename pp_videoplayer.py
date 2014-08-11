import time
import os

from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_showmanager import ShowManager
from pp_pluginmanager import PluginManager
from pp_omxdriver import OMXDriver
from pp_gpio import PPIO
from pp_utils import Monitor

class VideoPlayer:
    """ plays a track using omxplayer
        See pp_imageplayer for common software design description
    """

    _CLOSED = "omx_closed"    #probably will not exist
    _STARTING = "omx_starting"  #track is being prepared
    _PLAYING = "omx_playing"  #track is playing to the screen, may be paused
    _ENDING = "omx_ending"  #track is in the process of ending due to quit or end of track


# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                         show_id,
                         root,
                        canvas,
                        show_params,
                        track_params ,
                         pp_dir,
                        pp_home,
                        pp_profile):

        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_id=show_id
        self.root=root
        self.canvas = canvas
        self.show_params=show_params
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile


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
        if self.omx_volume<>"":
            self.omx_volume= "--vol "+ str(int(self.omx_volume)*100) + ' '

        if self.track_params['omx-window']<>'':
            self.omx_window= self.track_params['omx-window']
        else:
            self.omx_window= self.show_params['omx-window']


        # get background image from profile.
        self.background_file=''
        if self.track_params['background-image']<>"":
            self.background_file= self.track_params['background-image']
        else:
            if self.track_params['display-show-background']=='yes':
                self.background_file= self.show_params['background-image']
            
        # get background colour from profile.
        if self.track_params['background-colour']<>"":
            self.background_colour= self.track_params['background-colour']
        else:
            self.background_colour= self.show_params['background-colour']
        
        self.centre_x = int(self.canvas['width'])/2
        self.centre_y = int(self.canvas['height'])/2
        
        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']

        # open the plugin Manager
        self.pim=PluginManager(self.show_id,self.root,self.canvas,self.show_params,self.track_params,self.pp_dir,self.pp_home,self.pp_profile) 

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()        
        
        # could put instance generation in play, not sure which is better.
        self.omx=OMXDriver(self.canvas)
        self.tick_timer=None
        self.init_play_state_machine()



    def play(self, track,
                     showlist,
                     end_callback,
                     ready_callback,
                     enable_menu=False):
                         
        #instantiate arguments
        self.track=track
        self.showlist=showlist
        self.ready_callback=ready_callback   #callback when ready to play
        self.end_callback=end_callback         # callback when finished
        self.enable_menu = enable_menu
 
        # callback to the calling object to e.g remove egg timer and enable click areas.
        if self.ready_callback<>None:
            self.ready_callback()

        # create an  instance of showmanager so we can control concurrent shows
        self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)

        #set up video window
        reason,message,comand,has_window,x1,y1,x2,y2= self.parse_window(self.omx_window)
        if reason =='error':
            self.mon.err(self,'omx window error: ' + message + ' in ' + self.omx_window)
            self.end_callback(reason,message)
        else:
            if has_window==True:
                self.omx_window= '--win " '+ str(x1) +  ' ' + str(y1) + ' ' + str(x2) + ' ' + str(y2) + ' " '
            else:
                self.omx_window=''

             # Control other shows at beginning
            reason,message=self.show_manager.show_control(self.track_params['show-control-begin'])
            if reason in ('error','killed'):
                self.end_callback(reason,message)
                self=None
            else:      
                #display content
                reason,message=self.display_content()
                if reason == 'error':
                    self.mon.err(self,message)
                    self.end_callback(reason,message)
                    self=None
                else:
                    # create animation events
                    reason,message=self.ppio.animate(self.animate_begin_text,id(self))
                    if reason=='error':
                        self.mon.err(self,message)
                        self.end_callback(reason,message)
                        self=None
                    else:
                        # start playing the video.
                        if self.play_state == VideoPlayer._CLOSED:
                            self.mon.log(self,">play track received")
                            self.start_play_state_machine(self.track)
                        else:
                            self.mon.err(self,'play track rejected')
                            self.end_callback('error','play track rejected')
                            self=None

    def terminate(self,reason):
        # circumvents state machine and does not wait for omxplayer to close
        if self.omx<>None:
            self.mon.log(self,"sent terminate to omxdriver")
            self.omx.terminate(reason)
            self.end('killed',' end without waiting for omxplayer to finish') # end without waiting
        else:
            self.mon.log(self,"terminate, omxdriver not running")
            self.end('killed','terminate, mplayerdriver not running')


    def input_pressed(self,symbol):
        if symbol[0:4]=='omx-':
            self.control(symbol[4])
            
        elif symbol =='pause':
            self.pause()

        elif symbol=='stop':
            self.stop()
        else:
            pass


    def get_links(self):
        return self.track_params['links']

            
                
# ***************************************
# INTERNAL FUNCTIONS
# ***************************************

    # respond to normal stop
    def stop(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,">stop received")
        self.quit_signal=True


    #toggle pause
    def pause(self):
        if self.play_state in (VideoPlayer._PLAYING,VideoPlayer._ENDING):
            self.omx.pause()
            return True
        else:
            self.mon.log(self,"!<pause rejected")
            return False
        
    # other control when playing
    def control(self,char):
        if self.play_state==VideoPlayer._PLAYING and char not in ('q'):
            self.mon.log(self,"> send control to omx: "+ char)
            self.omx.control(char)
            return True
        else:
            self.mon.log(self,"!<control rejected")
            return False



# ***********************
# sequencing
# **********************

    """self. play_state controls the playing sequence, it has the following values.
         I am not entirely sure the starting and ending states are required.
         - _closed - the omx process is not running, omx process can be initiated
         - _starting - omx process is running but is not yet able to receive controls
         - _playing - playing a track, controls can be sent
         - _ending - omx is doing its termination, controls cannot be sent
    """

    def init_play_state_machine(self):
        self.quit_signal=False
        self.play_state=VideoPlayer._CLOSED
 
    def start_play_state_machine(self,track):
        #initialise all the state machine variables
        #self.iteration = 0                             # for debugging
        self.quit_signal=False     # signal that user has pressed stop
        self.play_state=VideoPlayer._STARTING
        
        #play the selected track
        options=self.omx_audio+ " " + self.omx_volume + ' ' + self.omx_window + ' ' + self.show_params['omx-other-options']+" "
        self.omx.play(track,options)
        self.mon.log (self,'Playing track from show Id: '+ str(self.show_id))
        # and start polling for state changes
        self.tick_timer=self.canvas.after(50, self.play_state_machine)
 

    def play_state_machine(self):      
        if self.play_state == VideoPlayer._CLOSED:
            self.mon.log(self,"      State machine: " + self.play_state)
            return 
                
        elif self.play_state == VideoPlayer._STARTING:
            self.mon.log(self,"      State machine: " + self.play_state)
            
            # if omxplayer is playing the track change to play state
            if self.omx.start_play_signal==True:
                self.mon.log(self,"            <start play signal received from omx")
                self.omx.start_play_signal=False
                self.play_state=VideoPlayer._PLAYING
                self.mon.log(self,"      State machine: omx_playing started")
            self.tick_timer=self.canvas.after(50, self.play_state_machine)

        elif self.play_state == VideoPlayer._PLAYING:
            # self.mon.log(self,"      State machine: " + self.play_state)
            # service any queued stop signals
            if self.quit_signal==True:
                self.mon.log(self,"      Service stop required signal")
                self.stop_omx()
                self.quit_signal=False
                # self.play_state = VideoPlayer._ENDING
                
            # omxplayer reports it is terminating so change to ending state
            if self.omx.end_play_signal:                    
                self.mon.log(self,"            <end play signal received")
                self.mon.log(self,"            <end detected at: " + str(self.omx.video_position))
                if self.omx.end_play_reason<>'nice_day':
                    # deal with omxplayer not sending 'have a nice day'
                    self.mon.warn(self,"            <end detected at: " + str(self.omx.video_position))
                    self.mon.warn(self,"            <pexpect reports: "+self.omx.end_play_reason)
                    self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                self.play_state = VideoPlayer._ENDING
                self.ending_count=0
                
            self.tick_timer=self.canvas.after(200, self.play_state_machine)

        elif self.play_state == VideoPlayer._ENDING:
            self.mon.log(self,"      State machine: " + self.play_state)
            # if spawned process has closed can change to closed state
            self.mon.log (self,"      State machine : is omx process running? -  "  + str(self.omx.is_running()))
            if self.omx.is_running() ==False:
                self.mon.log(self,"            <omx process is dead")
                self.play_state = VideoPlayer._CLOSED
                self.end('normal','quit by user or system')
            else:
                self.ending_count+=1
                if self.ending_count>10:
                    # deal with omxplayer not terminating at the end of a track
                    self.mon.warn(self,"            <omxplayer failed to close at: " + str(self.omx.video_position))
                    self.mon.warn(self,'pexpect.before  is'+self.omx.xbefore)
                    self.omx.kill()
                    self.mon.warn(self,'omxplayer now  terminated ')
                    self.play_state = VideoPlayer._CLOSED
                    self.end('normal','end from omxplayer failed to terminate')
                else:
                    self.tick_timer=self.canvas.after(200, self.play_state_machine)

    def stop_omx(self):
        # send signal to stop the track to the state machine
        self.mon.log(self,"         >stop omx received from state machine")
        if self.play_state==VideoPlayer._PLAYING:
            self.omx.stop()
            return True
        else:
            self.mon.log(self,"!<stop rejected")
            return False




# *****************
# ending the player
# *****************

    def end(self,reason,message):

            # stop the plugin
            if self.track_params['plugin']<>'':
                self.pim.stop_plugin()

            # os.system("xrefresh -display :0")
            # abort the timer
            if self.tick_timer<>None:
                self.canvas.after_cancel(self.tick_timer)
                self.tick_timer=None
            
            if reason in ('error','killed'):
                self.end_callback(reason,message)
                self=None

            else:
                # normal end so do show control and animation

                # Control concurrent shows at end
                reason,message=self.show_manager.show_control(self.track_params['show-control-end'])
                if reason =='error':
                    self.mon.err(self,message)
                    self.end_callback(reason,message)
                    self=None
                else:
                   # clear events list for this track
                    if self.track_params['animate-clear']=='yes':
                        self.ppio.clear_events_list(id(self))
                    
                    # create animation events for ending
                    reason,message=self.ppio.animate(self.animate_end_text,id(self))
                    if reason=='error':
                        self.mon.err(self,message)
                        self.end_callback(reason,message)
                        self=None
                    else:
                        self.end_callback('normal',"track has terminated or quit")
                        self=None



# *****************
# displaying things
# *****************
    def display_content(self):

        #background colour
        if  self.background_colour<>'':   
           self.canvas.config(bg=self.background_colour)
            
        # delete previous content
        self.canvas.delete('pp-content')

        # background image
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Video background file not found: "+ self.background_img_file)
                self.end('error',"Video background file not found")
            else:
                pil_background_img=PIL.Image.open(self.background_img_file)
                self.background = PIL.ImageTk.PhotoImage(pil_background_img)
                self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                             int(self.canvas['height'])/2,
                                             image=self.background,
                                            anchor=CENTER,
                                            tag='pp-content')

        # execute the plugin if required
        if self.track_params['plugin']<>'':

            reason,message,self.track = self.pim.do_plugin(self.track,self.track_params['plugin'],)
            if reason <> 'normal':
                return reason,message

                          
        # display show text if enabled
        if self.show_params['show-text']<> '' and self.track_params['display-show-text']=='yes':
            self.canvas.create_text(int(self.show_params['show-text-x']),int(self.show_params['show-text-y']),
                                                    anchor=NW,
                                                  text=self.show_params['show-text'],
                                                  fill=self.show_params['show-text-colour'],
                                                  font=self.show_params['show-text-font'],
                                                  tag='pp-content')


        # display track text if enabled
        if self.track_params['track-text']<> '':
            self.canvas.create_text(int(self.track_params['track-text-x']),int(self.track_params['track-text-y']),
                                                    anchor=NW,
                                                  text=self.track_params['track-text'],
                                                  fill=self.track_params['track-text-colour'],
                                                  font=self.track_params['track-text-font'],
                                                  tag='pp-content')

        # display instructions if enabled
        if self.enable_menu== True:
            self.canvas.create_text(int(self.show_params['hint-x']),
                                                    int(self.show_params['hint-y']),
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                font=self.show_params['hint-font'],
                                                anchor=NW,
                                                tag='pp-content')

        self.canvas.tag_raise('pp-click-area')
        self.canvas.update_idletasks( )
        return 'normal',''


# ****************
# utilities
# *****************

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file

# original _
# warp _ or xy2


    def parse_window(self,line):
        
            fields = line.split()
            # check there is a command field
            if len(fields) < 1:
                    return 'error','no type field','',False,0,0,0,0
                
            # deal with original which has 1
            if fields[0]=='original':
                if len(fields) <> 1:
                        return 'error','number of fields for original','',False,0,0,0,0    
                return 'normal','',fields[0],False,0,0,0,0


            #deal with warp which has 1 or 5  arguments
            # check basic syntax
            if  fields[0] <>'warp':
                    return 'error','not a valid type','',False,0,0,0,0
            if len(fields) not in (1,5):
                    return 'error','wrong number of coordinates for warp','',False,0,0,0,0

            # deal with window coordinates    
            if len(fields) == 5:
                #window is specified
                if not (fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4].isdigit()):
                    return 'error','coordinates are not positive integers','',False,0,0,0,0
                has_window=True
                return 'normal','',fields[0],has_window,int(fields[1]),int(fields[2]),int(fields[3]),int(fields[4])
            else:
                # fullscreen
                has_window=True
                return 'normal','',fields[0],has_window,0,0,self.canvas['width'],self.canvas['height']



# *****************
#Test harness follows - THIS IS OUT OF DATE
# *****************

class Test:
    
    def __init__(self,track,show_params,track_params):

        self.track=track
        self.show_params=show_params
        self.track_params = track_params
        self.break_from_loop=False

        self.vp=None
    
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
        self.vp=VideoPlayer(1,my_window,self.canvas,self.show_params,self.track_params)
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
            self.end()
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
            self.end()
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
            self.end()
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

    track="/home/pi/pp_home/media/suits-short.mkv"
    
    #create a dictionary of options and call the test class
    show_params={'omx-other-options' : '',
                             'omx-audio' : '',
                             'speaker' : 'left',
                             'animate-begin' : 'out1 on 1\nout1 off 20',
                             'animate-end' : '',
                             'animate-clear': 'yes',
                             'omx-volume':'0',
                             'omx-window':'0 0 900 900'
                            }

    test=Test(track,show_params,show_params)





            
