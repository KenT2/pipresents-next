#! /usr/bin/env python

"""
Part of Pi Presents
Pi Presents is a presentation package, running on the Raspberry Pi, for museum exhibits, galleries, and presentations.
Copyright 2012/2013, Ken Thompson

See manual.pdf for instructions.
"""
import os
import sys
import copy
import traceback
from subprocess import call
import time

from Tkinter import *
import Tkinter as tk
import tkMessageBox

from pp_options import command_options
from pp_showlist import ShowList
from pp_menushow import MenuShow
from pp_liveshow import LiveShow
from pp_mediashow import MediaShow
from pp_utils import Monitor
from pp_utils import StopWatch
from pp_validate import Validator
from pp_showmanager import ShowManager
from pp_resourcereader import ResourceReader
from pp_timeofday import TimeOfDay


class PiPresents:

    def __init__(self):
        
        self.pipresents_issue="1.2"
        
        StopWatch.global_enable=False

#****************************************
# INTERPRET COMMAND LINE
# ***************************************

        self.options=command_options()
        

        pp_dir=sys.path[0]
        
        if not os.path.exists(pp_dir+"/pipresents.py"):
            tkMessageBox.showwarning("Pi Presents","Bad Application Directory")
            exit()

        
        #Initialise logging
        Monitor.log_path=pp_dir
        self.mon=Monitor()
        self.mon.on()
        if self.options['debug']==True:
            Monitor.global_enable=True
        else:
            Monitor.global_enable=False
 
        self.mon.log (self, "Pi Presents is starting")
        self.mon.log (self," OS and separator:" + os.name +'  ' + os.sep)
        self.mon.log(self,"sys.path[0] -  location of code: "+sys.path[0])
        # self.mon.log(self,"os.getenv('HOME') -  user home directory (not used): " + os.getenv('HOME'))
        # self.mon.log(self,"os.path.expanduser('~') -  user home directory: " + os.path.expanduser('~'))
        
        self.ppio=None
        self.tod=None
 
        # create  profile  for pp_editor test files if already not there.
        if not os.path.exists(pp_dir+"/pp_home/pp_profiles/pp_editor"):
            self.mon.log(self,"Making pp_editor directory") 
            os.makedirs(pp_dir+"/pp_home/pp_profiles/pp_editor")
            
            
        #profile path from -p option
        if self.options['profile']<>"":
            self.pp_profile_path="/pp_profiles/"+self.options['profile']
        else:
            self.pp_profile_path = "/pp_profiles/pp_profile"
        
       #get directory containing pp_home from the command,
        if self.options['home'] =="":
            home = os.path.expanduser('~')+ os.sep+"pp_home"
        else:
            home = self.options['home'] + os.sep+ "pp_home"
            
        self.mon.log(self,"pp_home directory is: " + home)          
        #check if pp_home exists.
        # try for 10 seconds to allow usb stick to automount
        # fall back to pipresents/pp_home
        self.pp_home=pp_dir+"/pp_home"
        for i in range (1, 10):
            self.mon.log(self,"Trying pp_home at: " + home +  " (" + str(i)+')')
            if os.path.exists(home):
                self.mon.log(self,"Using pp_home at: " + home)
                self.pp_home=home
                break
            time.sleep (1)

        #check profile exists, if not default to error profile inside pipresents
        self.pp_profile=self.pp_home+self.pp_profile_path
        if not os.path.exists(self.pp_profile):
            self.pp_profile=pp_dir+"/pp_home/pp_profiles/pp_profile"

        if self.options['verify']==True:
            val =Validator()
            if  val.validate_profile(None,pp_dir,self.pp_home,self.pp_profile,self.pipresents_issue,False) == False:
                tkMessageBox.showwarning("Pi Presents","Validation Failed")
                exit()
                
        # open the resources
        self.rr=ResourceReader()
        # read the file, done once for all the other classes to use.
        if self.rr.read(pp_dir,self.pp_home)==False:
            #self.mon.err(self,"Version of profile " + self.showlist.sissue() + " is not  same as Pi Presents, must exit")
            self._end('error','cannot find resources.cfg')            

        
        #initialise the showlists and read the showlists
        self.showlist=ShowList()
        self.showlist_file= self.pp_profile+ "/pp_showlist.json"
        if os.path.exists(self.showlist_file):
            self.showlist.open_json(self.showlist_file)
        else:
            self.mon.err(self,"showlist not found at "+self.showlist_file)
            self._end('error','showlist not found')

        if float(self.showlist.sissue())<>float(self.pipresents_issue):
            self.mon.err(self,"Version of profile " + self.showlist.sissue() + " is not  same as Pi Presents, must exit")
            self._end('error','wrong version of profile')
 
        # get the 'start' show from the showlist
        index = self.showlist.index_of_show('start')
        if index >=0:
            self.showlist.select(index)
            self.starter_show=self.showlist.selected_show()
        else:
            self.mon.err(self,"Show [start] not found in showlist")
            self._end('error','start show not found')

        
