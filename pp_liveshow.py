import os
import copy
import ConfigParser
from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_imageplayer import ImagePlayer
from pp_videoplayer import VideoPlayer
from pp_audioplayer import AudioPlayer
from pp_browserplayer import BrowserPlayer
from pp_medialist import MediaList
from pp_messageplayer import MessagePlayer
from pp_resourcereader import ResourceReader
from pp_definitions import PPdefinitions
from pp_timeofday import TimeOfDay
from pp_options import command_options
from pp_controlsmanager import ControlsManager
from pp_utils import Monitor

class LiveShow:
    """ plays a set of tracks the content of which is dynamically specified by plaacing track files
                in one of two directories. Tracks are played in file leafname alphabetical order.
                Can be interrupted
    """
            
# *******************
# External interface
# ********************

    def __init__(self,
                            show_params,
                             root,
                            canvas,
                            showlist,
                             pp_dir,
                            pp_home,
                            pp_profile):

        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_params =show_params
        self.showlist=showlist
        self.root=root
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # open resources
        self.rr=ResourceReader()

        #create and instance of TimeOfDay scheduler so we can add events
        self.tod=TimeOfDay()


        # Init variables
        self.player=None
        self.shower=None
        self.end_liveshow_signal=False
        self.end_trigger_signal= False
        self.play_child_signal = False
        self.error=False
        self.egg_timer=None
        self.duration_timer=None
        self.state='closed'
        self.livelist=None
        self.new_livelist= None



    def play(self,show_id,end_callback,ready_callback, top=False,command='nil'):

        #instantiate the arguments
        self.show_id=show_id
        self.end_callback=end_callback
        self.ready_callback=ready_callback
        self.top=top
        self.mon.log(self,"Starting show: " + self.show_params['show-ref'])

        # check  data files are available.
        self.media_file = self.pp_profile + os.sep + self.show_params['medialist']
        if not os.path.exists(self.media_file):
            self.mon.err(self,"Medialist file not found: "+ self.media_file)
            self.end_liveshow_signal=True
            
        self.options=command_options()
               
        self.pp_live_dir1 = self.pp_home + os.sep + 'pp_live_tracks'
        if not os.path.exists(self.pp_live_dir1):
            os.mkdir(self.pp_live_dir1)

        self.pp_live_dir2=''   
        if self.options['liveshow'] <>"":
            self.pp_live_dir2 = self.options['liveshow']
            if not os.path.exists(self.pp_live_dir2):
                self.mon.err(self,"live tracks directory not found " + self.pp_live_dir2)
                self.end('error',"live tracks directory not found")

        #create a medialist for the liveshow and read it.
        # it should be empty of anonymous tracks but read it to check its version.
        self.medialist=MediaList()
        if self.medialist.open_list(self.media_file,self.showlist.sissue())==False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")

        #get control bindings for this show if top level
        controlsmanager=ControlsManager()
        if self.top==True:
            self.controls_list=controlsmanager.default_controls()
            # and merge in controls from profile
            self.controls_list=controlsmanager.merge_show_controls(self.controls_list,self.show_params['controls'])

        #set up the time of day triggers for the show
        if self.show_params['trigger-start']in('time','time-quiet'):
            error_text=self.tod.add_times(self.show_params['trigger-start-time'],id(self),self.tod_start_callback,self.show_params['trigger-start'])
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)
                
        if self.show_params['trigger-end']=='time':
            error_text=self.tod.add_times(self.show_params['trigger-end-time'],id(self),self.tod_end_callback,'n/a')
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)

        if self.show_params['trigger-end']=='duration':
            error_text=self.calculate_duration(self.show_params['trigger-end-time'])
            if error_text<>'':
                self.mon.err(self,error_text)
                self.end('error',error_text)       

        self.wait_for_trigger()                


    def managed_stop(self):
        # if next lower show eor player is running pass down to stop the show/track
        if self.shower<>None:
            self.shower.managed_stop()
        else:
            self.end_liveshow_signal=True
            if self.player<>None:
                self.player.input_pressed('stop')

                
    # kill or error
    def terminate(self,reason):
        if self.shower<>None:
            self.shower.terminate(reason)
        elif self.player<>None:
            self.player.terminate(reason)
        else:
            self.end(reason,'terminated without terminating shower or player')

 
   # respond to key presses.
    def input_pressed(self,symbol,edge,source):
        self.mon.log(self,"received key: " + symbol)
        if self.show_params['disable-controls']=='yes':
            return 

       # if at top convert symbolic name to operation otherwise lower down we have received an operation
        # look through list of standard symbols to find match (symbolic-name, function name) operation =lookup (symbol
        if self.top==True:
            operation=self.lookup_control(symbol,self.controls_list)
        else:
            operation=symbol
        # print 'operation',operation
        # if no match for symbol against standard operations then return
        if operation=='':
            return

        else:
            #service the standard inputs for this show
            if operation=='stop':
                # if next lower show eor player is running pass down to stop the show/track
                # ELSE stop this show except for exceptions
                if self.shower<>None:
                    self.shower.input_pressed('stop',edge,source)
                elif self.player<>None:
                    self.player.input_pressed('stop')
                else:
                    # not at top so stop the show
                    if  self.top == False:
                        self.end_liveshow_signal=True
                    else:
                        pass
        
            elif operation in ('up','down'):
            # if child or sub-show is running and is a show pass to show, track does not use up/down
                if self.shower<>None:
                    self.shower.input_pressed(operation,edge,source)

                    
            elif operation=='play':
                # if child show or sub-show is running and is show - pass down
                # ELSE use Return to start child
                if self.shower<>None:
                    self.shower.input_pressed(operation,edge,source)
                else:
                    if self.show_params['has-child']=="yes":
                        self.play_child_signal=True
                        if self.player<>None:
                            self.player.input_pressed("stop")
                  
            elif operation == 'pause':
                # pass down if show or track running.
                if self.shower<>None:
                    self.shower.input_pressed(operation,edge,source)
                elif self.player<>None:
                    self.player.input_pressed(operation)

            elif operation[0:4]=='omx-' or operation[0:6]=='mplay-':
                if self.player<>None:
                    self.player.input_pressed(operation)
     
    def lookup_control(self,symbol,controls_list):
        for control in controls_list:
            if symbol == control[0]:
                return control[1]
        return ''

