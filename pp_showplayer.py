
import time
import os

from pp_utils import Monitor
from pp_gpio import PPIO

from Tkinter import *
import Tkinter as tk
from pp_showmanager import ShowManager


class ShowPlayer:


# ***************************************
# EXTERNAL COMMANDS
# ***************************************

    def __init__(self,
                        show_id,
                        canvas,
                         pp_home,
                        show_params,
                        track_params,
                         pp_profile):
        """       
            canvas - the canvas onto which something could be drawn
            show_params - configuration of show playing the track
            track_params - config dictionary for this track overrides show_params
        """

        self.mon=Monitor()
        self.mon.on()

        
        #instantiate arguments
        self.show_id=show_id
        self.show_params=show_params       #configuration dictionary for the show
        self.canvas = canvas  #canvas onto which something could be drawn or use as widget for alarm
        self.pp_home=pp_home
        self.track_params=track_params
        self.pp_profile=pp_profile

 
        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()

        # could put instance generation in play, not sure which is better.
        self.error=False
        self.terminate_me=False


    def play(self, showlist,
                     end_callback,
                     ready_callback,
                     enable_menu=False, 
                     starting_callback=None,
                     playing_callback=None,
                     ending_callback=None):

        """
        play - plays the specified track, the first call after __init__
        showlist - showlist to access shows to control
        end_callback - callback when track ends (reason,message)
             reason = killed - return from a terminate with reason = killed
                           error - return because player or lower level has generated and runtime error
                           normal - anything else
            message = any text, used for debugging 
        ready_callback - callback when the track is ready to play, use to stop eggtimer etc.
        enable_menu - True if the track is to have a child show
        starting/playing/ending callback - called repeatedly in each state for show to display status, time etc.

        """
                         
        #instantiate arguments
        self.showlist=showlist
        self.ready_callback=ready_callback   #callback when ready to play
        self.enable_menu=enable_menu           # enable_menu is not used by AudioPlayer
        self.end_callback=end_callback         # callback when finished
        self.starting_callback=starting_callback  #callback during starting state
        self.playing_callback=playing_callback    #callback during playing state
        self.ending_callback=ending_callback      # callback during ending state


        # callback to the calling object to e.g remove egg timer.
        if self.ready_callback<>None:
            self.ready_callback()

        if self.track_params['clear-screen']=='yes':
            self.canvas.delete(ALL)

        # create animation events
        error_text=self.ppio.animate(self.animate_begin_text,id(self))
        if error_text<>'':
            self.mon.err(self,error_text)
            self.error=True
            self._end('error',error_text)


     # Parse list of show instructions and obey them
        self.show_manager=ShowManager()
        self.parse_show_control()
 
        # and end without playing any media
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Normal exit")
        self._end('normal','normally exiting ShowPlayer')



    def key_pressed(self,key_name):
        """
        no keypresses used by this player
        """
        pass


    def button_pressed(self,button,edge):
        """
        no button  presses used by this player
        """


    def terminate(self,reason):
        """
        terminate the  player in special circumstances
        normal user termination if by key_pressed 'escape'
        reason will be killed or error
        """
        # no sub-process to terminate so just call _end
        self.terminate_me=True
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+": terminate received")
        self._end('killed','showplayer killed')
            
                

        
# ***************************************
# INTERNAL FUNCTIONS
# ***************************************

    # tidy up and end ShowPlayer.
    def _end(self,reason,message):
     
            if reason=='error':
                self.end_callback("error",message)
                self=None
                
            elif reason=='killed':
                self.end_callback("killed",message)
                self=None
            else:
                self.end_callback('normal',"Showplayer finished")
                self=None

                


# ***************************************
# SHOW PLAYING
# ***************************************

        
# Extract shows from start show
    def parse_show_control(self):
        show_control_text=self.track_params['show-control']
        lines = show_control_text.split('\n')
        for line in lines:
            if line.strip()=="":
                continue
            fields= line.split()
            error_text=self.show_control(fields)
            if error_text<>"":
                self.mon.err(self,error_text)
                self.end_callback("error",error_text)
                self=None

    def show_control(self,fields):
            error_text=""
            show_ref=fields[0]
            show_command=fields[1]
            if show_command=='start':
                return self.start_show(show_ref)
            elif show_command =='stop':
                return self.stop_show(show_ref)
            else:
                return 'command not recognised '+ show_command

    def stop_show(self,show_ref):
        index=self.show_manager.show_registered(show_ref)
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Stopping show "+ show_ref + ' ' + str(index))
        show_obj=self.show_manager.show_running(index)
        if show_obj<>None:
            show_obj.managed_stop()
            # self.show_manager.set_stopped(index)
        return ''
            

    def start_show(self,show_ref):
            show_index = self.showlist.index_of_show(show_ref)
            if show_index >=0:
                show=self.showlist.show(show_index)
            else:
                return "Show not found in showlist: "+ field

            index=self.show_manager.register_show(show_ref)
            self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Starting show "+ show_ref + ' ' + str(index))
            if self.show_manager.show_running(index):
                self.mon.log(self,"show already running "+show_ref)
                return ""
            
            if show['type']=="mediashow":
                show_obj = MediaShow(show,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.show_manager.set_running(index,show_obj)
                show_obj.play(index,self._end_play_show,top=True,command='nil')
                return ''
 
             
            elif show['type']=="menu":
                show_obj = MenuShow(show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.show_manager.set_running(index,show_obj)
                show_obj.play(index,self._end_play_show,top=True,command='nil')
                return ''

            elif show['type']=="liveshow":
                show_obj= LiveShow(show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.show_manager.set_running(index,show_obj)
                show_obj.play(index,self._end_play_show,top=True,command='nil')
                return ''
                
            else:
                return "unknown mediashow type in start show - "+ show['type']


    def _end_play_show(self,index,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Returned from show with message: "+ message)
        # print 'returned to showplayer'
        self.show_manager.set_stopped(index)
        if reason in("killed","error"):
            self._end(reason,'showplayer terminated, kill or error')



        

from pp_menushow import MenuShow
from pp_liveshow import LiveShow
from pp_mediashow import MediaShow