# ********************
# SET UP THE GUI
# ********************
        #turn off the screenblanking and saver
        if self.options['noblank']==True:
            call(["xset","s", "off"])
            call(["xset","s", "-dpms"])

        self.root=Tk()
        # control display of window decorations
        if self.options['fullscreen']==True:
            self.root.attributes('-fullscreen', True)
            #self.root = Tk(className="fspipresents")
            os.system('unclutter &')
        else:
            #self.root = Tk(className="pipresents")
            pass


        self.title='Pi Presents - '+ self.pp_profile
        self.icon_text= 'Pi Presents'
        
        self.root.title(self.title)
        self.root.iconname(self.icon_text)
        self.root.config(bg='black')
        
        # get size of the screen
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # set window dimensions
        self.window_height=self.screen_height
        self.window_width=self.screen_width
        self.window_x=0
        self.window_y=0
        if self.options['fullscreen']==True:
            bar=self.options['fullscreen']
            # allow just 2 pixels for the hidden taskbar - not any more
            if bar in ('left','right'):
                self.window_width=self.screen_width
            else:
                self.window_height=self.screen_height
            if bar =="left":
                self.window_x=0
            if bar =="top":
                self.window_y=0  
            self.root.geometry("%dx%d%+d%+d"  % (self.window_width,self.window_height,self.window_x,self.window_y))
            self.root.attributes('-zoomed','1')
        else:
            self.window_width=self.screen_width-600
            self.window_height=self.screen_height-200
            self.window_x=50
            self.root.geometry("%dx%d%+d%+d" % (self.window_width,self.window_height,self.window_x,self.window_y))
            

        #canvas covers the whole window
        self.canvas_height=self.window_height
        self.canvas_width=self.window_width
        
        # make sure focus is set.
        self.root.focus_set()

        #define response to main window closing.
        self.root.protocol ("WM_DELETE_WINDOW", self.on_break_key)

        # Always use CTRL-Break key to close the program as a get out of jail
        self.root.bind("<Break>",self.e_on_break_key)
        
        #pass all other keys along to start shows and hence to 'players'
        self.root.bind("<Escape>", self._escape_pressed)
        self.root.bind("<Up>", self._up_pressed)
        self.root.bind("<Down>", self._down_pressed)
        self.root.bind("<Return>", self._return_pressed)
        self.root.bind("<space>", self._pause_pressed)
        self.root.bind("p", self._pause_pressed)

        #setup a canvas onto which will be drawn the images or text
        self.canvas = Canvas(self.root, bg='black')

        self.canvas.config(height=self.canvas_height, width=self.canvas_width)
        self.canvas.pack()
        # make sure focus is set on canvas.
        self.canvas.focus_set()


# ****************************************
# INITIALISE THE APPLICATION AND START
# ****************************************
        self.shutdown_required=False
        
        #kick off GPIO if enabled by command line option
        if self.options['gpio']==True:
            from pp_gpio import PPIO
            # initialise the GPIO
            self.ppio=PPIO()
            # PPIO.gpio_enabled=False
            if self.ppio.init(pp_dir,self.pp_profile,self.canvas,50,self.button_pressed)==False:
                self._end('error','gpio error')
                
            # and start polling gpio
            self.ppio.poll()

        #kick off the time of day scheduler
        self.tod=TimeOfDay()
        self.tod.init(pp_dir,self.pp_home,self.canvas,500)
        self.tod.poll()

        # Create list of start shows initialise them and then run them

        self.show_manager=ShowManager()
        self.show_manager.init()
        self.run_start_shows()
        self.root.mainloop( )




# *********************
# EXIT APP
# *********************

    # kill or error
    def terminate(self,reason):
        needs_termination=False
        for show in self.show_manager.shows:
            if show[ShowManager.SHOW_OBJ]<>None:
                needs_termination=True
                self.mon.log(self,"Sent terminate to show "+ show[ShowManager.SHOW_REF])
                show[ShowManager.SHOW_OBJ].terminate(reason)
        if needs_termination==False:
            self._end(reason,'terminate - no termination of lower levels required')



    def tidy_up(self):
        #turn screen blanking back on
        if self.options['noblank']==True:
            call(["xset","s", "on"])
            call(["xset","s", "+dpms"])
        # tidy up gpio
        if self.options['gpio']==True and self.ppio<>None:
            self.ppio.terminate()
        #tidy up time of day scheduler
        if self.tod<>None:
            self.tod.terminate()
        #close logging files 
        self.mon.finish()

        
    def on_kill_callback(self):
        self.tidy_up()
        if self.shutdown_required==True:
            call(['sudo', 'shutdown', '-h', '-t 5','now'])
        else:
            exit()

    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self.terminate("error")
        else:
            return value

