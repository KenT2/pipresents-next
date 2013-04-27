class PPdefinitions:

    IMAGE_FILES=('Image files', '.gif','.jpg','.jpeg','.bmp','.png','.tif')
    VIDEO_FILES=('Video files','.mp4','.mkv','.avi','.mp2','.wmv','.m4v')
    AUDIO_FILES=('Audio files','.mp3','.wav','.ogg','.wma')
    
    show_types={
    
                'mediashow':[ 'type','title','show-ref', 'medialist','sep',
                    'disable-controls','trigger','trigger-input','progress','trigger-next','next-input','sequence','repeat','repeat-interval','trigger-end','trigger-end-time','sep',
                    'has-child', 'hint-text', 'hint-y','hint-font','hint-colour','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
                   'transition', 'duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options'],
                 
                'menu':['type','title','show-ref','medialist','sep',
                    'disable-controls','menu-x', 'menu-y', 'menu-spacing','timeout','has-background',
                    'entry-font','entry-colour', 'entry-select-colour','sep',
                    'hint-text', 'hint-y', 'hint-font', 'hint-colour','sep',
                    'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
                    'transition','duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options'],
               
                'liveshow':[ 'type','title','show-ref', 'medialist','sep','disable-controls','trigger-start','trigger-start-time','trigger-end','trigger-end-time','sep',
                    'has-child', 'hint-text', 'hint-y','hint-font','hint-colour','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
                   'transition', 'duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-loop','omx-other-options'],
                 
                'start':['type','title','show-ref','start-show']
             }

        # must update show_types and new_shows
        
    new_shows={
    
                'mediashow':{'title': 'New Mediashow','show-ref':'', 'type': 'mediashow','medialist': '',
                          'disable-controls':'no','trigger': 'start','trigger-input':'','progress': 'auto','trigger-next': 'none','next-input':'','sequence': 'ordered','repeat': 'interval','repeat-interval': '10','trigger-end':'none', 'trigger-end-time':'',
                            'has-child': 'no', 'hint-text': '', 'hint-y': '100','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                            'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0',
                            'transition': 'cut', 'duration': '5','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'','omx-audio': 'hdmi','omx-volume':'0','omx-window':'','omx-other-options': ''},
                                     
                'liveshow':{'title': 'New Liveshow','show-ref':'', 'type': 'liveshow', 'disable-controls':'no','trigger-start': 'start','trigger-start-time':'','trigger-end':'none', 'trigger-end-time':'','medialist': '',
                        'has-child': 'no', 'hint-text': '', 'hint-y': '100','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0',
                         'transition': 'cut', 'duration': '5','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'','omx-audio': 'hdmi','omx-volume':'0','omx-window':'','omx-loop':'no','omx-other-options': ''},
            
                'menu':{'show-ref': '', 'title': 'New Menu','type': 'menu','medialist': '',
                        'disable-controls':'no','menu-x': '300', 'menu-y': '250', 'menu-spacing': '70','timeout': '0','has-background': 'yes',
                        'entry-font': 'Helvetica 30 bold','entry-colour': 'black', 'entry-select-colour': 'red',
                        'hint-text': 'Up, down to Select, Return to Play', 'hint-y': '100', 'hint-font': 'Helvetica 30 bold', 'hint-colour': 'white',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0',
                'transition': 'cut',  'duration': '5','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0', 'mplayer-other-options':'','omx-audio': 'hdmi','omx-volume':'0','omx-window':'','omx-other-options': ''},
            
                'start':{'title': 'First Show','show-ref':'start', 'type': 'start','start-show':'','controlled-show':''}  
            }
    
    show_field_specs={
                    'sep':{'shape':'sep'},
                    'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'MPlayer Speaker','must':'no','read-only':'no',
                             'values':['left','right','stereo']},
                    'disable-controls':{'param':'disable-controls','shape':'option-menu','text':'Disable Controls ','must':'no','read-only':'no','values':['yes','no']},
                    'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                    'entry-font':{'param':'entry-font','shape':'entry','text':'Entry Font','must':'no','read-only':'no'},
                    'entry-colour':{'param':'entry-colour','shape':'entry','text':'Entry Colour','must':'no','read-only':'no'},
                    'entry-select-colour':{'param':'entry-select-colour','shape':'entry','text':'Selected Entry Colour','must':'no','read-only':'no'},
                    'has-child':{'param':'has-child','shape':'option-menu','text':'Has Child','must':'no','read-only':'no',
                                        'values':['yes','no']},
                    'has-background':{'param':'has-background','shape':'option-menu','text':'Has Background Image','must':'no','read-only':'no','values':['yes','no']},
                    'hint-text':{'param':'hint-text','shape':'entry','text':'Hint Text','must':'no','read-only':'no'},
                    'hint-y':{'param':'hint-y','shape':'entry','text':'Hint y from bottom','must':'no','read-only':'no'},
                    'hint-font':{'param':'hint-font','shape':'entry','text':'Hint Font','must':'no','read-only':'no'},
                    'hint-colour':{'param':'hint-colour','shape':'entry','text':'Hint Colour','must':'no','read-only':'no'},
                    'medialist':{'param':'medialist','shape':'entry','text':'Medialist','must':'no','read-only':'no'},
                    'menu-x':{'param':'menu-x','shape':'entry','text':'Menu x Position','must':'no','read-only':'no'},
                    'menu-y':{'param':'menu-y','shape':'entry','text':'Menu y Position','must':'no','read-only':'no'},
                    'menu-spacing':{'param':'menu-spacing','shape':'entry','text':'Entry Spacing','must':'no','read-only':'no'},
                    'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'MPlayer Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Other MPlayer Options','must':'no','read-only':'no'},
                    'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'MPlayer Volume','must':'no','read-only':'no'},
                    'next-input':{'param':'next-input','shape':'entry','text':'Next Input','must':'no','read-only':'no'},
                    'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'OMX Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'omx-loop':{'param':'omx-loop','shape':'option-menu','text':'Seamless Loop','must':'no','read-only':'no',
                                       'values':['yes','no']},
                    'omx-other-options':{'param':'omx-other-options','shape':'entry','text':'Other OMX Options','must':'no','read-only':'no'},
                    'omx-volume':{'param':'omx-volume','shape':'entry','text':'OMXPlayer Volume','must':'no','read-only':'no'},
                    'omx-window':{'param':'omx-window','shape':'entry','text':'OMXPlayer Window','must':'no','read-only':'no'},
                    'progress':{'param':'progress','shape':'option-menu','text':'Progress','must':'no','read-only':'no',
                                        'values':['auto','manual']},
                    'repeat':{'param':'repeat','shape':'option-menu','text':'Repeat','must':'no','read-only':'no',
                                        'values':['oneshot','interval']},
                    'repeat-interval':{'param':'repeat-interval','shape':'entry','text':'Repeat Interval (secs.)','must':'no','read-only':'no'},
                    'sequence':{'param':'sequence','shape':'option-menu','text':'Sequence','must':'no','read-only':'no',
                                        'values':['ordered','shuffle']},
                    'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                    'show-text':{'param':'show-text','shape':'entry','text':'Show Text','must':'no','read-only':'no'},
                    'show-text-font':{'param':'show-text-font','shape':'entry','text':'Show Text Font','must':'no','read-only':'no'},
                    'show-text-colour':{'param':'show-text-colour','shape':'entry','text':'Show Text Colour','must':'no','read-only':'no'},
                    'show-text-x':{'param':'show-text-x','shape':'entry','text':'Show Text x Position','must':'no','read-only':'no'},
                    'show-text-y':{'param':'show-text-y','shape':'entry','text':'Show Text y Position','must':'no','read-only':'no'},
                    'start-show':{'param':'start-show','shape':'entry','text':'Start Shows','must':'no','read-only':'no'},
                    'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                    'timeout':{'param':'timeout','shape':'entry','text':'Timeout (secs)','must':'no','read-only':'no'},
                    'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                    'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no',
                                 'values':['cut',]},
                    'trigger':{'param':'trigger','shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no',
                                 'values':['start','button','time','time-quiet','GPIO']},
                    'trigger-start':{'param':'trigger-start','shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no','values':['start','time','time-quiet']},
                    'trigger-end':{'param':'trigger-end','shape':'option-menu','text':'Trigger for End','must':'no','read-only':'no','values':['none','time','duration']},
                    'trigger-next':{'param':'trigger-next','shape':'option-menu','text':'Trigger for next','must':'no','read-only':'no','values':['none','GPIO']},
                    'trigger-start-time':{'param':'trigger-start-time','shape':'entry','text':'Start Times','must':'no','read-only':'no'},
                    'trigger-end-time':{'param':'trigger-end-time','shape':'entry','text':'End Times','must':'no','read-only':'no'},
                    'trigger-input':{'param':'trigger-input','shape':'entry','text':'Trigger Input','must':'no','read-only':'no'},
                    'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'},
                          }
                         

    new_tracks={
                'video':{'title':'New Video','track-ref':'','type':'video','location':'','omx-audio':'','omx-volume':'','omx-window':'','omx-loop':'no','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','animate-begin':'','animate-clear':'no','animate-end':''},
                'message':{'title':'New Message','track-ref':'','type':'message','text':'','duration':'5','message-font':'Helvetica 30 bold','message-colour':'white','message-justify':'left','background-colour':'','background-image':''},
                'show':{'title':'New Show','track-ref':'','type':'show','sub-show':''},
                'image':{'title':'New Image','track-ref':'','type':'image','location':'','duration':'','transition':'','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','animate-begin':'','animate-clear':'no','animate-end':''},
                'audio':{'title':'New Audio','track-ref':'','type':'audio','location':'', 'duration':'0','audio-speaker':'','mplayer-audio':'','mplayer-volume':'',
                          'mplayer-other-options':'','clear-screen':'no','background-image':'','track-text':'','track-text-font':'','track-text-colour':'','track-text-x':'0','track-text-y':'0',
                          'animate-begin':'','animate-clear':'no','animate-end':''},
                'menu-background':{'title':'New Menu Background','track-ref':'pp-menu-background','type':'menu-background','location':''},
                'child-show': {'title':'New Child Show','track-ref':'pp-child-show','type':'show','sub-show':''}
                         }

    track_types={'video':['type','title','track-ref','location','omx-audio','omx-volume','omx-window','omx-loop','track-text','track-text-font','track-text-colour','track-text-x','track-text-y','animate-begin','animate-clear','animate-end'],
                'message':['type','title','track-ref','text','duration','message-font','message-colour','message-justify','background-colour','background-image'],
                'show':['type','title','track-ref','sub-show'],
                'image':['type','title','track-ref','location','duration','transition','track-text','track-text-font','track-text-colour',
                       'track-text-x','track-text-y','animate-begin','animate-clear','animate-end'],
                'audio':['type','title','track-ref','location','duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
                       'clear-screen','background-image','track-text','track-text-font','track-text-colour','track-text-x','track-text-y','animate-begin','animate-clear','animate-end'],
                'menu-background':['type','title','track-ref','location']
                         }
    
    track_field_specs={'sep':{'shape':'sep'},
                            'animate-begin':{'param':'animate-begin','shape':'text','text':'Begin Animation','must':'no','read-only':'no'},
                            'animate-end':{'param':'animate-end','shape':'text','text':'End Animation','must':'no','read-only':'no'},
                            'animate-clear':{'param':'animate-clear','shape':'option-menu','text':'Clear Animation','must':'no','read-only':'no',
                                      'values':['yes','no']},
                            'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'MPlayer Speaker','must':'no','read-only':'no',
                                       'values':['left','right','stereo','']},
                            'background-image':{'param':'background-image','shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                            'background-colour':{'param':'background-colour','shape':'entry','text':'Background Colour','must':'no','read-only':'no'},
                            'clear-screen':{'param':'clear-screen','shape':'option-menu','text':'Clear Screen','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                            'location':{'param':'location','shape':'browse','text':'Location','must':'no','read-only':'no'},
                            'message-justify':{'param':'message-justify','shape':'option-menu','text':'Justification','must':'no','read-only':'no',
                                       'values':['left','center','right']},
                            'message-font':{'param':'message-font','shape':'entry','text':'Text Font','must':'no','read-only':'no'},
                            'message-colour':{'param':'message-colour','shape':'entry','text':'Text Colour','must':'no','read-only':'no'},
                            'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'MPlayer Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Other MPlayer Options','must':'no','read-only':'no'},
                            'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'MPlayer Volume','must':'no','read-only':'no'},
                            'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'omx-audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'omx-loop':{'param':'omx-loop','shape':'option-menu','text':'Seamless Loop','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'omx-volume':{'param':'omx-volume','shape':'entry','text':'OMXPlayer Volume','must':'no','read-only':'no'},
                            'omx-window':{'param':'omx-window','shape':'entry','text':'OMXPlayer Window','must':'no','read-only':'no'},
                            'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                            'sub-show':{'param':'sub-show','shape':'option-menu','text':'Show to Run','must':'no','read-only':'no'},
                            'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                            'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                            'track-ref':{'param':'track-ref','shape':'entry','text':'Track Reference','must':'no','read-only':'no'},
                            'track-text':{'param':'track-text','shape':'entry','text':'Track Text','must':'no','read-only':'no'},
                            'track-text-font':{'param':'track-text-font','shape':'entry','text':'Track Text Font','must':'no','read-only':'no'},
                            'track-text-colour':{'param':'track-text-colour','shape':'entry','text':'Track Text Colour','must':'no','read-only':'no'},
                            'track-text-x':{'param':'track-text-x','shape':'entry','text':'Track Text x Position','must':'no','read-only':'no'},
                            'track-text-y':{'param':'track-text-y','shape':'entry','text':'Track Text y Position','must':'no','read-only':'no'},
                            'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no','values':['cut','']},
                            'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'}
                          }
        
