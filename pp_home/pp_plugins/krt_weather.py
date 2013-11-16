"""
ACKNOWLEDGEMENTS 
-----------------------------------
This example plugin and the idea for plugins came from 2-sidedtoast on the Raspberry Pi forum
His original module at code.google.com/p/python-weather-images/ used a program separate from
Pi Presents and initiated by Cron to write the image to the liveshow directory.

I have integrated his idea into Pi Presents such that you can call a plugin from imageplayer, videoplayer, audioplayer, messageplayer  and browserplayer. Plugins work for all types of show but Livshows need special treatment.

API
----
Plugins are organised as Python Classes. Each instance of a Player creates an instance of a Plugin which calls __init__

__init__(....) allows the context to be passed to the plugin. Most of the arguments will not be used in a simple example. You can initialise your own state variables in __init__.

Arguments of __init__ :
    root -
    the top level window - not of great use to a track plugin.
    
    canvas -
    the Tkinter canvas on which all displayed output of the Player is written. A plugin could write to the canvas directly and return a blank file path (see krt_weather_time.py)
    
    plugin_params -
    dictionary of the parameters defined in the plugin configuration file that called this plugin
    e.g. plugin_params['place'] will return New York for this example.
    
    show_params -
    dictionary of show parameters, definitions in /pipresents/pp_definitions.py.
    
    track_params -
    dictionary of track parameters, definitions in /pipresents/pp_definitions.py
    
    pp_dir -
    path of pipresents directory
    
    pp_home -
    path of data home directory
    
    pp_profile -
    path of profile directory


The plugin code must be in the method do_plugin(self,....). It has the following argument:

    track_file/message_text -
    The file specified in the Location field of the profile entry for this track. If the plugin is called from within a liveshow then this will be blank. Note: The track file eventually played will be that whose path is returned by the plugin.
    
    For Messageplayer the argument contains the text that would be  displayed.

    do_plugin(self,....) Returns: status,message,filepath

    - status -
    normal,error.  error is for fatal errors and will cause Pi Presents to exit after displaying the error.
    The plugin should deal nicely with non-fatal errors, like temporary loss of the intenet connection, and return status=normal
    
    - message -
    an error message
    
    - filepath -
    Full path of the track file to  be used by the player. Blank if no file is to be played.
    The type of file should be compatible with the underlying player (omxplayer etc.)


      
The plugin code must  have the method stop_plugin(self)
    This method should be used to delete the temporary file. It has other uses, see the plugin krt_weather_time.py

EXAMPLE
-------------
An example follows. It demonstrates the principles.

"""
# 2-sidedtoast wrote:
#create image for pi presents that shows current weather conditions
#dunnsept at gmail dot com
##
# currently works for US locations, have not tested Canada eh.
# change URL and regex below for other weather sites/countries

import os
import urllib,urllib2,re
from PIL import Image, ImageDraw, ImageFont

# the class must be called Plugin
class Plugin:

    # it must have an __init__ with these arguments
    def __init__(self,root,canvas,plugin_params,track_params,show_params,pp_dir,pp_home,pp_profile):
        self.root=root
        self.canvas=canvas
        self.plugin_params=plugin_params
        self.track_params=track_params
        self.show_params=show_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        ##    print pp_dir
        ##    print pp_home
        ##    print pp_profile
        ##    print show_params['show-ref']
        ##    print track_params['type']
        ##    print plugin_params['zip']

        
    def do_plugin(self,track_file):

        # was the player called from a liveshow?
        if self.show_params['type']=='liveshow':
            self.liveshow=True
        else:
            self.liveshow=False

        # if plugin is called in a liveshow then  a track file will not be provided so need to get one from somewhere else or create one
        if self.liveshow==True: 
            self.track_file='/home/pi/pp_home/media/space.jpg'
            # check it exists and return a fatal error if not.
            if not os.path.exists(self.track_file):
                return 'error','file not found by plugin: ' + plugin_params['plugin']+ ' ' +self.track_file,''
            img = Image.open(self.track_file)
        else:
            # can use the file from the call, but don't have to
            self.track_file=track_file
            img = Image.open(self.track_file)
            
        ##    print self.track_file
        ##    print self.liveshow
        
        # define path of the temporary file to take the output of plugin.
        self.used_file='/tmp/weather_ny.jpg'
            
        usrfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30)
        tcolor=(0,0,0)
        draw = ImageDraw.Draw(img)

        #use the zip code specified in the plugin configuraton file
        url='http://www.weather.com/weather/today/'+self.plugin_params['zip']
    
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
 
        try:
            # think you need to keep the timeout low as urlopen is blocking
            response = urllib2.urlopen(req,timeout=5)
         
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                text =  'The server could not fulfill the request. ' + str(e.code)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                img.save(self.used_file)
                return 'normal','',self.used_file
            
            elif hasattr(e, 'reason'):
                text =  'We failed to reach a server. ' + str(e.reason)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                img.save(self.used_file)
                return 'normal','',self.used_file
            
        else:
            # everything is fine
            link=response.read()
            response.close

            match2 = re.compile('<span itemprop="feels-like-temperature-fahrenheit">(.+?)</span>').findall(link)
            match3 = re.compile('<div class="wx-wind-label">(.+?)</div>').findall(link)
            match4 = re.compile('<div class="wx-phrase ">(.+?)</div>').findall(link)

            #edit text as you see fit, get the place from the plugin configuration file.
            text2 = self.plugin_params['place']+", Current Temperature = " + match2[0]
            text3 = match4[0] + " with winds " + match3[0]
            draw.text((100,150),text2,fill=tcolor,font=usrfont)
            draw.text((100,200),text3,fill=tcolor,font=usrfont)

            del draw


            img.save(self.used_file)
            # and return the file you want displayed
            return 'normal','',self.used_file
            
    def stop_plugin(self):
        # delete the temporary file if you want.
        os.remove(self.used_file)
        