# *********************
# Key and button presses
# ********************

    def shutdown_pressed(self):
        self.root.after(5000,self.on_shutdown_delay)

    def on_shutdown_delay(self):
        if self.ppio.is_pressed('shutdown'):
            self.shutdown_required=True
            self.on_break_key()

    def button_pressed(self,index,button,edge):
        self.mon.log(self, "Button Pressed: "+button)
        if button=="shutdown":
            self.shutdown_pressed()
        else:
            for show in self.show_manager.shows:
                show_obj=show[ShowManager.SHOW_OBJ]
                if show_obj<>None:
                    show_obj.button_pressed(button,edge) 
                    
           

    # key presses - convert from events to call to _key_pressed
    def _escape_pressed(self,event): self._key_pressed("escape")              
    def _up_pressed(self,event): self._key_pressed("up")  
    def _down_pressed(self,event): self._key_pressed("down")  
    def _return_pressed(self,event): self._key_pressed("return")
    def _pause_pressed(self,event): self._key_pressed("p")
        

    def _key_pressed(self,key_name):
        self.mon.log(self, "Key Pressed: "+ key_name)
        for show in self.show_manager.shows:
                show_obj=show[ShowManager.SHOW_OBJ]
                if show_obj<>None:
                    show_obj.key_pressed(key_name)          


         
    def on_break_key(self):
        self.mon.log(self, "kill received from user")
        #terminate any running shows and players     
        self.mon.log(self,"kill sent to shows")   
        self.terminate('killed')
 
 
    def e_on_break_key(self,event):
        self.on_break_key()

# *********************
# SHOW RUNNING
# ********************   
        
# Extract shows from start show
    def run_start_shows(self):
        start_shows_text=self.starter_show['start-show']
        fields= start_shows_text.split()
        for field in fields:       
            show_index = self.showlist.index_of_show(field)
            if show_index >=0:
                self.showlist.select(show_index)
                show=self.showlist.selected_show()
            else:
                self.mon.err(self,"Show not found in showlist: "+ field)
                self._end('error','show not found in showlist')
                
            if show['type']=="mediashow":
                show_obj = MediaShow(show,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_home,
                                                                self.pp_profile)
                showmanager_index=self.show_manager.register_show(field)
                self.show_manager.set_running(showmanager_index,show_obj)
                show_obj.play(showmanager_index,self._end_play_show,top=True,command='nil')
 
             
            elif show['type']=="menu":
                show_obj = MenuShow(show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                showmanager_index=self.show_manager.register_show(field)
                self.show_manager.set_running(showmanager_index,show_obj)
                show_obj.play(showmanager_index,self._end_play_show,top=True,command='nil')

            elif show['type']=="liveshow":
                show_obj= LiveShow(show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                showmanager_index=self.show_manager.register_show(field)
                self.show_manager.set_running(showmanager_index,show_obj)
                show_obj.play(showmanager_index,self._end_play_show,top=True,command='nil')
                
            else:
                self.mon.err(self,"unknown mediashow type in start show - "+ show['type'])
                self._end('error','unknown mediashow type')


    def _end_play_show(self,showmanager_index,reason,message):     
        self.mon.log(self,"Show " + str(showmanager_index) + " returned to Pipresents with reason: " + reason )
        self.show_manager.set_stopped(showmanager_index)
        # if all the shows have ended then end Pi Presents
        if self.show_manager.all_shows_stopped()==True:
            self._end(reason,message)
            
     
    def _end(self,reason,message):
        self.mon.log(self,"Pi Presents ending with message: " + message)
        if reason=='error':
            self.mon.log(self, "exiting because of error")
            self.tidy_up()
            exit()            
        if reason=='killed':
            self.mon.log(self,"kill received - exiting")
            self.on_kill_callback()
        else:
            # should never be here or fatal error
            self.mon.log(self, "exiting because invalid end reasosn")
            self.tidy_up()
            exit()

             
        

if __name__ == '__main__':

    pp = PiPresents()
    #try:
        #pp = PiPresents()
    #except:
        # traceback.print_exc(file=open("/home/pi/pp_exceptions.log","w"))
        #pass


