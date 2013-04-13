import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from Tkinter import *
import Tkinter
import os
import time

from pp_resourcereader import ResourceReader
from pp_utils import Monitor
from pp_gpio import PPIO


class ImagePlayer:
    """ Displays an image on a canvas for a period of time. Image display can be interrupted
          Implements animation of transitions but Pi is too slow without GPU aceleration."""

    # slide state constants
    NO_SLIDE = 0
    SLIDE_IN = 1
    SLIDE_DWELL= 2
    SLIDE_OUT= 3

# *******************
# external commands
# *******************

    def __init__(self,show_id,canvas,pp_home,show_params,track_params):
        """
                canvas - the canvas onto which the image is to be drawn
                cd -  dictionary of show parameters
                track_params - disctionary of track paramters
        """

        self.mon=Monitor()
        self.mon.on()

        self.show_id=show_id
        self.canvas=canvas
        self.pp_home=pp_home
        self.show_params=show_params
        self.track_params=track_params

        # open resources
        self.rr=ResourceReader()

            
        # get config from medialist if there.
        
        self.animate_begin_text=self.track_params['animate-begin']
        self.animate_end_text=self.track_params['animate-end']
        
        if 'duration' in self.track_params and self.track_params['duration']<>"":
            self.duration= int(self.track_params['duration'])
        else:
            self.duration= int(self.show_params['duration'])
            
        if 'transition' in self.track_params and self.track_params['transition']<>"":
            self.transition= self.track_params['transition']
        else:
            self.transition= self.show_params['transition']
  
        # keep dwell and porch as an integer multiple of tick          
        self.porch = 1000 #length of pre and post porches for an image (milliseconds)
        self.tick = 100 # tick time for image display (milliseconds)
        self.dwell = (1000*self.duration)- (2*self.porch)
        if self.dwell<0: self.dwell=0

        self.centre_x = int(self.canvas['width'])/2
        self.centre_y = int(self.canvas['height'])/2

        #create an instance of PPIO so we can create gpio events
        self.ppio = PPIO()

    def play(self,
                    track,
                    end_callback,
                    ready_callback,
                    enable_menu=False,
                    starting_callback=None,
                    playing_callback=None,
                    ending_callback=None):
                        
        # instantiate arguments
        self.track=track
        self.enable_menu=enable_menu
        self.ready_callback=ready_callback
        self.end_callback=end_callback

        #init state and signals
        self.state=ImagePlayer.NO_SLIDE
        self.quit_signal=False
        self.kill_required_signal=False
        self.error=False
        self._tick_timer=None
        self.drawn=None
        self.paused=False
        self.pause_text=None

        if os.path.exists(self.track)==True:
            self.pil_image=PIL.Image.open(self.track)
            # adjust brightness and rotate (experimental)
            # pil_image_enhancer=PIL.ImageEnhance.Brightness(pil_image)
            # pil_image=pil_image_enhancer.enhance(0.1)
            # pil_image=pil_image.rotate(45)
            # tk_image = PIL.ImageTk.PhotoImage(pil_image)
        else:
            self.pil_image=None

        # and start image rendering
        self.mon.log(self,'playing track from show Id: '+str(self.show_id))
        self._start_front_porch()

        
    def key_pressed(self,key_name):
        if key_name=='':
            return
        elif key_name in ('p',' '):
            self.pause()
        elif key_name=='escape':
            self._stop()
            return

    def button_pressed(self,button,edge):
        if button =='pause':
            self.pause()
        elif button=='stop':
            self._stop()
            return

    def terminate(self,reason):
        if reason=='error':
            self.error=True
            self.quit_signal=True
        else:
            self.kill_required_signal=True
            self.quit_signal=True

    def pause(self):
        if not self.paused:
            self.paused = True
        else:
            self.paused=False

    
        
