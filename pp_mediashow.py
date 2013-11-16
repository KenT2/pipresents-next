import os
from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance
import time

from pp_imageplayer import ImagePlayer
from pp_videoplayer import VideoPlayer
from pp_audioplayer import AudioPlayer
from pp_browserplayer import BrowserPlayer
from pp_medialist import MediaList
from pp_utils import Monitor
from pp_messageplayer import MessagePlayer
from pp_resourcereader import ResourceReader
from pp_controlsmanager import ControlsManager
from pp_timeofday import TimeOfDay

class MediaShow:


# *******************
# External interface
# ********************

    def __init__(self,
                            show_params,
                             root,
                            canvas,
                            showlist,
                            pp_dir,
                            pp_home,
                            pp_profile):
        """ canvas - the canvas that the menu is to be written on
            show - the dictionary fo the show to be played
            pp_home - Pi presents data_home directory
            pp_profile - Pi presents profile directory
        """

        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_params =show_params
        self.showlist=showlist
        self.root=root
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # open resources
        self.rr=ResourceReader()

        # Init variables
        self.player=None
        self.shower=None
        self.poll_for_interval_timer=None
        self.poll_for_continue_timer=None
        self.waiting_for_interval=False
        self.interval_timer=None
        self.duration_timer=None
        self.error=False
        
        self.interval_timer_signal=False
        self.end_trigger_signal=False
        self.end_mediashow_signal=False
        self.next_track_signal=False
        self.previous_track_signal=False
        self.play_child_signal = False
        self.req_next='nil'

        #create and instance of TimeOfDay scheduler so we can add events
        self.tod=TimeOfDay()

        self.state='closed'


    def play(self,show_id,end_callback,show_ready_callback, top=False,command='nil'):

        """ displays the mediashow
              end_callback - function to be called when the menu exits
              ready_callback - callback when menu is ready to display (not used)
              top is True when the show is top level (run from [start])
        """

        #instantiate the arguments
        self.show_id=show_id
        self.end_callback=end_callback
        self.show_ready_callback=show_ready_callback
        self.top=top
        self.command=command
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Starting show")

        # check  data files are available.
        self.media_file = self.pp_profile + "/" + self.show_params['medialist']
        if not os.path.exists(self.media_file):
            self.mon.err(self,"Medialist file not found: "+ self.media_file)
            self.end('error',"Medialist file not found")


        #create a medialist for the mediashow and read it.
        self.medialist=MediaList()
        if self.medialist.open_list(self.media_file,self.showlist.sissue())==False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")

        #get controls for this show if top level
        controlsmanager=ControlsManager()
        if self.top==True:
            self.controls_list=controlsmanager.default_controls()
            # and merge in controls from profile
            self.controls_list=controlsmanager.merge_show_controls(self.controls_list,self.show_params['controls'])


        #set up the time of day triggers for the show
        if self.show_params['trigger']in('time','time-quiet'):
            error_text=self.tod.add_times(self.show_params['trigger-input'],id(self),self.tod_start_callback,self.show_params['trigger'])
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)

        if self.show_params['trigger-end']=='time':
            # print self.show_params['trigger-end-time']
            error_text=self.tod.add_times(self.show_params['trigger-end-time'],id(self),self.tod_end_callback,'n/a')
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)
                
        if self.show_params['trigger-end']=='duration':
            error_text=self.calculate_duration(self.show_params['trigger-end-time'])
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)
                
        self.state='closed'
        self.egg_timer=None
        self.wait_for_trigger()


