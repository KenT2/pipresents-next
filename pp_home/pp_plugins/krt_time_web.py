"""
This example  demonstrates the dynamic creation of a web page.


"""

import os
import time

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

        #ignir ethe track_file as we are going to create one
        # define path of the temporary file to take the output of plugin.
        self.used_file='/tmp/time.htm'


        #create the weather image in used_file
        self.draw_time()

        #and return the image modified with draw_time.
        return 'normal','',self.used_file



    def draw_time(self):

        start_text='<head></head>\n<body>\n<h1>HTML created by krt_time_web.py plugin</h1>'

        time_text='My Local Time is: ' + time.asctime()
        end_text='\n</body>'

        handle=open(self.used_file,'w')
        handle.write(start_text+time_text+end_text)
        handle.close()






    def stop_plugin(self):
        # gets called by Pi Presents at the end of the track
        #stop the timer as the stop_plugin may have been called while it is running
        if self.timer<>None:
            self.canvas.after_cancel(self.timer)
        # delete the temporary file
        os.remove(self.used_file)
        
