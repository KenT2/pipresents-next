import os
import time

from Tkinter import *
import Tkinter
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_showmanager import ShowManager
from pp_pluginmanager import PluginManager
from pp_gpio import PPIO
from pp_utils import Monitor


class MessagePlayer:
    """ Displays lines of text in the centre of a coloured screen with background image
        See pp_imageplayer for common software design description
    """
    

# *******************
# external commands
# *******************

    def __init__(self,show_id,root,canvas,show_params,track_params,pp_dir,pp_home,pp_profile):

        self.mon=Monitor()
        self.mon.on()

        self.root=root
        self.canvas=canvas
        self.show_id=show_id
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

       # get config from medialist if there.
       
        if 'duration' in self.track_params and self.track_params['duration']<>"":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])

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
        
        # keep tick as an integer sub-multiple of 1 second         
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 1000*self.duration

        #get animation instructions from profile
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']

        # open the plugin Manager
        self.pim=PluginManager(self.show_id,self.root,self.canvas,self.show_params,self.track_params,self.pp_dir,self.pp_home,self.pp_profile) 

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO() 


    def play(self,
                    text,
                    showlist,
                    end_callback,
                    ready_callback,
                    enable_menu=False):
                        
        # instantiate arguments
        self.text=text
        self.showlist=showlist
        self.end_callback=end_callback
        self.ready_callback=ready_callback
        self.enable_menu=enable_menu
        
        #init state and signals
        self.quit_signal=False
        self.tick_timer=None
        self.drawn=None


        # create an  instance of showmanager so we can control concurrent shows
        self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.root,self.canvas,self.pp_dir,self.pp_profile,self.pp_home)

     # Control other shows at beginning
        reason,message=self.show_manager.show_control(self.track_params['show-control-begin'])
        if reason == 'error':
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
                    # start text display
                    self.start_dwell()

    def terminate(self,reason):
        # no lower level things to terminate so just go to end
        self.end(reason,'kill or error')

    def get_links(self):
        return self.track_params['links']

    def input_pressed(self,symbol):
        self.mon.log(self,"input received: "+symbol)
        if symbol=='stop':
            self.stop()



# *******************
# internal functions
# *******************

    def stop(self):
        self.quit_signal=True

        

            
# *******************
# sequencing
# *******************

    def start_dwell(self):
        self.dwell_counter=0
        if self.ready_callback<>None:
            self.ready_callback()
   
        self.tick_timer=self.canvas.after(self.tick, self.do_dwell)

        
    def do_dwell(self):
        if self.quit_signal == True:
            self.mon.log(self,"quit received")
            self.end('normal','user quit')
        else:
            if self.dwell<>0:
                self.dwell_counter=self.dwell_counter+1
                if self.dwell_counter==self.dwell/self.tick:
                    self.end('normal','finished')
                else:
                    self.tick_timer=self.canvas.after(self.tick, self.do_dwell)
            else:
                    self.tick_timer=self.canvas.after(self.tick, self.do_dwell)


# *****************
# ending the player
# *****************

    def end(self,reason,message):
        # stop the plugin
        if self.track_params['plugin']<>'':
            self.pim.stop_plugin()

        # abort the timer
        if self.tick_timer<>None:
            self.canvas.after_cancel(self.tick_timer)
            self.tick_timer=None
        
        if reason in ('error','killed'):
            self.end_callback(reason,message)
            self=None

        else:
            # normal end so do show control 
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

        if  self.background_colour<>'':   
            self.canvas.config(bg=self.background_colour)
        
        self.canvas.delete('pp-content')
      
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Message background file not found: "+ self.background_img_file)
                self.end('error',"Message background file not found")
            else:
                pil_background_img=PIL.Image.open(self.background_img_file)
                self.background = PIL.ImageTk.PhotoImage(pil_background_img)
                self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                              image=self.background,
                                              anchor=CENTER,
                                              tag='pp-content')

         # display show text if enabled
        if self.show_params['show-text']<> ''and self.track_params['display-show-text']=='yes':
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

        # execute the plugin if required
        if self.track_params['plugin']<>'':
            reason,message,self.text = self.pim.do_plugin(self.text,self.track_params['plugin'])
            if reason <> 'normal':
                return reason,message

 
        # display message text
        if self.track_params['message-x']<>'':
             self.canvas.create_text(int(self.track_params['message-x']), int(self.track_params['message-y']),
                                                    text=self.text.rstrip('\n'),
                                                    fill=self.track_params['message-colour'],
                                                    font=self.track_params['message-font'],
                                                    justify=self.track_params['message-justify'],
                                                    anchor = 'nw',
                                                    tag='pp-content')
        else:
            self.canvas.create_text(int(self.canvas['width'])/2, int(self.canvas['height'])/2,
                                                    text=self.text.rstrip('\n'),
                                                    fill=self.track_params['message-colour'],
                                                    font=self.track_params['message-font'],
                                                    justify=self.track_params['message-justify'],
                                                    tag='pp-content')     


        # display instructions (hint)
        if self.enable_menu==True:
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

# *****************
# utilities
# *****************


    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file     
