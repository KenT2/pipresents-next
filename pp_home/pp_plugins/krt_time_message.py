"""
This example works for message tracks
It modifies the message text which is provided by the player
and returns the modified text.
It also  writes to the screen directly.

Plugin configuration files of message type can be added to a liveshow
in addition to specifying this plugin in message tracks of other types of show.

The local time is read and is written direct to the Tkinter canvas used by
Pi Presents to display its output.

Writing to the screen is done in a function which is triggered by Tkinter canvas. after()
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

 
    def do_plugin(self,message_text):

        # was the player called from a liveshow?
        if self.show_params['type']=='liveshow':
            self.liveshow=True
        else:
            self.liveshow=False

        # if plugin is called in a liveshow then  a track file will not be provided so maybe get one from the plugin cfg file
        if self.liveshow==True:
            self.message_text=' this text has been supplied by the krt_time_message.py plugin'
        else:
            # just pass get the text so we can add to it later
            self.message_text=message_text + '\nThis line added by the krt_time_message.py plugin'




        #kick off the function to draw the time to the screen
        self.timer=self.canvas.after(10,self.draw_time)
        
        #and return the modified text
        return 'normal','',self.message_text


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

        
