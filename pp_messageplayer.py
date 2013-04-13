
from Tkinter import *
import Tkinter
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance
import os
import time
from pp_utils import Monitor


class MessagePlayer:
    """ Displays lines of text in the centre of a black screen"""
    

# *******************
# external commands
# *******************

    def __init__(self,show_id,canvas,pp_home,show_params,track_params):
        """
                canvas - the canvas onto which the image is to be drawn
                cd - configuration dictionary for the show from which player was called
        """

        self.mon=Monitor()
        self.mon.on()

        self.canvas=canvas
        self.pp_home=pp_home
        self.show_params=show_params
        self.track_params=track_params
        
       # get config from medialist if there.
       
        if 'duration' in self.track_params and self.track_params['duration']<>"":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])

        # keep dwell and porch as an integer multiple of tick          
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = (1000*self.duration)

        self.centre_x = int(self.canvas['width'])/2
        self.centre_y = int(self.canvas['height'])/2


    def play(self,
                    text,
                    end_callback,
                    ready_callback,
                    enable_menu=False,
                    starting_callback=None,
                    playing_callback=None,
                    ending_callback=None):
                        
        # instantiate arguments
        self.text=text
        self.enable_menu=enable_menu
        self.ready_callback=ready_callback
        self.end_callback=end_callback
        #init state and signals
        self.quit_signal=False
        self.kill_required_signal=False
        self.error=False
        self._tick_timer=None
        self.drawn=None

        
        self.background_img_file=''
        # get background image from profile.
        self.background_file  = self.track_params['background-image']
        if self.background_file<>'':
            self.background_img_file = self.complete_path(self.background_file)
            if not os.path.exists(self.background_img_file):
                self.mon.err(self,"Message background file not found: "+ self.background_img_file)
                self._end('error',"Message background file not found")

        # and start text display
        self._start_dwell()


    def key_pressed(self,key_name):
        self.mon.log(self,"key received: "+key_name)
        if key_name=='':
            return
        elif key_name in ('p'):
            return
        elif key_name=='escape':
            self._stop()
            return

    def button_pressed(self,button,edge):
        self.mon.log(self,"button received: "+button)
        if button =='pause':
            return
        elif button=='stop':
            self._stop()
            return


    def terminate(self,reason):
        if reason=='error':
            self.error=True
        else:
            self.kill_required_signal=True
        self.quit_signal=True

    
# *******************
# internal functions
# *******************

    def _stop(self):
        self.quit_signal=True
        
    def _error(self):
        self.error=True
        self.quit_signal=True
  
     #called when dwell has completed or quit signal is received
    def _end(self,reason,message):
        if self._tick_timer<>None:
            self.canvas.after_cancel(self._tick_timer)
            self._tick_timer=None
        self.quit_signal=False
        if self.error==True or reason=='error':
            self.end_callback("error",message)
            self=None  
        elif self.kill_required_signal==True:
            self.end_callback("killed",message)
            self=None
        else:
            self.end_callback('normal',message)
            self=None

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Background image is "+ track_file)
        return track_file     
            

    def _start_dwell(self):
        self.dwell_counter=0
        if self.ready_callback<>None:
            self.ready_callback()
        if  self.track_params['background-colour']<>'':   
            self.canvas.config(bg=self.track_params['background-colour'])
        
        #if self.background_img_file<>'' or self.text.rstrip('\n').strip() <> '':
        self.canvas.delete(ALL)
            
        if self.background_img_file<>'':
            pil_background_img=PIL.Image.open(self.background_img_file)
            self.background = PIL.ImageTk.PhotoImage(pil_background_img)
            self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                          int(self.canvas['height'])/2,
                                          image=self.background,
                                          anchor=CENTER)
 
        # display text
        self.canvas.create_text(int(self.canvas['width'])/2, int(self.canvas['height'])/2,
                                                text=self.text.rstrip('\n'),
                                                fill=self.track_params['message-colour'],
                                                font=self.track_params['message-font'])     
        
        # display instructions (hint)
        if self.enable_menu==True:
            self.canvas.create_text(int(self.canvas['width'])/2,
                                    int(self.canvas['height']) - int(self.show_params['hint-y']),
                                    text=self.show_params['hint-text'],
                                    fill=self.show_params['hint-colour'],
                                    font=self.show_params['hint-font'])
        
        self.canvas.update_idletasks( )
        self._tick_timer=self.canvas.after(self.tick, self._do_dwell)

        
    def _do_dwell(self):
        if self.quit_signal == True:
            self.mon.log(self,"quit received")
            self._end('normal','user quit')
        else:
            if self.dwell<>0:
                self.dwell_counter=self.dwell_counter+1
                if self.dwell_counter==self.dwell/self.tick:
                    self._end('normal','finished')
                else:
                    self._tick_timer=self.canvas.after(self.tick, self._do_dwell)
            else:
                    self._tick_timer=self.canvas.after(self.tick, self._do_dwell)
