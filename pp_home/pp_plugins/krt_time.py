"""
This example just writes to the screen directly.
The track file is just pased through unaltered

The local time is read and is written direct to the Tkinter canvas 
that is used by Pi Presents to display its output.

Writing to the screen is done in a function which is triggered by Tkinter canvas.after()
which is a non-blocking equivalent of sleep()


"""

import os
import time
from Tkinter import *
import Tkinter


class Plugin:

    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        self.timer=None

 
    def do_plugin(self,track_file):

        # was the player called from a liveshow?
        if self.show_params['type']=='liveshow':
            self.liveshow=True
        else:
            self.liveshow=False

        # if plugin is called in a liveshow then  a track file will not be provided so maybe get one from the plugin cfg file
        if self.liveshow==True:
            self.track_file=self.plugin_params['track-file']
        else:
            # just pass the track file though unmodified
            self.track_file=track_file

        
        # just return the track file
        self.used_file=self.track_file


        #kick off the function to draw the time to the screen
        self.timer=self.canvas.after(10,self.draw_time)
        
        #and return the track to play.
        return 'normal','',self.used_file


    def draw_time(self):
        
        time_text='My Local Time is: ' + time.asctime()

         # delete the time written on the previous iteration
        self.canvas.delete('krt-time')
        
        #krt-time tag allows deletion before update
        # pp-content tag ensures that Pi Presents deletes the text at the end of the track
        # it must be inclued
        self.canvas.create_text(100,10,
                                        anchor=NW,
                                      text=time_text,
                                      fill='white',
                                      font='arial 20 bold',
                                        tag=('krt-time','pp-content'))
        
        # and kick off draw_time() again in one second
        self.timer=self.canvas.after(1000,self.draw_time)



    def stop_plugin(self):
        # gets called by Pi Presents at the end of the track
        #stop the timer as the stop_plugin may have been called while it is running
        if self.timer<>None:
            self.canvas.after_cancel(self.timer)

        