# ********************************
# Respond to external events
# ********************************

    #stop received from another concurrent show
    def managed_stop(self):
           # if next lower show is running pass down to stop the show and lower level
            if self.shower<>None:
                self.shower.managed_stop()
            else:
                #stop the show if not at top
                self.end_mediashow_signal=True
                # and if track is runing stop that first
                if self.player<>None:
                    self.player.input_pressed('stop')

    # kill or error
    def terminate(self,reason):
        if self.shower<>None:
            self.shower.terminate(reason)
        elif self.player<>None:
            self.player.terminate(reason)
        else:
            self.end(reason,' terminated with no shower or player to terminate')


   
   # respond to input events
    def input_pressed(self,symbol,edge,source):
        self.mon.log(self, self.show_params['show-ref']+ ' '+ str(self.show_id)+": received input: " + symbol)

        
        #  check symbol against mediashow triggers, triggers can be used at top or lower level
        # and not affected by disable-controls

        if self.state=='waiting' and self.show_params['trigger'] in ('input','input-quiet')and symbol == self.show_params['trigger-input']:
            self.start_show()
        elif self.state=='playing' and self.show_params['trigger-next']=='input' and symbol == self.show_params['next-input']:
            self.next()

       # internal functions are triggered only when disable-controls is  'no'
        if self.show_params['disable-controls']=='yes':
            return

        # if at top convert symbolic name to operation otherwise lower down we have received an operation
        # look through list of standard symbols to find match (symbolic-name, function name) operation =lookup (symbol
        if self.top==True:
            operation=self.lookup_control(symbol,self.controls_list)
        else:
            operation=symbol
            
   
        # print 'operation',operation
        self.do_operation(operation,edge,source)


    #service the standard inputs for this show
    def do_operation(self,operation,edge,source):
        if self.shower<>None:
            # if next lower show is running pass down to stop the show and lower level
            self.shower.input_pressed(operation,edge,source) 
        else:        
            # control this show and its tracks
            # print 'operation',operation
            if operation=='stop':
                if self.top == False:
                    # not at top so stop the current show 
                    self.end_mediashow_signal=True
                    # and if a track is running stop that first
                    if self.player<>None:
                        self.player.input_pressed('stop')
                else:
                    # top = True, just stop track if running
                    if self.player<>None:
                        self.player.input_pressed('stop')

            elif operation in ('up','down'):
                #if playing rather than waiting use keys for next or previous
                if operation=='up' and self.state=='playing':
                    self.previous()
                else:
                    self.next()

            elif operation=='play':
                # use 'play' to start child if state=playing or to trigger the show if waiting for trigger
                if self.state=='playing':
                    if self.show_params['has-child']=='yes':
                        self.play_child_signal=True
                        self.child_track_ref='pp-child-show'
                        # and stop the current track if its running
                        if self.player<>None:
                            self.player.input_pressed('stop')
                else:
                    if self.state=='waiting':
                        self.start_show()

            elif operation == 'pause':
                if self.player<>None:
                    self.player.input_pressed(operation)
                    
            #if the operation is omxplayer or mplayer runtime control then pass it to player if running
            elif operation[0:4]=='omx-' or operation[0:6]=='mplay-'or operation[0:5]=='uzbl-':
                if self.player<>None:
                    self.player.input_pressed(operation)



    def lookup_control(self,symbol,controls_list):
        for control in controls_list:
            if symbol == control[0]:
                return control[1]
        return ''


