import os
import time

from Tkinter import *
import Tkinter

import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_resourcereader import ResourceReader
from pp_showmanager import ShowManager
from pp_gpio import PPIO
from pp_utils import Monitor


class ImagePlayer:
    """ Displays an image on a canvas for a period of time. Image display can be paused and interrupted
        __init_ just makes sure that all the things the player needs are available
        play starts playing the track and returns immeadiately
        play must end up with a call to tkinter's after, the after callback will interrogae the playing state at intervals and
        eventually return through end_callback
        input-pressed receives user input while the track is playing. it might pass the input on to the driver
        Input-pressed must not wait, it must set a signal and return immeadiately.
        The signal is interrogated by the after callback.
    """

    # slide state constants
    NO_SLIDE = 0
    SLIDE_DWELL= 1

# *******************
# external commands
# *******************

    def __init__(self,show_id,canvas,show_params,track_params,pp_home,pp_profile):
        """
                show_id - show instance that player is run from (for monitoring only)
                canvas - the canvas onto which the image is to be drawn
                show_params -  dictionary of show parameters
                track_params - disctionary of track paramters
                pp_home - data home directory
                pp_profile - profile name
        """

        self.mon=Monitor()
        self.mon.off()

        self.show_id=show_id
        self.canvas=canvas
        self.show_params=show_params
        self.track_params=track_params
        self.pp_home=pp_home
        self.pp_profile=pp_profile


        # open resources
        self.rr=ResourceReader()

        # get parameters 
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']
        
        if self.track_params['duration']<>"":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])
        
        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()

        # get background image from profile.
        if self.track_params['background-image']<>"":
            self.background_file= self.track_params['background-image']
        else:
            self.background_file= self.show_params['background-image']
            
        # get background colour from profile.
        if self.track_params['background-colour']<>"":
            self.background_colour= self.track_params['background-colour']
        else:
            self.background_colour= self.show_params['background-colour']


        # get  image window from profile
        if self.track_params['image-window'].strip()<>"":
            self.image_window= self.track_params['image-window'].strip()
        else:
            self.image_window= self.show_params['image-window'].strip()

            

    def play(self,
                    track,
                    showlist,
                    end_callback,
                    ready_callback,
                    enable_menu=False):

        """
                track - filename of track to be played
                showlist - from which track was taken
                end_callback - callback when player terminates
                ready_callback - callback just before anytthing is displayed
                enable_menu  - there will be a child track so display the hint text
        """
                        
        # instantiate arguments
        self.track=track
        self.showlist=showlist
        self.enable_menu=enable_menu
        self.ready_callback=ready_callback
        self.end_callback=end_callback

        #get the track to be displayed
        if os.path.exists(self.track)==True:
            self.pil_image=PIL.Image.open(self.track)
        else:
            self.pil_image=None

        #init state and signals  
        self.centre_x = int(self.canvas['width'])/2
        self.centre_y = int(self.canvas['height'])/2
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = 10*self.duration
        self.dwell_counter=0
        self.state=ImagePlayer.NO_SLIDE
        self.quit_signal=False
        self.drawn=None
        self.paused=False
        self.pause_text=None
        self.tick_timer=None
        

        #parse the image_window
        error,self.image_x1,self.image_y1,self.image_x2,self.image_y2,self.filter=self.parse_window(self.image_window)
        if error =='error':
            self.mon.err(self,'image window error: '+self.image_window)
            self.end('error','image window error')
        else:

            # create an  instance of showmanager so we can control concurrent shows
            self.show_manager=ShowManager(self.show_id,self.showlist,self.show_params,self.canvas,self.pp_profile,self.pp_home)

             # Control other shows at beginning
            reason,message=self.show_manager.show_control(self.track_params['show-control-begin'])
            if reason == 'error':
                self.end_callback(reason,message)
                self=None
            else:
                #display content
                self.display_content()

                # create animation events
                reason,message=self.ppio.animate(self.animate_begin_text,id(self))
                if reason=='error':
                    self.mon.err(self,message)
                    self.end_callback(reason,message)
                    self=None
                else:                              
                    # start dwelling
                    self.mon.log(self,'playing track from show Id: '+str(self.show_id))
                    self.start_dwell()

        
    def input_pressed(self,symbol):
        if symbol =='pause':
            self.pause()
        elif symbol=='stop':
            self.stop()
            return

    def terminate(self,reason):
        # no lower level things to terminate so just go to end
        self.end(reason,'kill or error')

    def get_links(self):
        return self.track_params['links']
      
# *******************
# internal functions
# *******************

    def pause(self):
        if not self.paused:
            self.paused = True
        else:
            self.paused=False

    def stop(self):
        self.quit_signal=True
        


        