# *******************
# internal functions
# *******************

    def _stop(self):
        self.quit_signal=True
        
    def _error(self):
        self.error=True
        self.quit_signal=True
  
     #called when back porch has completed or quit signal is received
    def _end(self,reason,message):
        if self._tick_timer<>None:
            self.canvas.after_cancel(self._tick_timer)
            self._tick_timer=None
        self.quit_signal=False
        # self.canvas.delete(ALL)
        self.canvas.update_idletasks( )
        self.state=self.NO_SLIDE
        if self.error==True or reason=='error':
            self.end_callback("error",message)
            self=None          
        elif self.kill_required_signal==True:
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
                self.end_callback("error",'error')
                self=None



    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self._error()
        else:
            return value



    def _start_front_porch(self):
        self.state=ImagePlayer.SLIDE_IN
        self.porch_counter=0
        if self.ready_callback<>None: self.ready_callback()

        if self.pil_image<>None or self.enable_menu== True or self.show_params['show-text']<> '' or self.track_params['track-text']<> '':
                self.canvas.delete(ALL)

        if self.transition=="cut":
            #just display the slide full brightness. No need for porch but used for symmetry
            if self.pil_image<>None:
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                      image=self.tk_img, anchor=CENTER)

  
        elif self.transition=="fade":
            #experimental start black and increase brightness (controlled by porch_counter).
            self._display_image()

        elif self.transition == "slide":
            #experimental, start in middle and move to right (controlled by porch_counter)
            if self.pil_image<>None:
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                  image=self.tk_img, anchor=CENTER)
            
        elif self.transition=="crop":
            #experimental, start in middle and crop from right (controlled by porch_counter)
            if self.pil_image<>None:
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                  image=self.tk_img, anchor=CENTER)
        self.canvas.update_idletasks()

        # create animation events
        error_text=self.ppio.animate(self.animate_begin_text,id(self))
        if error_text<>'':
            self.mon.err(self,error_text)
            self.error=True
            self._end()
                                                  
        self._tick_timer=self.canvas.after(self.tick, self._do_front_porch)
        
            
    def _do_front_porch(self):
        if self.quit_signal == True:
            self._end('normal','user quit')
        else:
            self.porch_counter=self.porch_counter+1
            # print "doing slide front porch " +str(self.porch_counter)
            self.canvas.config(bg='black')
            self._display_image()
            if self.porch_counter==self.porch/self.tick:
                self._start_dwell()
            else:
                self._tick_timer=self.canvas.after(self.tick,self._do_front_porch)


    def _start_dwell(self):
        self.state=ImagePlayer.SLIDE_DWELL
        self.dwell_counter=0
        self._tick_timer=self.canvas.after(self.tick, self._do_dwell)

        
    def _do_dwell(self):
        if self.quit_signal == True:
            self.mon.log(self,"quit received")
            self._end('normal','user quit')
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

            if self.dwell_counter==self.dwell/self.tick:
                self._start_back_porch()
            else:
                self._tick_timer=self.canvas.after(self.tick, self._do_dwell)

    def _start_back_porch(self):
        self.state=ImagePlayer.SLIDE_OUT
        self.porch_counter=self.porch/self.tick
        
        if self.transition=="cut":
             # just keep displaying the slide full brightness.
            # No need for porch but used for symmetry
             pass
            
        elif self.transition=="fade":
            #experimental start full and decrease brightness (controlled by porch_counter).
            self._display_image()

        elif self.transition== "slide":
            #experimental, start in middle and move to right (controlled by porch_counter)
            if self.pil_image<>None:
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                  image=self.tk_img, anchor=CENTER)
            
        elif self.transition =="crop":
            #experimental, start in middle and crop from right (controlled by porch_counter)
            if self.pil_image<>None:
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_image)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                  image=self.tk_img, anchor=CENTER)

        self._tick_timer=self.canvas.after(self.tick, self._do_back_porch)

            
    def _do_back_porch(self):
        if self.quit_signal == True:
            self._end('normal','user quit')
        else:
            self.porch_counter=self.porch_counter-1
            self._display_image()
            if self.porch_counter==0:
                self._end('normal','finished')
            else:
                self._tick_timer=self.canvas.after(self.tick,self._do_back_porch)

    



    def _display_image(self):
        if self.transition=="cut":
            pass
        
        # all the methods below have incorrect code !!!
        elif self.transition=="fade":
            if self.pil_image<>None:
                self.enh=PIL.ImageEnhance.Brightness(self.pil_image)
                prop=float(self.porch_counter)/float(20)  #????????
                self.pil_img=self.enh.enhance(prop)
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_img)
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                      image=self.tk_img, anchor=CENTER)

        elif self.transition=="slide":
            if self.pil_image<>None:
                self.canvas.move(self.drawn,5,0)
            
        elif self.transition=="crop":
            if self.pil_image<>None:
                self.crop= 10*self.porch_counter
                self.pil_img=self.pil_image.crop((0,0,1000-self.crop,1080))
                self.tk_img=PIL.ImageTk.PhotoImage(self.pil_img)           
                self.drawn = self.canvas.create_image(self.centre_x, self.centre_y,
                                                      image=self.tk_img, anchor=CENTER)


        # display instructions if enabled
       
        if self.enable_menu== True:
            self.canvas.create_text(self.centre_x, int(self.canvas['height']) - int(self.show_params['hint-y']),
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
            
        self.canvas.update_idletasks( )

