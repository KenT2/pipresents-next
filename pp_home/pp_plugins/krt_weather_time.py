"""
This example adds writing to the screen directly using Tkinter.

The track file is modified saved and returned to be displayed as in krt_weather

In addition the local time is read and is written direct to the Tkinter canvas that is used by
Pi Presents to display its output.

Writing to the screen is done in a function which is triggered by Tkinter using canvas.after()
which is a non-blocking equivalent of sleep()

"""

import os
import time
from Tkinter import *
import Tkinter
import urllib,urllib2,re
from PIL import Image, ImageDraw, ImageFont

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

        # initialise the timer
        self.timer=None

 
    def do_plugin(self,track_file):

        # was the player called from a liveshow?
        if self.show_params['type']=='liveshow':
            self.liveshow=True
        else:
            self.liveshow=False

        # if plugin is called in a liveshow then  a track file will not be provided so need to get one from somewhere else or create one
        if self.liveshow==True: 
            self.track_file='/home/pi/pp_home/media/river.jpg'
            self.img = Image.open(self.track_file)
        else:
            # can use the file from track_params, but don't have to
            self.track_file=track_file
            self.img = Image.open(self.track_file)
            
        ##    print self.track_file
        ##    print self.liveshow
        
        # define path of the temporary file to take the output of plugin.
        self.used_file='/tmp/weather_time_ny.jpg'


        #create the weather image in used_file
        self.draw_weather()

        #kick off the function to draw the time to the screen
        self.timer=self.canvas.after(10,self.draw_time)
        
        #and return the image modified with draw_weather.
        return 'normal','',self.used_file



    def draw_weather(self):

        usrfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 30)
        tcolor=(0,0,0)
        
        # use the track file specified in the profile as the base of the weather report
        draw = ImageDraw.Draw(self.img)

        #use the zip code specified in the plugin configuraton file
        url='http://www.weather.com/weather/today/'+self.plugin_params['zip']
        
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        try:
            response = urllib2.urlopen(req,timeout=5)
         
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                text =  'The server could not fulfill the request. ' + str(e.code)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                self.img.save(self.used_file)
                
            elif hasattr(e, 'reason'):
                text =  'We failed to reach a server. ' + str(e.reason)
                draw.text((100,150),text,fill=tcolor,font=usrfont)
                self.img.save(self.used_file)
        else:
            # everything is fine
            link=response.read()
            response.close

            match2 = re.compile('<span itemprop="feels-like-temperature-fahrenheit">(.+?)</span>').findall(link)
            match3 = re.compile('<div class="wx-wind-label">(.+?)</div>').findall(link)
            match4 = re.compile('<div class="wx-phrase ">(.+?)</div>').findall(link)

            #edit text as you see fit, along with location on screen
            text2 = self.plugin_params['place']+", Current Temperature = " + match2[0]
            text3 = match4[0] + " with winds " + match3[0]
            draw.text((100,150),text2,fill=tcolor,font=usrfont)
            draw.text((100,200),text3,fill=tcolor,font=usrfont)

            del draw
            self.img.save(self.used_file)



    def draw_time(self):
        
        time_text='My Local Time is: ' + time.asctime()

         # delete the time written on the previous iteration
        self.canvas.delete('krt-time')
        
        #krt-time tag allows deletion before update. Use your intials to make avoid clashes
        # pp-content tag ensures that Pi Presents deletes the text at the end of the track
        # it must be inclued
        self.canvas.create_text(100,100,
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
        # delete the temporary file
        os.remove(self.used_file)
        