# ***************************
# Constructing Livelist
# ***************************       
        
    def livelist_add_track(self,afile):
        (root,title)=os.path.split(afile)
        (root_plus,ext)= os.path.splitext(afile)
        if ext.lower() in PPdefinitions.IMAGE_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['image'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.VIDEO_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['video'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.AUDIO_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['audio'],{'title':title,'track-ref':'','location':afile})
        if ext.lower() in PPdefinitions.WEB_FILES:
            self.livelist_new_track(PPdefinitions.new_tracks['web'],{'title':title,'track-ref':'','location':afile})
        if ext.lower()=='.cfg':
            self.livelist_new_plugin(afile,title)
           

    def livelist_new_plugin(self,plugin_cfg,title):

        # read the file which is a plugin cfg file into a dictionary
        self.plugin_config = ConfigParser.ConfigParser()
        self.plugin_config.read(plugin_cfg)
        self.plugin_params =  dict(self.plugin_config.items('plugin'))
        # create a new livelist entry of a type specified in the config file with plugin
        self.livelist_new_track(PPdefinitions.new_tracks[self.plugin_params['type']],{'title':title,'track-ref':'','plugin':plugin_cfg,'location':plugin_cfg})        

        
    def livelist_new_track(self,fields,values):
        new_track=fields
        self.new_livelist.append(copy.deepcopy(new_track))
        last = len(self.new_livelist)-1
        self.new_livelist[last].update(values)        
    

        
    def new_livelist_create(self):
     
        self.new_livelist=[]
        if os.path.exists(self.pp_live_dir1):
            for file in os.listdir(self.pp_live_dir1):
                file = self.pp_live_dir1 + os.sep + file
                (root_file,ext_file)= os.path.splitext(file)
                if (ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES+PPdefinitions.WEB_FILES) or (ext_file.lower()=='.cfg'):
                    self.livelist_add_track(file)
                    
        if os.path.exists(self.pp_live_dir2):
            for file in os.listdir(self.pp_live_dir2):
                file = self.pp_live_dir2 + os.sep + file
                (root_file,ext_file)= os.path.splitext(file)
                if ext_file.lower() in PPdefinitions.IMAGE_FILES+PPdefinitions.VIDEO_FILES+PPdefinitions.AUDIO_FILES+PPdefinitions.WEB_FILES or (ext_file.lower()=='.cfg'):
                    self.livelist_add_track(file)
                    

        self.new_livelist= sorted(self.new_livelist, key= lambda track: os.path.basename(track['location']).lower())
        # print 'LIVELIST'
        # for it in self.new_livelist:
            # print 'type: ', it['type'], 'loc: ',it['location'],'\nplugin cfg: ', it['plugin']
        # print ''


    
    def livelist_replace_if_changed(self):
        self.new_livelist_create()
        if  self.new_livelist<>self.livelist:
            self.livelist=copy.deepcopy(self.new_livelist)
            self.livelist_index=0
   
   
    def livelist_next(self):
        if self.livelist_index== len(self.livelist)-1:
            self.livelist_index=0
        else:
            self.livelist_index +=1


# ***************************
# Sequencing
# ***************************


    def wait_for_trigger(self):
        self.state='waiting'
        if self.ready_callback<>None:
            self.ready_callback()

        self.mon.log(self,"Waiting for trigger: "+ self.show_params['trigger-start'])

        if self.show_params['trigger-start'] in ('time','time-quiet'):
            # if next show is this one display text
            next_show=self.tod.next_event_time()
            if next_show[3]<>True:
                if next_show[1]=='tomorrow':
                    text = self.resource('liveshow','m04')
                else:
                    text = self.resource('liveshow','m03')                     
                text=text.replace('%tt',next_show[0])
                self.display_message(self.canvas,'text',text,0,self.play_first_track)  
            
        elif self.show_params['trigger-start']=="start":
            self.play_first_track()            
        else:
            self.mon.err(self,"Unknown trigger: "+ self.show_params['trigger-start'])
            self.end('error',"Unknown trigger type")

    # callbacks from time of day scheduler
    def tod_start_callback(self):
         if self.state=='waiting' and self.show_params['trigger-start']in('time','time-quiet'):
            self.play_first_track()      

    def tod_end_callback(self):
        if self.state=='playing' and self.show_params['trigger-end'] in ('time','duration'):
            self.end_trigger_signal=True
            if self.shower<>None:
                self.shower.input_pressed('stop','front','')
            elif self.player<>None:
                self.player.input_pressed('stop')

    def play_first_track(self):
        self.state='playing'
        # start duration timer
        if self.show_params['trigger-end']=='duration':
            # print 'set alarm ', self.duration
            self.duration_timer = self.canvas.after(self.duration*1000,self.tod_end_callback)
        self.new_livelist_create()
        self.livelist = copy.deepcopy(self.new_livelist)
        self.livelist_index = 0
        self.play_track()

        
    def play_track(self):        
        self.livelist_replace_if_changed()
        if len(self.livelist)>0:
            self.play_selected_track(self.livelist[self.livelist_index])
        else:
            self.display_message(self.canvas,None,self.resource('liveshow','m01'),5,self.what_next)


     
    def what_next(self):
        # end of show time trigger
        if self.end_trigger_signal==True:
            self.end_trigger_signal=False
            if self.top==True:
                self.state='waiting'
                self.wait_for_trigger()
            else:
                # not at top so stop the show
                self.end('normal','sub-show end time trigger')
                    
        # user wants to end 
        elif self.end_liveshow_signal==True:
            self.end_liveshow_signal=False
            self.end('normal',"show ended by user")
        
        # play child?
        elif self.play_child_signal == True:
            self.play_child_signal=False
            index = self.medialist.index_of_track('pp-child-show')
            if index >=0:
                #don't select the track as need to preserve mediashow sequence.
                child_track=self.medialist.track(index)
                self.display_eggtimer(self.resource('liveshow','m02'))
                self.play_selected_track(child_track)
            else:
                self.mon.err(self,"Child show not found in medialist: "+ self.show_params['pp-child-show'])
                self.end('error',"child show not found in medialist")
                
        # otherwise loop to next track                       
        else:
            self.livelist_next()
            self.play_track()
          
      
# ***************************
# Dispatching to Players/Shows 
# ***************************

    def ready_callback(self):
        self.delete_eggtimer()

    def play_selected_track(self,selected_track):
        """ selects the appropriate player from type field of the medialist and computes
              the parameters for that type
              selected_track is a dictionary for the track/show
        """
        self.canvas.delete('pp-content')
        
        # is menu required
        if self.show_params['has-child']=="yes":
            enable_child=True
        else:
            enable_child=False

        #dispatch track by type
        self.player=None
        self.shower=None
        track_type = selected_track['type']
        self.mon.log(self,"Track type is: "+ track_type)
                                      
        if track_type=="image":
            track_file=self.complete_path(selected_track)
            # images played from menus don't have children
            self.player=ImagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                    self.showlist,
                                    self.end_player,
                                    self.ready_callback,
                                    enable_menu=enable_child)
            
        elif track_type=="video":
            # create a videoplayer
            track_file=self.complete_path(selected_track)
            self.player=VideoPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=enable_child)
                   
        elif track_type=="audio":
            # create a audioplayer
            track_file=self.complete_path(selected_track)
            self.player=AudioPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=enable_child)
                                                
        elif track_type=="message":
            # bit odd because MessagePlayer is used internally to display text. 
            text=selected_track['text']
            self.player=MessagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(text,
                                    self.showlist,
                                    self.end_player,
                                    self.ready_callback,
                                    enable_menu=enable_child
                                    )

        elif track_type=="web":
            # create a browser
            track_file=self.complete_path(selected_track)
            self.player=BrowserPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.ready_callback,
                                        enable_menu=enable_child)
                                        
        elif track_type=="show":
            # get the show from the showlist
            index = self.showlist.index_of_show(selected_track['sub-show'])
            if index >=0:
                self.showlist.select(index)
                selected_show=self.showlist.selected_show()
            else:
                self.mon.err(self,"Show not found in showlist: "+ selected_track['sub-show'])
                self.end_liveshow_signal=True
                
            if selected_show['type']=="mediashow":    
                self.shower= MediaShow(selected_show,
                                                               self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                               self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            
            elif selected_show['type']=="menu":
                self.shower= MenuShow(selected_show,
                                                          self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                          self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="radiobuttonshow":
                self.shower= RadioButtonShow(selected_show,
                                                         self.root,
                                                        self.canvas,
                                                        self.showlist,
                                                         self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="hyperlinkshow":
                self.shower= HyperlinkShow(selected_show,
                                                       sef.root,
                                                        self.canvas,
                                                        self.showlist,
                                                       self.pp_dir,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')
                
            else:
                self.mon.err(self,"Unknown Show Type: "+ selected_show['type'])
                self.end_liveshow_signal=True
                                                                            
        else:
            self.mon.err(self,"Unknown Track Type: "+ track_type)
            self.end_liveshow_signal=True
            

    def end_shower(self,show_id,reason,message):
        self.mon.log(self,"Returned from shower with message: "+ message)
        self.shower=None
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            self.what_next()  
        
    def end_player(self,reason,message):
        self.mon.log(self,"Returned from player with message: "+ message)
        self.player=None
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            self.what_next()


# ***************************
# end of show 
# ***************************

    def end(self,reason,message):
        self.end_liveshow_signal=False
        self.mon.log(self,"Ending Liveshow: "+ self.show_params['show-ref'])
        self.tidy_up()
        self.end_callback(self.show_id,reason,message)
        self=None

    
    def tidy_up(self):
        if self.duration_timer<>None:
            self.canvas.after_cancel(self.duration_timer)
            self.duration_timer=None
        #clear outstanding time of day events for this show
        # self.tod.clear_times_list(id(self))     


# ******************************
# Displaying things
# *********************************
        
    def display_eggtimer(self,text):
        self.egg_timer=self.canvas.create_text(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                                  text= text,
                                                  fill='white',
                                                  font="Helvetica 20 bold",
                                                   tag='pp-eggtimer')
        self.canvas.update_idletasks( )


    def delete_eggtimer(self):
        self.canvas.delete('pp-eggtimer')
        self.canvas.update_idletasks( )

    # used to display internal messages in situations where a medialist entry could not be used.
    def display_message(self,canvas,source,content,duration,display_message_callback):
            self.display_message_callback=display_message_callback
            tp={'duration':duration,'message-colour':'white','message-font':'Helvetica 20 bold','message-justify':'left',
                'background-colour':'','background-image':'','show-control-begin':'','show-control-end':'',
                'animate-begin':'','animate-clear':'','animate-end':'','message-x':'','message-y':'',
                'display-show-background':'no','display-show-text':'no','show-text':'','track-text':'',
                'plugin':''}
            self.player=MessagePlayer(self.show_id,self.root,canvas,tp,tp,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(content,self.showlist,self.display_message_end,None)

   
    def  display_message_end(self,reason,message):
        self.player=None
        if reason in ("killed",'error'):
            self.end(reason,message)
        else:
            self.display_message_callback()


# ******************************
# utilities
# *********************************

    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            self.terminate("error",'Cannot find resource')
        else:
            return value
        

    def complete_path(self,selected_track):
        #  complete path of the filename of the selected entry
        track_file = selected_track['location']
        if track_file<>'' and track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Track to play is: "+ track_file)
        return track_file     
         

    def calculate_duration(self,line):
        fields=line.split(':')
        if len(fields)==1:
            secs=fields[0]
            minutes='0'
            hours='0'
        if len(fields)==2:
            secs=fields[1]
            minutes=fields[0]
            hours='0'
        if len(fields)==3:
            secs=fields[2]
            minutes=fields[1]
            hours=fields[0]
        self.duration=3600*long(hours)+60*long(minutes)+long(secs)
        return ''

        
from pp_menushow import MenuShow
from pp_mediashow import MediaShow
from pp_radiobuttonshow import RadioButtonShow
from pp_hyperlinkshow import HyperlinkShow
