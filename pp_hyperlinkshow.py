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
from pp_messageplayer import MessagePlayer
from pp_resourcereader import ResourceReader
from pp_pathmanager import PathManager
from pp_controlsmanager import ControlsManager
from pp_utils import Monitor


class HyperlinkShow:
    """
        Aimed at touchscreens but can be used for any purpose where the user is required to follow hyperlinks between tracks
        Profiles for media tracks (message, image, video, audio ) specify links to other tracks
        in a link a symbolic name of an input is associated with a track-reference
        The show begins at first-track and then uses events (GPIO, keypresses etc.) to link to other tracks via their symbolic names
        If using 'call' keeps a record of the tracks it has visited so the 'return' command can go back.
        Executes timeout-track if no user input is received.

        links are of the form:
           symbolic-name command [track-ref]
        
        link commands:
          call <track-ref> play track-ref and add it to the path
          return - return 1 back up the path removing the track from the path, stops at home-track.
          return n - return n tracks back up the path removing the track from the path, stops at home-track.
          return <track-ref> return to <track-ref> removing tracks from the path
          home  - return to home-track removing tracks from the path
          jump <track-ref-> - play trck-ref forgetting the path back to home-track
          goto <track-ref> - play track-ref, forget the path 
          exit - end the hyperlink show
          null - inhibits the link defined in the show with the same symbolic name.

          reserved symbolic names
          pp-onend command  - pseudo symbolic name for end of a track

        interface:
         * play - selects the first track to play (first-track) 
         * input_pressed,  - receives user events passes them to a Shower/Player if a track is playing,
                otherwise actions them depending on the symbolic name supplied
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
        """ canvas - the canvas that the tracks of the event show are to be written on
            show_params - the name of the configuration dictionary section for the hyperlinkshow
            showlist  - the showlist, to enable runningnof show type tracks.
            pp_home - Pi presents data_home directory
            pp_profile - Pi presents profile directory
        """
        
        self.mon=Monitor()
        self.mon.on()
        
        #instantiate arguments
        self.show_params=show_params
        self.root=root
        self.showlist=showlist
        self.canvas=canvas
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile

        # open resources
        self.rr=ResourceReader()

        #create a path stack
        self.path = PathManager()
        
        # init variables
        self.drawn  = None
        self.player=None
        self.shower=None
        self.timeout_running=None
        self.error=False



    def play(self,show_id,end_callback,ready_callback,top=False,command='nil'):
        """ starts the hyperlink show at start-track 
              end_callback - function to be called when the show exits
              ready_callback - callback when event-show is ready to display its forst track (not used?)
              top is True when the show is top level (run from [start] or from show control)
              command is not used
        """
        
        #instantiate arguments
        self.show_id=show_id
        self.end_callback=end_callback
        self.ready_callback=ready_callback
        self.top=top
        self.command=command

        # check data files are available.
        self.medialist_file = self.pp_profile + "/" + self.show_params['medialist']
        if not os.path.exists(self.medialist_file):
            self.mon.err(self,"Medialist file not found: "+ self.medialist_file)
            self.end('error',"Medialist file not found")
        
        #create a medialist object for the hyperlinkshow and read the file into it.
        self.medialist=MediaList()
        if self.medialist.open_list(self.medialist_file,self.showlist.sissue()) == False:
            self.mon.err(self,"Version of medialist different to Pi Presents")
            self.end('error',"Version of medialist different to Pi Presents")

        #get controls for this show if top level
        controlsmanager=ControlsManager()
        if self.top==True:
            self.controls_list=controlsmanager.default_controls()
            # and merge in controls from profile
            self.controls_list=controlsmanager.merge_show_controls(self.controls_list,self.show_params['controls'])

        
        # read show  links and destinations
        self.first_track_ref=self.show_params['first-track-ref']
        self.home_track_ref=self.show_params['home-track-ref']
        self.timeout_track_ref=self.show_params['timeout-track-ref']
        

    # state variables and signals   
        self.end_hyperlinkshow_signal= False
        self.egg_timer=None
        self.next_track_signal=False
        self.next_track_ref=''
        self.current_track_ref=''
        self.current_track_type=''

        # ready callback for show
        if self.ready_callback<>None:
            self.ready_callback()
                    
        self.canvas.delete('pp-content')
        self.canvas.config(bg='black')
        
        self.do_first_track()

        
#stop received from another concurrent show via ShowManager

    def managed_stop(self):
            # set signal to stop the hyperlinkshow when all  sub-shows and players have ended
            self.end_hyperlinkshow_signal=True
            # then stop and shows or tracks.
            if self.shower<>None:
                self.shower.managed_stop()
            elif self.player<>None:
                self.player.input_pressed('stop')
            else:
                self.end('normal','stopped by ShowManager')
                
  
       
    # kill or error
    def terminate(self,reason):
        self.end_hyperlinkshow_signal=True
        if self.shower<>None:
            self.shower.terminate(reason)
        elif self.player<>None:
            self.player.terminate(reason)
        else:
            self.end(reason,'terminated without terminating shower or player')

          

   # respond to inputs
    def input_pressed(self,symbol,edge,source):

        self.mon.log(self,"received symbol: " + symbol)
        
        #does the symbol match a link, if so execute it
        if self.is_link(symbol,edge,source)==True:
            return
        
        # controls are disabled so ignore anything else
        if self.show_params['disable-controls']=='yes':
            return

        # does it match a control       
        # if at top convert symbolic name to operation otherwise lower down we have received an operatio    
        # look through list of controls to find match
        if self.top==True:
            operation=self.lookup_control(symbol,self.controls_list)
        else:
            operation=symbol
        # print 'operation',operation 
        if operation<>'':
            self.do_operation(operation,edge,source)



    def do_operation(self,operation,edge,source):
        if self.shower<>None:
            # if next lower show is running pass down to stop the show and lower level
            self.shower.input_pressed(operation,edge,source) 
        else:        
            # control this show and its tracks
            if operation=='stop':
                if self.player<>None:
                    if self.current_track_ref==self.first_track_ref and self.top==False:
                        self.end_radiobuttonshow_signal=True
                    self.player.input_pressed('stop')

            elif operation == 'pause':
                if self.player<>None:
                    self.player.input_pressed(operation)

            elif operation[0:4]=='omx-' or operation[0:6]=='mplay-'or operation[0:5]=='uzbl-':
                if self.player<>None:
                    self.player.input_pressed(operation)

   
    def is_link(self,symbol,edge,source):
        # find the first entry in links that matches the symbol and execute its operation
        # print 'hyperlinkshow ',symbol
        found=False
        for link in self.links:
            #print link
            if symbol==link[0]:
                found=True
                if link[1]<>'null':
                    # print 'match',link[0]
                    link_operation=link[1]
                    if link_operation=='home':
                        self.do_home(edge,source)
                    elif link_operation =='return':
                        self.do_return(link[2],edge,source)
                    elif link_operation =='call':
                        self.do_call(link[2],edge,source)
                    elif link_operation =='goto':
                        self.do_goto(link[2],edge,source)
                    elif link_operation =='jump':
                        self.do_jump(link[2],edge,source)
                    elif link_operation=='exit':
                        self.end('normal','executed exit command')
        return found


    def lookup_control(self,symbol,controls_list):
        for control in controls_list:
            if symbol == control[0]:
                return control[1]
        return ''

# *********************
# INTERNAL FUNCTIONS
# ********************

# *********************
# Show Sequencer
# *********************


    def timeout_callback(self):
        self.do_call(self.timeout_track_ref,'front','timeout')

    def do_call(self,track_ref,edge,source):
        if track_ref<>self.current_track_ref:
            self.mon.log(self, 'call: '+track_ref)
            self.next_track_signal=True
            self.next_track_op='call'
            self.next_track_arg=track_ref
            if self.shower<>None:
                self.shower.input_pressed('stop',edge,source)
            elif self.player<>None:
                self.player.input_pressed('stop')
            else:
                self.what_next()


    def do_goto(self,to,edge,source):
        if to<>self.current_track_ref:
            self.mon.log(self,'goto: '+to)
            self.next_track_signal=True
            self.next_track_op='goto'
            self.next_track_arg=to
            if self.shower<>None:
                self.shower.input_pressed('stop',edge,source)
            elif self.player<>None:
                self.player.input_pressed('stop')
            else:
                self.what_next()

    def do_jump(self,to,edge,source):
        if to<>self.current_track_ref:
            self.mon.log(self,'jump to: '+to)
            self.next_track_signal=True
            self.next_track_op='jump'
            self.next_track_arg=to
            if self.shower<>None:
                self.shower.input_pressed('stop',edge,source)
            elif self.player<>None:
                self.player.input_pressed('stop')
            else:
                self.what_next()
        
    def do_return(self,to,edge,source):
        self.next_track_signal=True
        if to.isdigit() or to=='':
            self.mon.log(self,'hyperlink command - return by: '+to)
            self.next_track_op='return-by'
            if to == '':
                self.next_track_arg='1'
            else:    
                self.next_track_arg=to
        else:
            self.mon.log(self,'hyperlink command - return to: '+to)
            self.next_track_op='return-to'
            self.next_track_arg=to        
        if self.shower<>None:
            self.shower.input_pressed('stop',edge,source)
        elif self.player<>None:
            self.player.input_pressed('stop')
        else:
            self.what_next()
        
    def do_home(self,edge,source):
        if self.current_track_ref<>self.home_track_ref:
            self.mon.log(self,'hyperlink command - home')
            self.next_track_signal=True
            self.next_track_op='home'
            if self.shower<>None:
                self.shower.input_pressed('stop',edge,source)
            elif self.player<>None:
                self.player.input_pressed('stop')
            else:
                self.what_next()


    def do_first_track(self):
        index = self.medialist.index_of_track(self.first_track_ref)
        if index >=0:
            #don't use select the track as not using selected_track in hyperlinkshow
            first_track=self.medialist.track(index)
            self.current_track_ref=first_track['track-ref']
            self.path.append(first_track['track-ref'])
            self.play_selected_track(first_track)
        else:
            self.mon.err(self,"first-track not found in medialist: "+ self.show_params['first-track-ref'])
            self.end('error',"first track not found in medialist")

            

    
    def what_next(self):
        # user wants to end the show 
        if self.end_hyperlinkshow_signal==True:
            self.end_hyperlinkshow_signal=False
            self.end('normal',"show ended by user")

        # user has selected another track
        elif self.next_track_signal==True:
                self.next_track_signal=False

                # home
                if self.next_track_op in ('home'):
                    # back to 1 before home
                    back_ref=self.path.back_to(self.home_track_ref)
                    if back_ref=='':
                        self.mon.err(self,"home - home track not in path: "+self.home_track_ref)
                        self.end('error',"home - home track not in path")
                    # play home
                    self.next_track_ref=self.home_track_ref
                    self.path.append(self.next_track_ref)

                # return-by
                elif self.next_track_op in ('return-by'):
                    if self.current_track_ref<>self.home_track_ref:
                        # back n stopping at home
                        # back one more and return it
                        back_ref=self.path.back_by(self.home_track_ref,self.next_track_arg)
                        # use returned track
                        self.next_track_ref=back_ref
                        self.path.append(self.next_track_ref)

                # return-to
                elif self.next_track_op in ('return-to'):
                    #back to one before return-to track
                    back_ref=self.path.back_to(self.next_track_arg)
                    if back_ref=='':
                        self.mon.err(self,"return-to - track not in path: "+self.next_track_arg)
                        self.end('error',"return-to - track not in path")
                    # and append the return to track
                    self.next_track_ref=self.next_track_arg
                    self.path.append(self.next_track_ref)
                    
                # call
                elif self.next_track_op in ('call'):
                    # append the required track
                    self.path.append(self.next_track_arg)
                    self.next_track_ref=self.next_track_arg

                # goto
                elif self.next_track_op in ('goto'):
                    self.path.pop_for_sibling()
##                    #back to first track and remove it
##                    back_ref=self.path.back_to(self.first_track_ref)
##                    if back_ref=='':
##                        self.mon.err(self,"goto - first track not in path: "+self.first_track_ref)
##                        self.end('error',"goto - first track not in path")
                   #add the goto track
                    self.next_track_ref=self.next_track_arg
                    self.path.append(self.next_track_arg)

                # jump
                elif self.next_track_op in ('jump'):
                    # back to home and remove it
                    back_ref=self.path.back_to(self.home_track_ref)
                    if back_ref=='':
                        self.mon.err(self,"jump - home track not in path: "+self.home_track_ref)
                        self.end('error',"jump - track not in path")
                    # add back the home track without playing it
                    self.path.append(self.home_track_ref)
                    # append the jumped to track
                    self.next_track_ref=self.next_track_arg
                    self.path.append(self.next_track_ref)

                else:
                    self.mon.err(self,"unaddressed what next: "+ self.next_track_op+ ' '+self.next_track_arg)
                    self.end('error',"unaddressed what next")
                
                self.current_track_ref=self.next_track_ref                    
                index = self.medialist.index_of_track(self.next_track_ref)
                if index >=0:
                    #don't use select the track as not using selected_track in hyperlinkshow
                    next_track=self.medialist.track(index)
                    self.play_selected_track(next_track)
                else:
                    self.mon.err(self,"next-track not found in medialist: "+ self.next_track_ref)
                    self.end('error',"next track not found in medialist")
                    
        else:
            #track ends naturally
            #then input pp-onend symbolic name
            self.input_pressed('pp-onend','front','key')
        




# *********************
# Dispatching to Players
# *********************


    def page_callback(self):
        # called from a Player when ready to play, merge the links from the track with those from the show
        # and then enable the click areas
        self.delete_eggtimer()
        links_text=self.player.get_links()
        reason,message,track_links=self.path.parse_links(links_text)
        if reason=='error':
            self.mon.err(self,message + " in page")
            self.end('error',message)
        self.path.merge_links(self.links,track_links)

        # enable the click-area that are in the list of links
        self.enable_click_areas()


    
    def enable_click_areas(self):
        for link in self.links:
            #print 'trying link ',link[0] 
            if not('key-' in link[0]) and link[1]<>'null' and link[0]<>'pp-auto':
                # print 'enabling link ',link[0]
                self.canvas.itemconfig(link[0],state='normal')

                
    def play_selected_track(self,selected_track):
        """ selects the appropriate player from type field of the medialist and computes
              the parameters for that type
              selected track is a dictionary for the track/show
        """     

        if self.timeout_running<>None:
            self.canvas.after_cancel(self.timeout_running)
            self.timeout_running=None
            
        # self.canvas.delete(ALL)
        self.display_eggtimer(self.resource('hyperlinkshow','m01'))

        self.current_track_type = selected_track['type']
        
        #read the show links. Track links will be added by ready_callback
        links_text=self.show_params['links']
        reason,message,self.links=self.path.parse_links(links_text)
        if reason=='error':
            self.mon.err(self,message + " in show")
            self.end('error',message)

        #start timeout for the track if required           
             
        if self.current_track_ref<>self.first_track_ref and int(self.show_params['timeout'])<>0:
            self.timeout_running=self.canvas.after(int(self.show_params['timeout'])*1000,self.timeout_callback)
        

        # dispatch track by type
        self.player=None
        self.shower=None
        track_type = selected_track['type']
        self.mon.log(self,"Track type is: "+ track_type)
        
        if track_type=="video":
            # create a videoplayer
            track_file=self.complete_path(selected_track)
            self.player=VideoPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.page_callback,
                                        enable_menu=False)
                                        
        elif track_type=="audio":
            # create a audioplayer
            track_file=self.complete_path(selected_track)
            self.player=AudioPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.page_callback,
                                        enable_menu=False)
                                        
        elif track_type=="image":
            track_file=self.complete_path(selected_track)
            self.player=ImagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                    self.showlist,
                                    self.end_player,
                                    self.page_callback,
                                    enable_menu=False,
                                    )

        elif track_type=="web":
            # create a browser
            track_file=self.complete_path(selected_track)
            self.player=BrowserPlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(track_file,
                                        self.showlist,
                                        self.end_player,
                                        self.page_callback,
                                        enable_menu=False)
                                    
                         
        elif track_type=="message":
            # bit odd because MessagePlayer is used internally to display text. 
            text=selected_track['text']
            self.player=MessagePlayer(self.show_id,self.root,self.canvas,self.show_params,selected_track,self.pp_dir,self.pp_home,self.pp_profile)
            self.player.play(text,
                                    self.showlist,
                                    self.end_player,
                                    self.page_callback,
                                    enable_menu=False
                                    )
 
        elif track_type=="show":
            self.enable_click_areas()
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
                self.shower.play(self.show_id,self.end_shower,self.ready_callback,top=False,command='nil')

            elif selected_show['type']=="liveshow":    
                self.shower= LiveShow(selected_show,
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
                                                               self.root,
                                                                self.canvas,
                                                                self.showlist,
                                                               self,pp_dir,
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
        # this does not seem to change the colour of the polygon
        self.canvas.itemconfig('pp-click-area',state='hidden')
        self.canvas.update_idletasks( )
        if reason in("killed","error"):
            self.end(reason,message)
        else:
            self.display_eggtimer(self.resource('hyperlinkshow','m02'))
            self.what_next()

    # callback from when shower ends
    def end_shower(self,show_id,reason,message):
        self.mon.log(self,"Returned from shower with message: "+ message)
        self.shower=None
        self.canvas.itemconfig('pp-click-area',state='hidden')
        self.canvas.update_idletasks( )
        if reason in ("killed","error"):
            self.end(reason,message)
        else:
            self.display_eggtimer(self.resource('hyperlinkshow','m03'))
            self.what_next()  


# *********************
# End the show
# *********************
    # finish the player for killing, error or normally
    # this may be called directly sub/child shows or players are not running
    # if they might be running then need to call terminate.

    def end(self,reason,message):
        self.mon.log(self,"Ending hyperlinkshow: "+ self.show_params['show-ref'])  
        self.end_callback(self.show_id,reason,message)
        self=None
        return




# *********************
# displaying things
# *********************

    def display_eggtimer(self,text):
        #self.egg_timer=self.canvas.create_text(int(self.canvas['width'])/2,
                                              #int(self.canvas['height'])/2,
                                                  #text= text,
                                                # fill='white',
                                               # font="Helvetica 20 bold")
        #self.canvas.update_idletasks( )
        pass


    def delete_eggtimer(self):
        if self.egg_timer!=None:
            self.canvas.delete(self.egg_timer)

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
            # players or showers may be running so need terminate
            self.terminate("error")
        else:
            return value
        
        
from pp_mediashow import MediaShow
from pp_liveshow import LiveShow
from pp_radiobuttonshow import RadioButtonShow
from pp_menushow import MenuShow





