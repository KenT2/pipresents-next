from Tkinter import *
import Tkinter as tk
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
import tkFont
import os
import json


class Validator:

    def validate_profile(self, root, pp_dir, pp_home, pp_profile,editor_issue,display):

        # USES
        # self.current_showlist

        # CREATES
        # v_media_lists - file names of all medialists in the profile
        # v_shows
        # v_track_labels - list of track labels in current medialist.
        # v_show_labels - list of show labels in the showlist
        # v_medialist_refs - list of references to medialist files in the showlist

            # open results display
            self.result=ResultWindow(root,"Validate "+pp_profile,display)
            self.result.display('t',"\nVALIDATING PROFILE '"+ pp_profile + "'")

            if not  os.path.exists(pp_profile+os.sep+"pp_showlist.json"):
                self.result.display('f',"pp_showlist.json not in profile")
                self.result.display('t', "Validation Aborted")
                return False                   
            ifile  = open(pp_profile+os.sep+"pp_showlist.json", 'rb')
            sdict= json.load(ifile)
            ifile.close()
            v_shows=sdict['shows']
            if 'issue' in sdict:
                profile_issue= sdict['issue']
            else:
                profile_issue="1.0"
                          
            if profile_issue <> editor_issue:
                self.result.display('f',"Profile version "+profile_issue+ " is different to that editor")
                self.result.display('t', "Validation Aborted")
                return False                                            
            
            # read the gpio config
            # gpio_cfg_ok=read_gpio_cfg(pp_dir,pp_home,pp_profile)
                
                
            # MAKE LIST OF SHOW LABELS
            v_show_labels=[]
            for show in v_shows:
                if show['type']<>'start': v_show_labels.append(show['show-ref'])

            # CHECK ALL MEDIALISTS AND THEIR TRACKS
            v_media_lists = []
            for file in os.listdir(pp_profile):
                if not file.endswith(".json") and file<>'gpio.cfg':
                    self.result.display('f',"Invalid medialist in profile: "+ file)
                    self.result.display('t', "Validation Aborted")
                    return False
                    
                if file.endswith(".json") and file<>'pp_showlist.json':
                    self.result.display('t',"\nChecking medialist '"+file+"'")
                    v_media_lists.append(file)

                    #open a medialist and test its tracks
                    ifile  = open(pp_profile + os.sep + file, 'rb')
                    sdict= json.load(ifile)
                    ifile.close()                          
                    tracks = sdict['tracks']
                    if 'issue' in sdict:
                        medialist_issue= sdict['issue']
                    else:
                        medialist_issue="1.0"
                          
                    # check issue of medialist      
                    if medialist_issue <> editor_issue:
                        self.result.display('f',"Medialist version "+medialist_issue+ " is different to that editor")
                        self.result.display('t', "Validation Aborted")
                        return False

                    #open a medialist and test its tracks
                    v_track_labels=[]
                    anonymous=0
                    for track in tracks:
                        self.result.display('t',"    Checking track '"+track['title']+"'")
                        # check track-ref
                        if track['track-ref'] not in ('','pp-menu-background','pp-child-show'):self.result.display('f',"invalid track-ref")
                        if track['track-ref']=='':
                            anonymous+=1
                        else:
                            v_track_labels.append(track['track-ref'])
                            if track['track-ref']=='pp-child-show' and track['type']<>'show': self.result.display('f',"pp-child-show track is not a show")
                            if track['track-ref']=='pp-menu-background' and track['type']<>'menu-background': self.result.display('f',"pp-menu-background track is not a 'menu-background'")
                        
                        # check media tracks not blank where mandatory
                        if track['type'] in ('video','menu-background'):
                            if track['location'].strip()=='':
                                self.result.display('f',"blank location")

                        # warn if media tracks blank  where optional
                        if track['type'] in ('audio','image'):
                            if track['location'].strip()=='':
                                self.result.display('w',"blank location")
                        
                        # check location of relative media tracks where present                   
                        if track['type'] in ('video','audio','image','menu-background'):    
                            track_file=track['location']
                            if track['location'].strip()<>'' and  track_file[0]=="+":
                                    track_file=pp_home+track_file[1:]
                                    if not os.path.exists(track_file): self.result.display('f',"location "+track['location']+ " media file not found")
                                                  
                        # Check simple fields                        
                        if track['type']=="image":
                            if track['duration']<>"" and not track['duration'].isdigit(): self.result.display('f',"'duration' is not blank, 0 or a positive integer")
                            if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")

                        if track['type']=="video":
                           if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")

                                
                                
                        if track['type']=="audio":
                            if not track['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                            if track['track-text']<>"":
                                if not track['track-text-x'].isdigit(): self.result.display('f',"'track-text-x' is not 0 or a positive integer")
                                if not track['track-text-y'].isdigit(): self.result.display('f',"'track-text-y' is not 0 or a positive integer")
                            if track['background-image']<>'':
                                track_file=track['background-image']
                                if track_file[0]=="+":
                                    track_file=pp_home+track_file[1:]
                                    if not os.path.exists(track_file): self.result.display('f',"location "+track['location']+ " background image file not found")                                
                                
                        if track['type']=="message":
                            if track['duration']<>"" and not track['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                            if track['background-image']<>'':
                                track_file=track['background-image']
                                if track_file[0]=="+":
                                    track_file=pp_home+track_file[1:]
                                    if not os.path.exists(track_file): self.result.display('f',"location "+track['location']+ " background image file not found")                                

                        if track['type']=='control':
                                self.check_animate('animate-begin',track['animate-begin'])
                                self.check_show_control(track['show-control'],v_show_labels)
   
                        # check animation fields
                        if track['type']in("image",'audio','video'):
                            self.check_animate('animate-begin',track['animate-begin'])
                            self.check_animate('animate-end',track['animate-end'])
                        
                        # CHECK CROSS REF TRACK TO SHOW
                        if track['type'] == 'show':
                                if track['sub-show']=="":
                                    self.result.display('f',"No 'Show to Run'")
                                else:
                                    if track['sub-show'] not in v_show_labels: self.result.display('f',"show "+track['sub-show'] + " does not exist")
                                
                    if anonymous == 0 :self.result.display('w',"zero anonymous tracks in medialist " + file)

                    # check for duplicate track-labels
                    if v_track_labels.count('pp-menu-background') >1: self.result.display('f', "more than one pp-menu-background")
                    if v_track_labels.count('pp-child-show') >1: self.result.display('f', "more than one pp-child-show")

            # SHOWS
            # find start show and test it, test show-refs at the same time
            found=0
            for show in v_shows:
                if show['type']=='start':
                    self.result.display('t',"\nChecking show '"+show['title'] + "' first pass")
                    found+=1
                    if show['show-ref']<> 'start': self.result.display('f',"start show has incorrect label")
                else:
                    self.result.display('t',"Checking show '"+show['title'] + "' first pass")
                    if show['show-ref']=='': self.result.display('f',"show-ref is blank")
                    if ' ' in show['show-ref']: self.result.display('f',"Spaces not allowed in show-ref " + show['show-ref'])
                    
            if found == 0:self.result.display('f',"There is no start show")
            if found > 1:self.result.display('f',"There is more than 1 start show")    


            # check for duplicate show-labels
            for show_label in v_show_labels:
                found = 0
                for show in v_shows:
                    if show['show-ref']==show_label: found+=1
                if found > 1: self.result.display('f',show_label + " is defined more than once")
                
            # check other things about all the shows and create a list of medialist file references
            v_medialist_refs=[]
            for show in v_shows:
                if show['type']=="start":
                    self.result.display('t',"\nChecking show '"+show['title']+ "' second pass" )
                    self.check_start_shows(show,v_show_labels)               
                else:
                    self.result.display('t',"Checking show '"+show['title']+ "' second pass" )

                    # Validate simple fields of show
                    if show['type']=="mediashow":
                            if not show['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")
                            if show['has-child']=='yes':
                                if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")
                            if show['repeat']=='interval' and not show['repeat-interval'].isdigit(): self.result.display('f',"'repeat-interval' is not 0 or a positive integer")
                            if show['show-text']<>"":
                                if not show['show-text-x'].isdigit(): self.result.display('f',"'show-text-x' is not 0 or a positive integer")
                                if not show['show-text-y'].isdigit(): self.result.display('f',"'show-text-y' is not 0 or a positive integer")
                            if show['trigger']=='GPIO':
                                self.check_triggers('trigger',show['trigger-input'])
                            elif show['trigger']=='time':
                                self.check_times(show['trigger-input'])
                            if show['trigger-next']=='GPIO':
                                self.check_triggers('next',show['next-input'])
                            if show['trigger-end']=='time':
                                self.check_times(show['trigger-end-time'])
                            if show['trigger-end']=='duration':
                                self.check_end_duration(show['trigger-end-time'])                               
                                
                    if show['type']=="menu":
                            if not show['timeout'].isdigit(): self.result.display('f',"'timeout' is not 0 or a positive integer")
                            if not show['menu-x'].isdigit(): self.result.display('f',"'menu-x' is not 0 or a positive integer")
                            if not show['menu-y'].isdigit(): self.result.display('f',"'menu-y' is not 0 or a positive integer")
                            if not show['menu-spacing'].isdigit(): self.result.display('f',"'menu-spacing' is not 0 or a positive integer")
                            if not show['duration'].isdigit(): self.result.display('f',"'duration' is not 0 or a positive integer")                            
                            if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")


                    if show['type']=="liveshow":
                            if show['has-child']=='yes':
                                if not show['hint-y'].isdigit(): self.result.display('f',"'hint-y' is not 0 or a positive integer")
                            if show['show-text']<>"":
                                if not show['show-text-x'].isdigit(): self.result.display('f',"'show-text-x' is not 0 or a positive integer")
                                if not show['show-text-y'].isdigit(): self.result.display('f',"'show-text-y' is not 0 or a positive integer")
                            if show['trigger-start']=='time':
                                self.check_times(show['trigger-start-time'])
                            if show['trigger-end']=='time':
                                self.check_times(show['trigger-end-time'])
                            if show['trigger-end']=='duration':
                                self.check_end_duration(show['trigger-end-time'])                            
                                
                    if '.json' not in show['medialist']:
                        self.result.display('f', show['show-ref']+ " show has invalid medialist")
                        self.result.display('t', "Validation Aborted")
                        return False
                    elif show['medialist'] not in v_media_lists:
                        self.result.display('f', "'"+show['medialist']+ "' medialist not found")
                        self.result.display('t', "Validation Aborted")
                        return False
                    else:
                        if not os.path.exists(pp_profile + os.sep + show['medialist']):
                            self.result.display('f', "'"+show['medialist']+ "' medialist file does not exist")
                            self.result.display('t', "Validation Aborted")
                            return False
                    v_medialist_refs.append(show['medialist'])

        
               # CHECK CROSS REF SHOW TO TRACK
                    ifile  = open(pp_profile + os.sep + show['medialist'], 'rb')
                    tracks = json.load(ifile)['tracks']
                    ifile.close()
                    
                     # make a list of the track labels
                    v_track_labels=[]
                    for track in tracks:
                        if track['track-ref'] in ('pp-menu-background','pp-child-show'):
                            v_track_labels.append(track['track-ref'])
                            
                    if show['type']in('mediashow','liveshow') and show['has-child']=='yes':
                        if 'pp-child-show' not in v_track_labels: self.result.display('f'," pp-child-show track missing in medialist "+show['medialist'])
                    if show['type']=='menu' and show['has-background']=='yes':
                         if 'pp-menu-background' not in v_track_labels: self.result.display('f', " pp-menu-background track missing in medialist "+show['medialist'])

            self.result.display('t', "\nValidation Complete")
            self.result.stats()
            if self.result.num_errors() == 0:
                return True
            else:
                return False
 
 
    def check_start_shows(self,show,v_show_labels):
        text=show['start-show']
        show_count=0
        fields = text.split()
        for field in fields:
                show_count+=1
                if field not in v_show_labels:
                    self.result.display('f',"start show has undefined start-show: "+ field)
        if show_count==0:
            self.result.display('f',"start show has zero start-shows")

    def check_triggers(self,field,line):
        words=line.split()
        if len(words)!=1: self.result.display('f','Wrong number of fields in: ' + field + ", " + line)

# ***********************************
# time of day inputs
# ************************************ 

    def check_times(self,text):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_times_line(line)
            
    def check_times_line(self,line):
        items = line.split()
        if len(items)==0: self.result.display('w','No time values when using time of day trigger: ')
        for item in items:
            self.check_times_item(item)

    def check_times_item(self,item):
        if item[0]=='+':
            if not item.lstrip('+').isdigit():
                self.result.display('f','Value of relative time is not positive integer: ' + item)
                return
        else:
            #hh:mm;ss
            fields=item.split(':')
            if len(fields)==0:
                return
            if len(fields)==1:
                 self.result.display('f','Too few fields in time: ' + item)
                 return
            if len(fields)>3:
                 self.result.display('f','Too many fields in time: ' + item)
                 return
            if len(fields)<>3:
                seconds='0'
            else:
                seconds=fields[2]
            if not fields[0].isdigit() or not  fields[1].isdigit() or  not seconds.isdigit():
                self.result.display('f','Fields of time are not positive integers: ' + item)
                return        
            if int(fields[0])>23 or int(fields[1])>59 or int(seconds)>59:
             self.result.display('f','Fields of time are out of range: ' + item)
             return
             
    def check_end_duration(self,line):          
        fields=line.split(':')
        if len(fields)==0:
            self.result.display('f','End Trigger, Duration: Field is empty: ' + line)
            return
        if len(fields)>3:
            self.result.display('f','End Trigger, Duration: More then 3 fields: ' + line)
            return
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
        if not hours.isdigit() or not  minutes.isdigit() or  not secs.isdigit():
            self.result.display('f','End Trigger, Duration: Fields are not positive integers: ' + line)
            return
        
        if int(hours)>23 or int(minutes)>59 or int(secs)>59:
             self.result.display('f','End Trigger, Duration: Fields are out of range: ' + line)
             return


    def check_show_control(self,text,v_show_labels):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_show_control_fields(line,v_show_labels)

    def check_show_control_fields(self,line,v_show_labels):
        fields = line.split()
        if len(fields)==0: return

        if len(fields)<>2:
            self.result.display('f','Incorrect number of fields in: ' + line)
            return

        if fields[0] not in v_show_labels:
                self.result.display('f',"cannot find show reference: "+ fields[0])
        
        if fields[1] not in ('start','stop'):
            self.result.display('f','Incorrect command in: ' + line)
            return
            
# ***********************************
# checking show animation
# ************************************ 

    def check_animate_fields(self,field,line):
        fields= line.split()
        if len(fields)==0: return
            
        if len(fields)>3: self.result.display('f','Too many fields in: ' + field + ", " + line)

        if len(fields)<2:
            self.result.display('f','Too few fields in: ' + field + ", " + line)
            return
        
        name = fields[0]
        # name not checked - done at runtime
        
        to_state_text=fields[1]
        if not (to_state_text  in ('on','off')): self.result.display('f','Illegal to-state in: ' + field + ", " + line)
        
        if len(fields)==2:
            delay_text='0'
        else:
            delay_text=fields[2]
        
        if  not delay_text.isdigit(): self.result.display('f','Delay is not 0 or a positive integer in:' + field + ", " + line)

        return
    

    
    def check_animate(self,field,text):
        lines = text.split("\n")
        for line in lines:
            error_text=self.check_animate_fields(field,line)

            

    
    def read_gpio_cfg(self,pp_dir,pp_home):
        tryfile=self.pp_home+os.sep+"gpio.cfg"
        if os.path.exists(tryfile):
             filename=tryfile
        else:
            self.result.display('t', "gpio.cfg not found in pp_home")
            tryfile=self.pp_dir+os.sep+'pp_home'+os.sep+"gpio.cfg"
            if os.path.exists(tryfile):
                filename=tryfile
            else:
                self.result.display('w', "gpio.cfg not found in pipresents/pp_home - GPIO checking turned off")
                return False
        self.config = ConfigParser.ConfigParser()
        self.config.read(filename)
        return True

        
    def get(self,section,item):
        if self.config.has_option(section,item)==False:
            return False
        else:
            return self.config.get(section,item)

# *************************************
# RESULT WINDOW CLASS
# ************************************


class ResultWindow:

    def __init__(self, parent, title,display_it):
        self.display_it=display_it
        self.errors=0
        self.warnings=0
        if self.display_it == False: return
        top = tk.Toplevel()
        top.title(title)
        scrollbar = Scrollbar(top, orient=tk.VERTICAL)
        self.textb = Text(top,width=80,height=40, wrap='word', font="arial 11",padx=5,yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.textb.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.textb.pack(side=LEFT, fill=BOTH, expand=1)
        self.textb.config(state=NORMAL)
        self.textb.delete(1.0, END)
        self.textb.config(state=DISABLED)


    def display(self,priority,text):
        if priority=='f':   self.errors+=1
        if priority =='w':self.warnings +=1       
        if self.display_it==False: return
        self.textb.config(state=NORMAL)
        if priority=='t':
             self.textb.insert(END, text+"\n")
        if priority=='f':
            self.textb.insert(END, "    ** Error:   "+text+"\n\n")
        if priority=='w':
            self.textb.insert(END, "    ** Warning:   "+text+"\n\n")           
        self.textb.config(state=DISABLED)

    def stats(self):
        if self.display_it==False: return
        self.textb.config(state=NORMAL)
        self.textb.insert(END, "\nErrors: "+str(self.errors)+"\nWarnings: "+str(self.warnings)+"\n\n\n")
        self.textb.config(state=DISABLED)

    def num_errors(self):
        return self.errors
