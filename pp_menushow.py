import os
import copy

from Tkinter import *
import Tkinter as tk
import PIL.Image
import PIL.ImageTk
import PIL.ImageEnhance

from pp_imageplayer import ImagePlayer
from pp_medialist import MediaList
from pp_videoplayer import VideoPlayer
from pp_audioplayer import AudioPlayer
from pp_browserplayer import BrowserPlayer
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
                             root,
                            canvas,
                            showlist,
                             pp_dir,
                            pp_home,
                            pp_profile):
        """ canvas - the canvas that the menu is to be written on
            show - the name of the configuration dictionary section for the menu
            showlist  - the showlist
            pp_home - Pi presents data_home directory
            pp_profile - Pi presents profile directory"""
        
        self.mon=Monitor()
        self.mon.on()
        
        self.display_guidelines_command=show_params['menu-guidelines']
        self.display_guidelines=self.display_guidelines_command

        
        #instantiate arguments
        self.show_params=show_params
        self.root=root
        self.canvas=canvas
        self.showlist=showlist
        self.pp_dir=pp_dir
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
                self.menu_img_file = self.complete_path(self.medialist.track(background_index)['location'])
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

        if self.show_params['menu-background-colour']<>'':
            self.canvas.config(bg=self.show_params['menu-background-colour'])
            
        self.canvas.delete('pp-content')
        self.canvas.update()
        
        # display background image
        if self.show_params['has-background']=="yes":
            self.display_background()

        self.delete_eggtimer()
        self.display_new_menu()
        self.canvas.tag_raise('pp-click-area')            
        self.canvas.update_idletasks( )

        # display menu text if enabled
        if self.show_params['menu-text']<> '':
            self.canvas.create_text(int(self.show_params['menu-text-x']),int(self.show_params['menu-text-y']),
                                                    anchor=NW,
                                                  text=self.show_params['menu-text'],
                                                  fill=self.show_params['menu-text-colour'],
                                                  font=self.show_params['menu-text-font'],
                                                  tag='pp-content')

        self.canvas.update_idletasks( )
        
        # display instructions (hint)
        hint_text=self.show_params['hint-text']
        if hint_text<>'':
            self.canvas.create_text(int(self.show_params['hint-x']),int(self.show_params['hint-y']),
                                                    anchor=NW,
                                text=hint_text,
                                fill=self.show_params['hint-colour'],
                                font=self.show_params['hint-font'],
                                tag='pp-content')

        self.canvas.update_idletasks( )


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
        self.mon.log(self,"Show Id: "+str(self.show_id)+" received key or operation: " + symbol)
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
                        
                elif operation[0:4]=='omx-' or operation[0:6]=='mplay-'or operation[0:5]=='uzbl-':
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
            track_file=self.complete_path(selected_track['location'])
            self.player=VideoPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.delete_eggtimer,
                                        enable_menu=False)
                                        
        elif track_type=="audio":
            # create a audioplayer
            track_file=self.complete_path(selected_track['location'])
            self.player=AudioPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.delete_eggtimer,
                                        enable_menu=False)
                                        
        elif track_type=="image":
            # images played from menus don't have children
            track_file=self.complete_path(selected_track['location'])
            self.player=ImagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                    self.showlist,
                                    self.end_player,
                                    self.delete_eggtimer,
                                    enable_menu=False,
                                    )
            
        elif track_type=="web":
            # create a browser
            track_file=self.complete_path(selected_track['location'])
            self.player=BrowserPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.delete_eggtimer,
                                        enable_menu=False)

                                    
        elif track_type=="message":
            # bit odd because MessagePlayer is used internally to display text. 
            text=selected_track['text']
            self.player=MessagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
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
                                                                self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                               self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.delete_eggtimer,top=False,command='nil')

            elif selected_show['type']=="liveshow":    
                self.shower= LiveShow(selected_show,
                                                                 self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                                self.pp_dir,
                                                                self.pp_home,
                                                                self.pp_profile)
                self.shower.play(self.show_id,self.end_shower,self.delete_eggtimer,top=False,command='nil')

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


   
    
    def display_new_menu(self):

        # calculate menu geometry
        error,reason=self.calculate_geometry()
        if error<>'normal':
            self.mon.err(self,"Menu geometry error: "+ reason)
            self.end('error',"Menu geometry error")
        else:
            # display the menu entries
            self.display_menu_entries()


    def display_menu_entries(self):
        # init the loop
        column_index=0
        row_index=0
        self.menu_length=1
        
        # id store is a list of elements each being a list of the three ids of the elements of the entry
        self.menu_entry_id=[]
        # offsets for the above
        self.icon_id_index=0 # rectangle around the icon
        self.image_id_index=1 # icon image - needed for tkinter
        self.text_id_index=2 # the text - need whn no icon is displayed

        #select the startof the medialist
        self.medialist.start()

        #loop through menu entries
        while True:
            #display the entry
            #calculate top left corner of entry
            self.calculate_entry_position(column_index,row_index)


            # display the button strip
            self.display_entry_strip()

            #display the selected entry highlight
            icon_id=self.display_icon_rectangle()

            #display the image in the icon
            image_id=self.display_icon_image()

            if self.show_params['menu-text-mode']<>'none':
                text_id=self.display_icon_text()
            else:
                text_id=None

            #append id's to the list
            self.menu_entry_id.append([icon_id,image_id,text_id])

            self.canvas.update_idletasks( )            
            #and loop
            if self.medialist.at_end():
                break
            self.menu_length+=1
            self.medialist.next('ordered')

            if self.direction=='horizontal':
                column_index+=1
                if column_index>=self.menu_columns:
                    column_index=0
                    row_index+=1
            else:
                row_index+=1
                if row_index>=self.menu_rows:
                    row_index=0
                    column_index+=1
                    
        # finally select and highlight the first entry
        self.medialist.start()
        self.menu_index=0
        self.highlight_menu_entry(self.menu_index,True)


    def print_geometry(self,total_width,total_height):
        print 'menu width: ', self.menu_width
        print 'columns', self.menu_columns
        print 'icon width: ', self.icon_width
        print 'horizontal padding: ', self.menu_horizontal_padding
        print 'text width: ', self.text_width
        print 'entry width: ', self.entry_width
        print 'total width: ', total_width
        print 'x separation: ', self.x_separation
        print ''
        print 'menu height', self.menu_height
        print 'rows: ', self.menu_rows
        print 'icon height', self.icon_height
        print 'vertical padding: ', self.menu_vertical_padding        
        print 'text height', self.text_height
        print 'entry height', self.entry_height
        print 'total height', total_height
        print 'y separation', self.y_separation

        
    # ------------------------------------------------------------------
    #calculate menu entry size and separation between menu entries
    # ------------------------------------------------------------------
    def calculate_geometry(self):

        self.display_strip=self.show_params['menu-strip']
        self.screen_width=int(self.canvas['width'])
        self.screen_height=int(self.canvas['height'])
        
        if self.display_strip=='yes':
            self.strip_padding=int(self.show_params['menu-strip-padding'])
        else:
            self.strip_padding=0

        # parse the menu window
        error,reason,self.menu_x_left,self.menu_y_top,self.menu_x_right,self.menu_y_bottom=self.parse_menu_window(self.show_params['menu-window'])
        if error<>'normal':
            return 'error',"Menu Window error: "+ reason

        if self.show_params['menu-icon-mode']=='none' and self.show_params['menu-text-mode']=='none':
            return 'error','Icon and Text are both None'
        if self.show_params['menu-icon-mode']=='none' and self.show_params['menu-text-mode']=='overlay':
            return 'error','cannot overlay none icon'

        self.direction=self.show_params['menu-direction']
        
        self.menu_width=self.menu_x_right - self.menu_x_left
        self.menu_height=self.menu_y_bottom - self.menu_y_top

        self.list_length=self.medialist.display_length()

        # get or calculate rows and columns
        if self.direction=='horizontal':
            if self.show_params['menu-columns']=='':
                return 'error','blank columns for horizontal direction'
            self.menu_columns=int(self.show_params['menu-columns'])
            self.menu_rows=self.list_length//self.menu_columns
            if self.list_length % self.menu_columns<>0:
                self.menu_rows+=1
        else:
            if self.show_params['menu-rows']=='':
                return 'error','blank rows for vertical direction'
            self.menu_rows=int(self.show_params['menu-rows'])
            self.menu_columns=self.list_length//self.menu_rows
            if self.list_length % self.menu_rows<>0:
                self.menu_columns+=1
                
        self.x_separation=int(self.show_params['menu-horizontal-separation'])
        self.y_separation=int(self.show_params['menu-vertical-separation'])

        # get size of padding depending on exitence of icon and text
        if self.show_params['menu-icon-mode'] in ('thumbnail','bullet') and self.show_params['menu-text-mode'] == 'right':
            self.menu_horizontal_padding=int(self.show_params['menu-horizontal-padding'])
        else:
            self.menu_horizontal_padding=0

        if self.show_params['menu-icon-mode'] in ('thumbnail','bullet') and self.show_params['menu-text-mode'] == 'below':
            self.menu_vertical_padding=int(self.show_params['menu-vertical-padding'])
        else:
            self.menu_vertical_padding=0
            
        #calculate size of icon depending on use
        if self.show_params['menu-icon-mode'] in ('thumbnail','bullet'):
            self.icon_width=int(self.show_params['menu-icon-width'])
            self.icon_height=int(self.show_params['menu-icon-height'])
        else:
            self.icon_width=0
            self.icon_height=0

        #calculate size of text box depending on mode
        if self.show_params['menu-text-mode']<>'none':
            self.text_width=int(self.show_params['menu-text-width'])
            self.text_height=int(self.show_params['menu-text-height'])
        else:
            self.text_width=0
            self.text_height=0
            
        # calculate size of entry box by combining text and icon sizes
        if self.show_params['menu-text-mode'] == 'right':
            self.entry_width=self.icon_width+self.menu_horizontal_padding+self.text_width
            self.entry_height=max(self.text_height,self.icon_height)
        elif self.show_params['menu-text-mode']=='below':
            self.entry_width=max(self.text_width,self.icon_width)
            self.entry_height=self.icon_height + self.menu_vertical_padding + self.text_height 
        else:
            # no text or overlaid text
            if self.show_params['menu-icon-mode'] in ('thumbnail','bullet'):
                # icon only
                self.entry_width=self.icon_width
                self.entry_height=self.icon_height
            else:
                #text only
                self.entry_width=self.text_width
                self.entry_height=self.text_height

        if self.entry_width<=self.menu_horizontal_padding:
            return 'error','entry width is zero'

        if self.entry_height<=self.menu_vertical_padding:
            return 'error','entry height is zero'

        # calculate totals for debugging puropses
        total_width=self.menu_columns * self.entry_width +(self.menu_columns-1)*self.x_separation
        total_height=self.menu_rows * self.entry_height + (self.menu_rows-1)*self.y_separation
        
        # self.print_geometry(total_width,total_height)   


        # display guidelines and debgging text if there is a problem     
        if total_width>self.menu_width and self.display_guidelines<>'never':
                self.display_guidelines='always'
                self.mon.log(self,'\nMENU IS WIDER THAN THE WINDOW')
                self.print_geometry(total_width,total_height)


        if total_height>self.menu_height and self.display_guidelines<>'never':
                self.display_guidelines='always'
                self.mon.log(self,'\nMENU IS TALLER THAN THE WINDOW')
                self.print_geometry(total_width,total_height)            

        # display calculated total rectangle guidelines for debugging
        if self.display_guidelines=='always':
            points=[self.menu_x_left,self.menu_y_top, self.menu_x_left+total_width,self.menu_y_top+total_height]

            # and display the icon rectangle
            self.canvas.create_rectangle(points,
                                           outline='red',
                                           fill='',
                                           tag='pp-content')

        
        # display menu rectangle guidelines for debugging
        if self.display_guidelines=='always':
            points=[self.menu_x_left,self.menu_y_top, self.menu_x_right,self.menu_y_bottom]
            self.canvas.create_rectangle(points,
                                           outline='blue',
                                           fill='',
                                           tag='pp-content')
                
        return 'normal',''

    def calculate_entry_position(self,column_index,row_index):
            self.entry_x=self.menu_x_left+ column_index*(self.x_separation+self.entry_width)
            self.entry_y=self.menu_y_top+ row_index*(self.y_separation+self.entry_height)

            
    def display_entry_strip(self):
        if self.display_strip=='yes':
            if self.direction=='vertical':
                    #display the strip
                    strip_points=[self.entry_x - self.strip_padding -1 ,
                                  self.entry_y - self.strip_padding - 1,
                                  self.entry_x+ self.entry_width + self.strip_padding - 1,
                                  self.entry_y+self.entry_height+ self.strip_padding - 1]
                    self.canvas.create_rectangle(strip_points,
                                                       outline='',
                                                        fill='gray',
                                                       stipple='gray12',                                 
                                                       tag='pp-content')

                    top_l_points=[self.entry_x - self.strip_padding,
                                  self.entry_y - self.strip_padding,
                                  self.entry_x + self.entry_width + self.strip_padding ,
                                  self.entry_y - self.strip_padding]
                    
                    self.canvas.create_line(top_l_points,
                                            fill='light gray',
                                            tag='pp-content')
                    
                    bottom_l_points=[self.entry_x - self.strip_padding,
                                     self.entry_y + self.entry_height + self.strip_padding,
                                     self.entry_x+ self.entry_width + self.strip_padding ,
                                     self.entry_y+ self.entry_height + self.strip_padding]
                    
                    self.canvas.create_line(bottom_l_points,
                                            fill='dark gray',
                                            tag='pp-content')

                    left_l_points=[self.entry_x - self.strip_padding,
                                   self.entry_y - self.strip_padding,
                                   self.entry_x - self.strip_padding,
                                   self.entry_y + self.entry_height + self.strip_padding]
                    
                    self.canvas.create_line(left_l_points,
                                            fill='gray',
                                            tag='pp-content')

            else:
                    #display the strip vertically
                    strip_points=[self.entry_x - self.strip_padding +1 ,
                                  self.entry_y - self.strip_padding +1,
                                  self.entry_x+self.entry_width + self.strip_padding -1,
                                  self.entry_y + self.entry_height+ self.strip_padding -1]
                    
                    self.canvas.create_rectangle(strip_points,
                                                       outline='',
                                                        fill='gray',
                                                       stipple='gray12',                                 
                                                       tag='pp-content')

                    top_l_points=[self.entry_x - self.strip_padding,
                                  self.entry_y - self.strip_padding,
                                  self.entry_x + self.entry_width + self.strip_padding,
                                  self.entry_y - self.strip_padding]
                    
                    self.canvas.create_line(top_l_points,
                                            fill='light gray',
                                            tag='pp-content')
                    
                    left_l_points=[self.entry_x - self.strip_padding,
                                   self.entry_y - self.strip_padding,
                                   self.entry_x - self.strip_padding,
                                   self.entry_y + self.entry_height+ self.strip_padding]
                    
                    self.canvas.create_line(left_l_points,
                                            fill='gray',
                                            tag='pp-content')

                    right_l_points=[self.entry_x +self.entry_width + self.strip_padding,
                                     self.entry_y - self.strip_padding,
                                     self.entry_x +self.entry_width + self.strip_padding,
                                     self.entry_y + self.entry_height+ self.strip_padding]
                    
                    self.canvas.create_line(right_l_points,
                                            fill='dark gray',
                                            tag='pp-content')


    # display the rectangle that goes arond the icon when the entry is selected
    def display_icon_rectangle(self):
            if self.show_params['menu-icon-mode'] in ('thumbnail','bullet'):

                #calculate icon parameters
                if self.icon_width<self.text_width and self.show_params['menu-text-mode']=='below':
                        self.icon_x_left=self.entry_x+abs(self.icon_width-self.text_width)/2
                else:
                        self.icon_x_left=self.entry_x
                self.icon_x_right=self.icon_x_left+self.icon_width

                if self.icon_height<self.text_height and self.show_params['menu-text-mode']=='right':
                        self.icon_y_top=self.entry_y+abs(self.icon_height-self.text_height)/2
                else:
                        self.icon_y_top=self.entry_y
                self.icon_y_bottom=self.icon_y_top+self.icon_height

                
                req_horiz_sep=self.menu_horizontal_padding
                req_vert_sep=self.menu_vertical_padding

                
                points=[self.icon_x_left,self.icon_y_top,self.icon_x_right,self.icon_y_top,self.icon_x_right,self.icon_y_bottom,self.icon_x_left,self.icon_y_bottom]

                # display guidelines make it white when not selctedfor debugging
                if self.display_guidelines=='always':
                    outline='white'
                else:
                    outline=''

                # and display the icon rectangle
                icon_id=self.canvas.create_polygon(points,
                                                   outline=outline,
                                                   fill='',
                                                   tag='pp-content')


            else:
                # not using icon so set starting point for text to zero icon size
                self.icon_x_right=self.entry_x
                self.icon_y_bottom=self.entry_y
                req_horiz_sep=0
                req_vert_sep=0
                icon_id=None
            return icon_id
        

    #display the image in a menu entry
    def  display_icon_image(self):
            image_id=None
            if self.show_params['menu-icon-mode'] == 'thumbnail':
                # try for the thumbnail
                if self.medialist.selected_track()['thumbnail']<>'' and os.path.exists(self.complete_path(self.medialist.selected_track()['thumbnail'])):
                    self.pil_image=PIL.Image.open(self.complete_path(self.medialist.selected_track()['thumbnail']))
                else:
                    #cannot find thumbnail get the image if its an image track
                    if self.medialist.selected_track()['type'] =='image':
                        self.track=self.complete_path(self.medialist.selected_track()['location'])
                    else:
                        self.track=''
                    if self.medialist.selected_track()['type']=='image' and os.path.exists(self.track)==True: 
                        self.pil_image=PIL.Image.open(self.track)
                    else:
                        #use a standard thumbnail
                        type=self.medialist.selected_track()['type']
                        standard=self.pp_dir+os.sep+'pp_home'+os.sep+'pp_resources'+os.sep+type+'.png'
                        if os.path.exists(standard)==True:
                            self.pil_image=PIL.Image.open(standard)
                            self.mon.log(self,'WARNING: default thumbnail used for '+self.medialist.selected_track()['title'])
                        else:
                            self.pil_image=None

                # display the image                
                if self.pil_image<>None:
                    self.pil_image=self.pil_image.resize((self.icon_width-2,self.icon_height-2))                 
                    image_id=PIL.ImageTk.PhotoImage(self.pil_image)
                    self.canvas.create_image(self.icon_x_left+1, self.icon_y_top+1,
                                                image=image_id, anchor=NW,
                                                 tag='pp-content')
                else:
                        image_id=None
                        
            elif self.show_params['menu-icon-mode'] =='bullet':
                    bullet=self.complete_path(self.show_params['menu-bullet'])                  
                    if os.path.exists(bullet)==False:
                        self.pil_image=None                          
                    else:
                        self.pil_image=PIL.Image.open(bullet)
                    if self.pil_image<>None:
                        self.pil_image=self.pil_image.resize((self.icon_width-2,self.icon_height-2))                 
                        image_id=PIL.ImageTk.PhotoImage(self.pil_image)
                        self.canvas.create_image(self.icon_x_left+1, self.icon_y_top+1,
                                                      image=image_id, anchor=NW,
                                                      tag='pp-content')                                      
            else:
                image_id=None
            return image_id

            
    #display the text of a menu entry
    def display_icon_text(self):
            text_mode=self.show_params['menu-text-mode']
            if self.show_params['menu-icon-mode'] in ('thumbnail','bullet'):
                if text_mode=='right':
                    if self.icon_height>self.text_height:
                        text_y_top=self.entry_y+abs(self.icon_height-self.text_height)/2
                    else:
                        text_y_top=self.entry_y
                    text_y_bottom=text_y_top+self.text_height
                    
                    text_x_left=self.icon_x_right+self.menu_horizontal_padding
                    text_x_right=text_x_left+self.text_width
                    
                    text_x=text_x_left
                    text_y=text_y_top+(self.text_height/2)

                elif text_mode=='below':
                    text_y_top=self.icon_y_bottom+self.menu_vertical_padding
                    text_y_bottom=text_y_top+self.text_height
                    
                    if self.icon_width>self.text_width:
                        text_x_left=self.entry_x+abs(self.icon_width-self.text_width)/2
                    else:
                        text_x_left=self.entry_x
                    text_x_right=text_x_left+self.text_width
                    
                    text_x=text_x_left+(self.text_width/2)
                    text_y=text_y_top

                else:
                    # icon with text_mode=overlay or none
                    text_x_left=self.icon_x_left
                    text_x_right= self.icon_x_right
                    text_y_top=self.icon_y_top
                    text_y_bottom=self.icon_y_bottom
                    text_x=(text_x_left+text_x_right)/2
                    text_y=(text_y_top+text_y_bottom)/2                    

            else:
                    #no icon text only
                    text_y_top=self.entry_y
                    text_y_bottom=text_y_top+self.text_height
                    text_x_left=self.entry_x
                    text_x_right=text_x_left+self.text_width
                    text_x=self.entry_x
                    text_y=self.entry_y+self.text_height/2


            #display the guidelines for debugging
            if self.display_guidelines=='always':
                points=[text_x_left,text_y_top,text_x_right,text_y_top,text_x_right,text_y_bottom,text_x_left,text_y_bottom]
                self.canvas.create_polygon(points,fill= '' ,
                                              outline='white',
                                              tag='pp-content')

            # display the text
            if text_mode=='below' and self.show_params['menu-icon-mode']  in ('thumbnail','bullet'):
                anchor=N
                justify=CENTER
            elif text_mode=='overlay' and self.show_params['menu-icon-mode']  in ('thumbnail','bullet'):
                anchor=CENTER
                justify=CENTER
            else:
                anchor=W
                justify=LEFT
            text_id=self.canvas.create_text(text_x,text_y,
                                       text=self.medialist.selected_track()['title'],
                                       anchor=anchor,
                                       fill=self.show_params['entry-colour'],
                                       font=self.show_params['entry-font'],
                                       width=self.text_width,
                                       justify=justify,
                                       tag='pp-content')
            return text_id
        

    def highlight_menu_entry(self,index,state):
        if self.show_params['menu-icon-mode']<>'none':
            if state==True:
                self.canvas.itemconfig(self.menu_entry_id[index][self.icon_id_index],
                                       outline=self.show_params['entry-select-colour'],
                                       width=4,
                                       )
            else:
                self.canvas.itemconfig(self.menu_entry_id[index][self.icon_id_index],
                                        outline='',
                                       width=1
                                       )
        else:
            if state==True:
                self.canvas.itemconfig(self.menu_entry_id[index][self.text_id_index],
                                       fill=self.show_params['entry-select-colour'])
            else:
                self.canvas.itemconfig(self.menu_entry_id[index][self.text_id_index],
                                    fill=self.show_params['entry-colour'])
                

    
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

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file<>'' and track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        return track_file     

    def parse_menu_window(self,line):
            if line<>'':
                fields = line.split()
                if len(fields) not in  (1, 2,4):
                    return 'error','wrong number of fields',0,0,0,0
                if len(fields)==1:
                    if fields[0]=='fullscreen':
                        return 'normal','',0,0,self.screen_width - 1, self.screen_height - 1
                    else:
                        return 'error','single field is not fullscreen',0,0,0,0
                if len(fields)==2:                    
                    if fields[0].isdigit() and fields[1].isdigit():
                        return 'normal','',int(fields[0]),int(fields[1]),self.screen_width, self.screen_height
                    else:
                        return 'error','field is not a digit',0,0,0,0
                if len(fields)==4:                    
                    if fields[0].isdigit() and fields[1].isdigit() and fields[2].isdigit() and fields[3].isdigit():
                        return 'normal','',int(fields[0]),int(fields[1]),int(fields[2]),int(fields[3])
                else:
                     return 'error','field is not a digit',0,0,0,0
            else:
                     return 'error','line is blank',0,0,0,0


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
