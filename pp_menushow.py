import os

from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_imageplayer import ImagePlayer
from pp_medialist import MediaList
from pp_videoplayer import VideoPlayer
from pp_audioplayer import AudioPlayer
from pp_messageplayer import MessagePlayer
from pp_resourcereader import ResourceReader
from pp_controlsmanager import ControlsManager
from pp_utils import Monitor


class MenuShow:
    """ Displays a menu with optional hint below it. User can traverse the menu and
              select a track using key or button presses.
        Interface:
         * play - displays the menu and selects the first entry
         * input_pressed,  - receives user events passes them to a Player if a track is playing,
                otherwise actions them with _next, _previous, _play_selected_track, _end
         Optional display of eggtimer by means of Players ready_callback
         Supports imageplayer, videoplayer,messagplayer,audioplayer,menushow,mediashow
         Destroys itself on exit
    """

# *********************
# external interface
# ********************

    def __init__(self,
                            show_params,
                            canvas,
                            showlist,
                            pp_home,
                            pp_profile):
        """ canvas - the canvas that the menu is to be written on
            show - the name of the configuration dictionary section for the menu
            showlist  - the showlist
            pp_home - Pi presents data_home directory
            pp_profile - Pi presents profile directory"""
        
        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_params=show_params
        self.showlist=showlist
        self.canvas=canvas
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # open resources
        self.rr=ResourceReader()
        
        # init variables
        self.drawn  = None
        self.player=None
        self.shower=None
        self.menu_timeout_running=None
        self.error=False




    def play(self,show_id,end_callback,ready_callback,top=False,command='nil'):
        """ displays the menu 
              end_callback - function to be called when the menu exits
              ready_callback - callback when menu is ready to display (not used)
              top is True when the show is top level (run from [start])
        """
        
        #instantiate arguments
        self.show_id=show_id
        self.end_callback=end_callback
        self.ready_callback=ready_callback
        self.top=top
        self.command=command

        # check  data files are available.
        self.menu_file = self.pp_profile + "/" + self.show_params['medialist']
        if not os.path.exists(self.menu_file):
            self.mon.err(self,"Medialist file not found: "+ self.menu_file)
            self.end('error',"Medialist file not found")
        
        #create a medialist for the menu and read it.
        self.medialist=MediaList()
        if self.medialist.open_list(self.menu_file,self.showlist.sissue()) == False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")

        #get control bindings for this show if top level
        controlsmanager=ControlsManager()
        if self.top==True:
            self.controls_list=controlsmanager.default_controls()
            # and merge in controls from profile
            self.controls_list=controlsmanager.merge_show_controls(self.controls_list,self.show_params['controls'])

           
        if self.show_params['has-background']=="yes":
            background_index=self.medialist.index_of_track ('pp-menu-background')
            if background_index>=0:
                self.menu_img_file = self.complete_path(self.medialist.track(background_index))
                if not os.path.exists(self.menu_img_file):
                    self.mon.err(self,"Menu background file not found: "+ self.menu_img_file)
                    self.end('error',"Menu background file not found")
            else:
                self.mon.err(self,"Menu background not found in medialist")
                self.end('error',"Menu background not found")
                               
        self.end_menushow_signal= False
        if self.ready_callback<>None:
            self.ready_callback()

        self.menu_timeout_value=int(self.show_params['timeout'])*1000
        self.do_menu()


    def do_menu(self):
        #start timeout alarm if required
        if int(self.show_params['timeout'])<>0:
            self.menu_timeout_running=self.canvas.after(self.menu_timeout_value,self.timeout_menu)

        self.canvas.config(bg='black')
        self.canvas.delete('pp-content')
        self.canvas.update()
        
        # display background image
        if self.show_params['has-background']=="yes":
            self.display_background()

        self.delete_eggtimer()
        
       #display the list of tracks
        self.display_track_titles()

        # display instructions (hint)
        self.canvas.create_text(int(self.canvas['width'])/2,
                                int(self.canvas['height']) - int(self.show_params['hint-y']),
                                text=self.show_params['hint-text'],
                                fill=self.show_params['hint-colour'],
                                font=self.show_params['hint-font'],
                                tag='pp-content')
        self.canvas.update( )


    #stop received from another concurrent show
    def managed_stop(self):
        if self.menu_timeout_running<>None:
            self.canvas.after_cancel(self.menu_timeout_running)
            self.menu_timeout_running=None
        if self.shower<>None:
            self.shower.managed_stop()
        elif self.player<>None:
            self.end_menushow_signal=True
            self.player.input_pressed('stop')
        else:
            self.end('normal','stopped by ShowManager')
            

    # kill or error received
    def terminate(self,reason):
        if self.menu_timeout_running<>None:
            self.canvas.after_cancel(self.menu_timeout_running)
            self.menu_timeout_running=None
        if self.shower<>None:
            self.shower.terminate(reason)
        elif self.player<>None:
            self.player.terminate(reason)
        else:
            self.end(reason,'Terminated no shower or player running')



   # respond to user inputs.
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
            if self.shower<>None:
                # if next lower show is running pass down operatin to  the show and lower levels
                self.shower.input_pressed(operation,source,edge) 
            else:
                #service the standard inputs for this show
                if operation=='stop':
                    if self.menu_timeout_running<>None:
                        self.canvas.after_cancel(self.menu_timeout_running)
                        self.menu_timeout_running=None
                    if self.shower<>None:
                        self.shower.input_pressed('stop',edge,source)
                    elif self.player<>None:
                        self.player.input_pressed('stop')
                    else:
                        # not at top so end the show
                        if  self.top == False:
                            self.end('normal',"exit from stop command")
                        else:
                            pass
              
                elif operation in ('up','down'):
                # if child or sub-show running and is a show pass down
                # if  child not running - move
                    if self.shower<>None:
                        self.shower.input_pressed(operation,edge,source)
                    else:
                        if self.player==None:
                            if self.menu_timeout_running<>None:
                                self.canvas.after_cancel(self.menu_timeout_running)
                                self.menu_timeout_running=self.canvas.after(self.menu_timeout_value,self.timeout_menu)
                            if operation=='up':
                                self.previous()
                            else:
                                self.next()
                        
                elif operation =='play':
                    # if child running and is show - pass down
                    # if no track already running  - play
                    if self.shower<>None:
                        self.shower.input_pressed(operation,edge,source)
                    else:
                        if self.player==None:
                            self.play_selected_track(self.medialist.selected_track())

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