# ***************************
# Show sequencer
# ***************************

    def end_interval_timer(self):
        self.interval_timer_signal=True

    # callback from time of day scheduler
    def tod_start_callback(self):
         if self.state=='waiting' and self.show_params['trigger']in('time','time-quiet'):
            self.start_show()

    def tod_end_callback(self):
        if self.state=='playing' and self.show_params['trigger-end'] in ('time','duration'):
            self.end_trigger_signal=True
            if self.shower<>None:
                self.shower.input_pressed('stop')
            elif self.player<>None:
                self.player.input_pressed('stop')
                

    def stop(self,message):
        self.end_mediashow_signal=True
        if self.interval_timer<>None:
            self.canvas.after_cancel(self.interval_timer)

   
    def next(self):
        # stop track if running and set signal
        self.next_track_signal=True
        if self.shower<>None:
            self.shower.input_pressed("stop")
        else:
            if self.player<>None:
                self.player.input_pressed("stop")

    def previous(self):
        self.previous_track_signal=True
        if self.shower<>None:
            self.shower.input_pressed("stop")
        else:
            if self.player<>None:
                self.player.input_pressed("stop")
    
        
    # wait for trigger sets the state to waiting so that events can do a start show.    
    def wait_for_trigger(self):
        self.state='waiting'
        if self.show_ready_callback<>None:
            self.show_ready_callback()

        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Waiting for trigger: "+ self.show_params['trigger'])
        
        if self.show_params['trigger']=="input":
            # blank screen waiting for trigger if auto, otherwise display something
            if self.show_params['progress']=="manual":
                text= self.resource('mediashow','m01')
            else:
                text= self.resource('mediashow','m02')
            self.display_message(self.canvas,'text',text,0,self.start_show)


        elif self.show_params['trigger']=="input-quiet":
            # blank screen waiting for trigger
            text = self.resource('mediashow','m10')
            self.display_message(self.canvas,'text',text,0,self.start_show)
            pass

        elif self.show_params['trigger'] in ('time','time-quiet'):
            # show next show notice
            quiet=3
            # if next show is this one display text
            next_show=self.tod.next_event_time()
            if next_show[quiet]==False:
                if next_show[1]=='tomorrow':
                    text = self.resource('mediashow','m09')
                else:
                    text = self.resource('mediashow','m08')                     
                text=text.replace('%tt',next_show[0])
                self.display_message(self.canvas,'text',text,0,self.start_show)  
            
        elif self.show_params['trigger']=="start":
            self.start_show()
            
        else:
            self.mon.err(self,"Unknown trigger: "+ self.show_params['trigger'])
            self.end('error',"Unknown trigger type")



  
    def start_show(self):
        self.state='playing'
        self.direction='forward'
        # self.canvas.delete(ALL)
        # start interval timer
        if self.show_params['repeat']=="interval" and self.show_params['repeat-interval']<>0:
            self.interval_timer_signal=False
            self.interval_timer=self.canvas.after(int(self.show_params['repeat-interval'])*1000,self.end_interval_timer)
            
        # start duration timer
        if self.show_params['trigger-end']=='duration':
            # print 'set alarm ', self.duration
            self.duration_timer = self.canvas.after(self.duration*1000,self.tod_end_callback)
        
        # and play the first track unless commanded otherwise
        if self.command=='backward':
            self.medialist.finish()
        else:
            self.medialist.start()
        self.play_selected_track(self.medialist.selected_track())
 
 
    def what_next(self):
        self.direction='forward'

        # end of show trigger caused by tod
        if self.end_trigger_signal==True:
            self.end_trigger_signal=False
            if self.top==True:
                self.state='waiting'
                self.wait_for_trigger()
            else:
                # not at top so stop the show
                self.end('normal','sub-show end time trigger')
        
        # user wants to end, wait for any shows or tracks to have ended then end show
        # probalby will get here with end_m set when player and shower has finished
        elif self.end_mediashow_signal==True:
            if self.player==None and self.shower==None:
                self.end_mediashow_signal=False
                self.end('normal',"show ended by user")

            
        #returning from a subshow needing to move onward 
        elif self.req_next=='do-next':
            self.req_next='nil'
            self.medialist.next(self.show_params['sequence'])
            self.play_selected_track(self.medialist.selected_track())
            
        #returning from a subshow needing to move backward 
        elif self.req_next=='do-previous':
            self.req_next='nil'
            self.direction='backward'
            self.medialist.previous(self.show_params['sequence'])
            self.play_selected_track(self.medialist.selected_track())         
               
        # user wants to play child
        elif self.play_child_signal == True:
            self.play_child_signal=False
            index = self.medialist.index_of_track(self.child_track_ref)
            if index >=0:
                #don't use select the track as need to preserve mediashow sequence.
                child_track=self.medialist.track(index)
                self.display_eggtimer(self.resource('mediashow','m07'))
                self.play_selected_track(child_track)
            else:
                self.mon.err(self,"Child show not found in medialist: "+ self.show_params['pp-child-show'])
                self.end('error',"child show not found in medialist")
        
        # skip to next track on user input
        elif self.next_track_signal==True:
            self.next_track_signal=False
            if self.medialist.at_end()==True:
                if  self.show_params['sequence']=="ordered" and self.show_params['repeat']=='oneshot' and self.top==False:
                    self.end('do-next',"Return from Sub Show")
                elif  self.show_params['sequence']=="ordered" and self.show_params['repeat']=='single-run' and self.top==False:
                    self.end('do-next',"Return from Sub Show")
                else:
                    self.medialist.next(self.show_params['sequence'])
                    self.play_selected_track(self.medialist.selected_track())               
            else:
                self.medialist.next(self.show_params['sequence'])
                self.play_selected_track(self.medialist.selected_track())
                
        # skip to previous track on user input
        elif self.previous_track_signal==True:
            self.previous_track_signal=False
            self.direction='backward'
            if self.medialist.at_start()==True:
                if  self.show_params['sequence']=="ordered" and self.show_params['repeat']=='oneshot' and self.top==False:
                    self.end('do-previous',"Return from Sub Show")
                elif  self.show_params['sequence']=="ordered" and self.show_params['repeat']=='single-run' and self.top==False:
                    self.end('do-previous',"Return from Sub Show")
                else:
                    self.medialist.previous(self.show_params['sequence'])
                    self.play_selected_track(self.medialist.selected_track())               
            else:
                self.medialist.previous(self.show_params['sequence'])              
                self.play_selected_track(self.medialist.selected_track())
        

        # track is finished and we are on auto        
        elif self.show_params['progress']=="auto":
            
            if self.medialist.at_end()==True:

                # oneshot
                if self.show_params['sequence']=="ordered" and self.show_params['repeat']=='oneshot' and self.top==False:
                    self.end('normal',"End of Oneshot in subshow")
                    
                elif self.show_params['sequence']=="ordered" and self.show_params['repeat']=='oneshot' and self.top==True:
                    self.wait_for_trigger()

                # single run
                elif self.show_params['sequence']=="ordered" and self.show_params['repeat']=='single-run' and self.top==True:
                   self.end('normal',"End of Single Run")

                elif self.show_params['sequence']=="ordered" and self.show_params['repeat']=='single-run' and self.top==False:
                   self.end('do-next',"End of single run - Return from Sub Show")

                # repeating and waiting to restart 
                elif self.waiting_for_interval==True:
                    if self.interval_timer_signal==True:
                        self.interval_timer_signal=False
                        self.waiting_for_interval=False
                        self.start_show()
                    else:
                        self.poll_for_interval_timer=self.canvas.after(1000,self.what_next)
 
                elif self.show_params['sequence']=="ordered" and self.show_params['repeat']=='interval' and int(self.show_params['repeat-interval'])>0:
                    self.waiting_for_interval=True
                    self.poll_for_interval_timer=self.canvas.after(1000,self.what_next) 
                    
                #elif self.show_params['sequence']=="ordered" and self.show_params['repeat']=='interval' and int(self.show_params['repeat-interval'])==0:
                elif self.show_params['repeat']=='interval' and int(self.show_params['repeat-interval'])==0:
                    self.medialist.next(self.show_params['sequence'])
                    self.play_selected_track(self.medialist.selected_track())

                # shuffling so there is no end condition
                elif self.show_params['sequence']=="shuffle":
                    self.medialist.next(self.show_params['sequence'])
                    self.play_selected_track(self.medialist.selected_track())
                    
                else:
                    self.mon.err(self,"Unhandled playing event: "+self.show_params['sequence'] +' with ' + self.show_params['repeat']+" of "+ self.show_params['repeat-interval'])
                    self.end('error',"Unhandled playing event")
                    
            else:
                self.medialist.next(self.show_params['sequence'])
                self.play_selected_track(self.medialist.selected_track())
                    
        # track has finished and we are on manual progress               
        elif self.show_params['progress']=="manual":
                    self.delete_eggtimer()
                    self.canvas.delete('pp-content')
                    if self.show_params['trigger-next']=='input':
                        self.display_eggtimer(self.resource('mediashow','m03'))
                    self.poll_for_continue_timer=self.canvas.after(2000,self.what_next)
                    
        else:
            #unhandled state
            self.mon.err(self,"Unhandled playing event: ")
            self.end('error',"Unhandled playing event")           