# ******************************************
# Sequencing
# ********************************************

    def start_dwell(self):

        if self.ready_callback<>None:
            self.ready_callback()
        self.state=ImagePlayer.SLIDE_DWELL
        self.tick_timer=self.canvas.after(self.tick, self.do_dwell)

        
    def do_dwell(self):
        if self.quit_signal == True:
            self.mon.log(self,"quit received")
            self.end('normal','user quit')
        else:
            if self.paused == False:
                self.dwell_counter=self.dwell_counter+1

            # one time flipping of pause text
            if self.paused==True and self.pause_text==None:
                self.pause_text=self.canvas.create_text(100,100, anchor=NW,
                                                      text=self.resource('imageplayer','m01'),
                                                      fill="white",
                                                      font="arial 25 bold")
                self.canvas.update_idletasks( )
                
            if self.paused==False and self.pause_text<>None:
                    self.canvas.delete(self.pause_text)
                    self.pause_text=None
                    self.canvas.update_idletasks( )

            if self.dwell<>0 and self.dwell_counter==self.dwell:
                self.end('normal','user quit or duration exceeded')
            else:
                self.tick_timer=self.canvas.after(self.tick, self.do_dwell)



# *****************
# ending the player
# *****************

    def end(self,reason,message):
            self.state=self.NO_SLIDE
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


# **********************************
# displaying things
# **********************************

    def display_content(self):

        #background colour
        if  self.background_colour<>'':   
           self.canvas.config(bg=self.background_colour)
           
        self.canvas.delete('pp-content')


        # background image
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Background file not found: "+ self.background_img_file)
                self.end('error',"Background file not found")
            else:
                pil_background_img=PIL.Image.open(self.background_img_file)
                self.background = PIL.ImageTk.PhotoImage(pil_background_img)
                self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                             int(self.canvas['height'])/2,
                                             image=self.background,
                                            anchor=CENTER,
                                            tag='pp-content')
                                            
        if self.pil_image<>None:
            if self.image_window.strip()=='centred':
                # load and display the unmodified image in centre
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                  image=self.tk_img, anchor=CENTER,
                                                  tag='pp-content')
            else:
                if self.image_x2==0:
                    # load and display the unmodified image at x1,y1
                    self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                    self.drawn = self.canvas.create_image(self.image_x1, self.image_y1,
                                                      image=self.tk_img, anchor=NW,
                                                      tag='pp-content')
                else:
                    # resize the image as it loads and display in the centre of the window
                    win_centre_x=(self.image_x2+self.image_x1)/2
                    win_centre_y= (self.image_y2+self.image_y1)/2
                    self.pil_image.thumbnail((self.image_x2-self.image_x1,self.image_y2-self.image_y1),eval(self.filter))
                    self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                    self.drawn = self.canvas.create_image(win_centre_x, win_centre_y,
                                                      image=self.tk_img, anchor=CENTER,
                                                      tag='pp-content')                                                 
                                                  
        # display hint if enabled
       
        if self.enable_menu== True:
            self.canvas.create_text(self.centre_x, int(self.canvas['height']) - int(self.show_params['hint-y']),
                                                  text=self.show_params['hint-text'],
                                                  fill=self.show_params['hint-colour'],
                                                font=self.show_params['hint-font'],
                                                tag='pp-content')

        # display show text if enabled
        if self.show_params['show-text']<> '':
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
            
        self.canvas.tag_raise('pp-click-area')            
        self.canvas.update_idletasks( )


# **********************************
# utilties
# **********************************


    def parse_window(self,line):
            fields = line.split()
            if len(fields) not in (1,2,4,5):
                return 'error',0,0,0,0,''
            else:
                if len(fields)==1:
                    if fields[0]=='centred':
                        return 'normal',fields[0],0,0,0,''
                    else:
                        return 'error',0,0,0,0,''
                
                elif len(fields)==2:
                    if fields[0].isdigit() and fields[1].isdigit():
                        return 'normal',int(fields[0]),int(fields[1]),0,0,''
                    else:
                        return 'error',0,0,0,0,''
                    
                elif len(fields)==4:
                    if fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit():
                        return 'normal',int(fields[0]),int(fields[1]),int(fields[2]),int(fields[3]),'PIL.Image.NEAREST'
                    else:
                        return 'error',0,0,0,0,''
                else:
                    if len(fields)==5:
                        if fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit() and fields[4] in ('NEAREST','BILINEAR','BICUBIC','ANTIALIAS'):
                            return 'normal',int(fields[0]),int(fields[1]),int(fields[2]),int(fields[3]),'PIL.Image.'+fields[4]
                        else:
                            return 'error',0,0,0,0,''                            
  

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file     
 
  

# get a text string from resources.cfg
    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self.error()
        else:
            return value