# *********************
# INTERNAL FUNCTIONS
# ********************

# *********************
# Sequencing
# *********************

    def timeout_menu(self):
        self.end('normal','menu timeout')
        return
        
    def next(self):     
        self.highlight_menu_entry(self.menu_index,False)
        self.medialist.next('ordered')
        if self.menu_index==self.menu_length-1:
            self.menu_index=0
        else:
            self.menu_index+=1
        self.highlight_menu_entry(self.menu_index,True)     


    def previous(self):   
        self.highlight_menu_entry(self.menu_index,False)
        if self.menu_index==0:
            self.menu_index=self.menu_length-1
        else:
            self.menu_index-=1
        self.medialist.previous('ordered')
        self.highlight_menu_entry(self.menu_index,True)
        

     # at the end of a track just re-display the menu with the original callback from the menu       
    def what_next(self,message):
        # user wants to end
        if self.end_menushow_signal==True:
            self.end_menushow_signal=False
            self.end('normal',"show ended by user")
        else:
            self.do_menu()


# *********************
# Dispatching to Players
# *********************

    def play_selected_track(self,selected_track):
        """ selects the appropriate player from type field of the medialist and computes
              the parameters for that type
              selected track is a dictionary for the track/show
        """
         #remove menu and show working.....        

        if self.menu_timeout_running<>None:
            self.canvas.after_cancel(self.menu_timeout_running)
            self.menu_timeout_running=None
            
        self.canvas.delete('pp-content')
        self.display_eggtimer(self.resource('menushow','m01'))
    
        # dispatch track by type
        self.player=None
        self.shower=None
        track_type = selected_track['type']
        self.mon.log(self,"Track type is: "+ track_type)
        
        if track_type=="video":
            # create a videoplayer
            track_file=self.complete_path(selected_track)
            self.player=VideoPlayer(self.show_id,self.canvas,self.show_params,selected_track,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.delete_eggtimer,
                                        enable_menu=False)
                                        
        elif track_type=="audio":
            # create a audioplayer
            track_file=self.complete_path(selected_track)
            self.player=AudioPlayer(self.show_id,self.canvas,self.show_params,selected_track,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.delete_eggtimer,
                                        enable_menu=False)
                                        
        elif track_type=="image":
            # images played from menus don't have children
            track_file=self.complete_path(selected_track)
            self.player=ImagePlayer(self.show_id,self.canvas,self.show_params,selected_track,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                    self.showlist,
                                    self.end_player,
                                    self.delete_eggtimer,
                                    enable_menu=False,
                                    )
                                    
        elif track_type=="message":
            # bit odd because MessagePlayer is used internally to display text. 
            text=selected_track['text']
            self.player=MessagePlayer(self.show_id,self.canvas,self.show_params,selected_track,self.pp_home,self.pp_profile)
            self.player.play(text,
                                    self.showlist,
                                    self.end_player,
                                    self.delete_eggtimer,
                                    enable_menu=False
                                    )
 
        elif track_type=="show":
            # get the show from the showlist
            index = self.showlist.index_of_show(selected_track['sub-show'])
            if index >=0:
                self.showlist.select(index)
                selected_show=self.showlist.selected_show()
            else:
                self.mon.err(self,"Show not found in showlist: "+ selected_track['sub-show'])
                self.end("Unknown show")
          
            if selected_show['type']=="mediashow":    
                self.shower= MediaShow(selected_show,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.delete_eggtimer,top=False,command='nil')

            elif selected_show['type']=="liveshow":    
                self.shower= LiveShow(selected_show,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.delete_eggtimer,top=False,command='nil')

            elif selected_show['type']=="radiobuttonshow":
                self.shower= RadioButtonShow(selected_show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="hyperlinkshow":
                self.shower= HyperlinkShow(selected_show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')


            elif selected_show['type']=="menu": 
                self.shower= MenuShow(selected_show,
                                                        self.canvas,
                                                        self.showlist,
                                                        self.pp_home,
                                                        self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.delete_eggtimer,top=False,command='nil')                    
            else:
                self.mon.err(self,"Unknown Show Type: "+ selected_show['type'])
                self.end("Unknown show type")  
                
        else:
            self.mon.err(self,"Unknown Track Type: "+ track_type)
            self.end("Unknown track type")
    
    # callback from when player ends
    def end_player(self,reason,message):
        self.mon.log(self,"Returned from player with message: "+ message)
        self.player=None
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            self.display_eggtimer(self.resource('menushow','m02'))
            self.what_next(message)

    # callback from when shower ends
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,"Returned from shower with message: "+ message)
        self.shower=None
        if reason in ("killed","error"):
            self.end(reason,message)
        else:
            self.display_eggtimer(self.resource('menushow','m03'))
            self.what_next(message)  
   


# *********************
# Ending the show
# *********************
    # finish the player for killing, error or normally
    # this may be called directly if sub/child shows or players are not running
    # if they might be running then need to call terminate?????
    
    def end(self,reason,message):
        self.mon.log(self,"Ending menushow: "+ self.show_params['show-ref'])  
        if self.menu_timeout_running<>None:
            self.canvas.after_cancel(self.menu_timeout_running)
            self.menu_timeout_running=None
        self.end_callback(self.show_id,reason,message)
        self=None
        return


# *********************
# Displaying things
# *********************

    def display_background(self):
        pil_menu_img=PIL.Image.open(self.menu_img_file)
        self.menu_background = PIL.ImageTk.PhotoImage(pil_menu_img)
        self.drawn = self.canvas.create_image(int(self.canvas['width'])/2,
                                      int(self.canvas['height'])/2,
                                      image=self.menu_background,
                                      anchor=CENTER,
                                      tag='pp-content')


    def display_track_titles(self):
        self.menu_length=1
        self.menu_entry_id=[]
        x=int(self.show_params['menu-x'])
        y=int(self.show_params['menu-y'])
        self.medialist.start()
        while True:
            id=self.canvas.create_text(x,y,anchor=NW,
                                       text="* "+self.medialist.selected_track()['title'],
                                       fill=self.show_params['entry-colour'],
                                       font=self.show_params['entry-font'],
                                       tag='pp-content')
            self.menu_entry_id.append(id)
            y=y + int(self.show_params['menu-spacing'])
            if self.medialist.at_end():
                break
            self.menu_length+=1
            self.medialist.next('ordered')
            
        # select and highlight the first entry
        self.medialist.start()
        self.menu_index=0
        self.highlight_menu_entry(self.menu_index,True)
        
        self.canvas.tag_raise('pp-click-area')            
        self.canvas.update_idletasks( )
        
        # self.medialist.print_list()


    def highlight_menu_entry(self,index,state):
        if state==True:
            self.canvas.itemconfig(self.menu_entry_id[index],fill=self.show_params['entry-select-colour'])
        else:
            self.canvas.itemconfig(self.menu_entry_id[index],fill=self.show_params['entry-colour'])
    
    
    def display_eggtimer(self,text):
        # print "display eggtimer"
        self.canvas.create_text(int(self.canvas['width'])/2,
                                              int(self.canvas['height'])/2,
                                                  text= text,
                                                  fill='white',
                                                  font="Helvetica 20 bold",
                                                   tag='pp-eggtimer')
        self.canvas.update_idletasks( )


    def delete_eggtimer(self):
        # print"delete eggtimer"
        self.canvas.delete('pp-eggtimer')
        self.canvas.update_idletasks( )


# *********************
# utilities
# *********************

    def complete_path(self,selected_track):
        #  complete path of the filename of the selected entry
        track_file = selected_track['location']
        if track_file<>'' and track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        self.mon.log(self,"Track to play is: "+ track_file)
        return track_file     
         

    def resource(self,section,item):
        value=self.rr.get(section,item)
        if value==False:
            self.mon.err(self, "resource: "+section +': '+ item + " not found" )
            # timers may be running so need terminate
            self.terminate("error")
        else:
            return value

from pp_mediashow import MediaShow
from pp_liveshow import LiveShow
from pp_radiobuttonshow import RadioButtonShow
from pp_hyperlinkshow import HyperlinkShow