# ***************************
# Dispatching to Players/Shows 
# ***************************
   
    def ready_callback(self):
        self.delete_eggtimer()

    def play_selected_track(self,selected_track):
        """ selects the appropriate player from type field of the medialist and computes
              the parameters for that type
              selected track is a dictionary for the track/show
        """
        self.delete_eggtimer()
        if self.show_params['progress']=="manual":
            self.display_eggtimer(self.resource('mediashow','m04'))

        # is menu required
        if self.show_params['has-child']=="yes":
            self.enable_child=True
        else:
            self.enable_child=False

        #dispatch track by type
        self.player=None
        self.shower=None
        track_type = selected_track['type']
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Track type is: "+ track_type)
        if track_type=="video":
            # create a videoplayer
            track_file=self.complete_path(selected_track)
            self.player=VideoPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=self.enable_child)
  
        elif track_type=="audio":
            # create a audioplayer
            track_file=self.complete_path(selected_track)
            self.player=AudioPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=self.enable_child)
 
        elif track_type=="web":
            # create a browser
            track_file=self.complete_path(selected_track)
            self.player=BrowserPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=self.enable_child)
  


 
        elif track_type=="image":
            track_file=self.complete_path(selected_track)
            # images played from menus don't have children
            self.player=ImagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                    self.showlist,
                                    self.end_player,
                                    self.ready_callback,
                                    enable_menu=self.enable_child)
                                    
        elif track_type=="message":
            # bit odd because MessagePlayer is used internally to display text. 
            text=selected_track['text']
            self.player=MessagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(text,
                                    self.showlist,
                                    self.end_player,
                                    self.ready_callback,
                                    enable_menu=self.enable_child
                                    )

 
        elif track_type=="show":
            # get the show from the showlist
            index = self.showlist.index_of_show(selected_track['sub-show'])
            if index >=0:
                self.showlist.select(index)
                selected_show=self.showlist.selected_show()
            else:
                self.mon.err(self,"Show not found in showlist: "+ selected_track['sub-show'])
                self.end('error',"Unknown show")
                
            if selected_show['type']=="mediashow":    
                self.shower= MediaShow(selected_show,
                                                               self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                               self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command=self.direction)

            elif selected_show['type']=="liveshow":    
                self.shower= LiveShow(selected_show,
                                                                self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="radiobuttonshow":
                self.shower= RadioButtonShow(selected_show,
                                                         self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="hyperlinkshow":
                self.shower= HyperlinkShow(selected_show,
                                                       self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                       self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')
            
            elif selected_show['type']=="menu":
                self.shower= MenuShow(selected_show,
                                                        self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                          self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')
                
            else:
                self.mon.err(self,"Unknown Show Type: "+ selected_show['type'])
                self.end('error'"Unknown show type")  
            
        else:
            self.mon.err(self,"Unknown Track Type: "+ track_type)
            self.end('error',"Unknown track type")            


    def end_player(self,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Returned from player with message: "+ message)
        self.player=None
        self.req_next='nil'
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            # elif>else move to what-next?
            if self.show_params['progress']=="manual":
                self.display_eggtimer(self.resource('mediashow','m05'))
                self.req_next=reason
                self.what_next()
            else:
                self.req_next=reason
                self.what_next()
                

    def end_shower(self,show_id,reason,message):
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Returned from shower with message: "+ message)
        self.shower=None
        self.req_next='nil'
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            if self.show_params['progress']=="manual":
                self.display_eggtimer(self.resource('mediashow','m06'))
                self.req_next=reason
                self.what_next() 
            else:
                self.req_next=reason
                self.what_next() 



# ***************************
# end of show 
# ***************************

    def end(self,reason,message):
        self.end_mediashow_signal=False
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Ending Mediashow")
        self.tidy_up()
        self.end_callback(self.show_id,reason,message)
        self=None
        return

    def tidy_up(self):
        #clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))
        if self.poll_for_continue_timer<>None:
                self.canvas.after_cancel(self.poll_for_continue_timer)
                self.poll_for_continue_timer=None
        if self.poll_for_interval_timer<>None:
                self.canvas.after_cancel(self.poll_for_interval_timer)
                self.poll_for_interval_timer=None
        if self.interval_timer<>None:
            self.canvas.after_cancel(self.interval_timer)
            self.interval_timer=None
        if self.duration_timer<>None:
            self.canvas.after_cancel(self.duration_timer)
            self.duration_timer=None


# ***************************
# displaying things
# ***************************
    
    def display_eggtimer(self,text):
        self.canvas.create_text(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                                  text= text,
                                                  fill='white',
                                                  font="Helvetica 20 bold",
                                                tag='pp-eggtimer')
        self.canvas.update_idletasks( )


    def delete_eggtimer(self):
        self.canvas.delete('pp-eggtimer')
        self.canvas.update_idletasks( )


    # used to display internal messages in situations where a medialist entry could not be used.
    def display_message(self,canvas,source,content,duration,_display_message_callback):
            self.display_message_callback=_display_message_callback
            tp={'duration':duration,'message-colour':'white','message-font':'Helvetica 20 bold','background-colour':'',
                'message-justify':'left','background-image':'','show-control-begin':'','show-control-end':'',
                'animate-begin':'','animate-clear':'','animate-end':'','message-x':'','message-y':'',
                'display-show-background':'no','display-show-text':'no','show-text':'','track-text':'',
                'plugin':''}
            self.player=MessagePlayer(self.show_id,self.root,canvas,tp,tp,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(content,self.showlist,self.display_message_end,None,False)

    def   display_message_end(self,reason,message):
        self.player=None
        if reason in ('error','killed'):
            self.end(reason,message)
        else:
            self.display_message_callback()



# ***************************
# utilities
# ***************************

    def calculate_duration(self,line):
        fields=line.split(':')
        if len(fields)==1:
            secs=fields[0]
            minutes='0'
            hours='0'
        if len(fields)==2:
            secs=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields)==3:
            secs=fields[2]
            minutes=fields[1]
            hours=fields[0]
        self.duration=3600*long(hours)+60*long(minutes)+long(secs)
        return ''

    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self.terminate("error")
        else:
            return value
        
    def complete_path(self,selected_track):
        #  complete path of the filename of the selected entry
        track_file = selected_track['location']
        if track_file<>'' and track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,self.show_params['show-ref']+ ' '+ str(self.show_id)+ ": Track to play is: "+ track_file)
        return track_file     
        
from pp_menushow import MenuShow
from pp_liveshow import LiveShow
from pp_radiobuttonshow import RadioButtonShow
from pp_hyperlinkshow import HyperlinkShow
