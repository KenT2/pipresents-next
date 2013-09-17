class PPdefinitions:

    IMAGE_FILES=('Image files', '.gif','.jpg','.jpeg','.bmp','.png','.tif')
    VIDEO_FILES=('Video files','.mp4','.mkv','.avi','.mp2','.wmv','.m4v')
    AUDIO_FILES=('Audio files','.mp3','.wav','.ogg')


    # order of fields for editor display
    show_types={
    
        'mediashow':[
            'tab-show','sep',  
                     'type','title','show-ref', 'medialist','trigger','trigger-input','progress','trigger-next','next-input','sequence','repeat','repeat-interval','trigger-end','trigger-end-time','sep',
            'tab-child','sep',  
                'has-child', 'hint-text', 'hint-y','hint-font','hint-colour',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                    'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options',
            'tab-controls','sep',  
                    'disable-controls', 'controls'
            ],
                 
        'menu':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','menu-x', 'menu-y', 'menu-spacing','timeout','has-background','entry-font','entry-colour', 'entry-select-colour','sep',
                    'hint-text', 'hint-y', 'hint-font', 'hint-colour',
            'tab-show-text','sep',  
                    'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                    'background-image','background-colour','transition','duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options',
            'tab-controls','sep',  
               'disable-controls','controls'
            ],

        
        'liveshow':[
            'tab-show','sep',  
                'type','title','show-ref', 'medialist','trigger-start','trigger-start-time','trigger-end','trigger-end-time',
            'tab-child','sep',  
                    'has-child', 'hint-text', 'hint-y','hint-font','hint-colour',
            'tab-show-text','sep',
                   'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
        
                   
        'hyperlinkshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','home-track-ref','timeout','timeout-track-ref',            
            'tab-show-text','sep',
                'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options',
            'tab-links','sep',
                'links',
            'tab-controls','sep',  
                'disable-controls','controls'
            ],
        

        'radiobuttonshow':[
            'tab-show','sep',  
                'type','title','show-ref','medialist','first-track-ref','timeout',
            'tab-show-text','sep',
                    'show-text','show-text-font','show-text-colour','show-text-x','show-text-y',
            'tab-tracks','sep',  
                'background-image','background-colour','transition', 'duration','image-window','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options','omx-audio','omx-volume','omx-window','omx-other-options',
            'tab-links','sep',
                'links',
            'tab-controls','sep',  
                'disable-controls','controls'
                    ],
              
                'start':[
                    'tab-show','sep',  
                        'type','title','show-ref','start-show'
                    ]
             }


    # field details for creating new shows and for update of profile    
    new_shows={

               'hyperlinkshow':{ 'type':'hyperlinkshow','title':'New Hyperlink Show','show-ref':'', 'medialist':'',
                    'links':'','first-track-ref':'','home-track-ref':'','timeout-track-ref':'','disable-controls':'no','timeout': '60',
                             'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                            'transition': 'cut', 'duration': '0','image-window':'centred',
                             'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                                 'omx-audio': 'hdmi','omx-volume':'0','omx-window':'centred','omx-other-options': '',
                            'controls':''},

    
               'radiobuttonshow':{ 'type':'radiobuttonshow','title':'New Radio Button Show','show-ref':'', 'medialist':'',
                    'links':'','first-track-ref':'','disable-controls':'no','timeout': '60',
                             'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                            'transition': 'cut', 'duration': '0','image-window':'centred',
                             'audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                                   'omx-audio': 'hdmi','omx-volume':'0','omx-window':'centred','omx-other-options': '',
                                   'controls':''},
    
                'mediashow':{'title': 'New Mediashow','show-ref':'', 'type': 'mediashow','medialist': '',
                          'disable-controls':'no','trigger': 'start','trigger-input':'','progress': 'auto','trigger-next': 'continue','next-input':'','sequence': 'ordered','repeat': 'interval','repeat-interval': '10','trigger-end':'none', 'trigger-end-time':'',
                            'has-child': 'no', 'hint-text': '', 'hint-y': '100','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                            'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                            'transition': 'cut', 'duration': '5','image-window':'centred','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                             'omx-audio': 'hdmi','omx-volume':'0','omx-window':'centred','omx-other-options': '',
                             'controls':''},
                                     
                'liveshow':{'title': 'New Liveshow','show-ref':'', 'type': 'liveshow', 'disable-controls':'no','trigger-start': 'start','trigger-start-time':'','trigger-end':'none', 'trigger-end-time':'','medialist': '',
                        'has-child': 'no', 'hint-text': '', 'hint-y': '100','hint-font': 'Helvetica 30 bold','hint-colour': 'white',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                         'transition': 'cut', 'duration': '5','image-window':'centred','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0','mplayer-other-options':'',
                            'omx-audio': 'hdmi','omx-volume':'0','omx-window':'centred','omx-other-options': '',
                            'controls':''},
            
                'menu':{'show-ref': '', 'title': 'New Menu','type': 'menu','medialist': '',
                        'disable-controls':'no','menu-x': '300', 'menu-y': '250', 'menu-spacing': '70','timeout': '0','has-background': 'yes',
                        'entry-font': 'Helvetica 30 bold','entry-colour': 'black', 'entry-select-colour': 'red',
                        'hint-text': 'Up, down to Select, Return to Play', 'hint-y': '100', 'hint-font': 'Helvetica 30 bold', 'hint-colour': 'white',
                        'show-text':'','show-text-font':'','show-text-colour':'','show-text-x':'0','show-text-y':'0','background-image':'','background-colour':'',
                'transition': 'cut',  'duration': '5','image-window':'centred','audio-speaker':'stereo','mplayer-audio':'hdmi','mplayer-volume':'0', 'mplayer-other-options':'',
                        'omx-audio': 'hdmi','omx-volume':'0','omx-window':'centred','omx-other-options': '',
                        'controls':''},
            
                'start':{'title': 'Start','show-ref':'start', 'type': 'start','start-show':''}  
            }
    
    show_field_specs={
                    'sep':{'shape':'sep'},
                    'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'MPlayer Speaker','must':'no','read-only':'no',
                             'values':['left','right','stereo']},
                    'background-colour':{'param':'background-colour','shape':'colour','text':'Background Colour','must':'no','read-only':'no'},
                    'background-image':{'param':'background-image','shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                    'controls':{'param':'controls','shape':'text','text':'Controls','must':'no','read-only':'no'},
                    'disable-controls':{'param':'disable-controls','shape':'option-menu','text':'Disable Controls ','must':'no','read-only':'no','values':['yes','no']},
                    'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                    'entry-font':{'param':'entry-font','shape':'font','text':'Entry Font','must':'no','read-only':'no'},
                    'entry-colour':{'param':'entry-colour','shape':'colour','text':'Entry Colour','must':'no','read-only':'no'},
                    'entry-select-colour':{'param':'entry-select-colour','shape':'colour','text':'Selected Entry Colour','must':'no','read-only':'no'},
                    'timeout-track-ref':{'param':'timeout-track-ref','shape':'entry','text':'Timeout Track','must':'no','read-only':'no'},
                    'first-track-ref':{'param':'first-track-ref','shape':'entry','text':'First Track','must':'no','read-only':'no'},
                    'has-child':{'param':'has-child','shape':'option-menu','text':'Has Child','must':'no','read-only':'no',
                                        'values':['yes','no']},
                    'has-background':{'param':'has-background','shape':'option-menu','text':'Has Background Image','must':'no','read-only':'no','values':['yes','no']},
                    'hint-text':{'param':'hint-text','shape':'entry','text':'Hint Text','must':'no','read-only':'no'},
                    'hint-y':{'param':'hint-y','shape':'entry','text':'Hint y from bottom','must':'no','read-only':'no'},
                    'hint-font':{'param':'hint-font','shape':'font','text':'Hint Font','must':'no','read-only':'no'},
                    'hint-colour':{'param':'hint-colour','shape':'colour','text':'Hint Colour','must':'no','read-only':'no'},
                    'home-track-ref':{'param':'home-track-ref','shape':'entry','text':'Home Track','must':'no','read-only':'no'},
                    'image-window':{'param':'image-window','shape':'entry','text':'Image Window','must':'no','read-only':'no'},
                    'links':{'param':'links','shape':'text','text':'Links','must':'no','read-only':'no'},
                    'medialist':{'param':'medialist','shape':'entry','text':'Medialist','must':'no','read-only':'no'},
                    'menu-x':{'param':'menu-x','shape':'entry','text':'Menu x Position','must':'no','read-only':'no'},
                    'menu-y':{'param':'menu-y','shape':'entry','text':'Menu y Position','must':'no','read-only':'no'},
                    'menu-spacing':{'param':'menu-spacing','shape':'entry','text':'Entry Spacing','must':'no','read-only':'no'},
                    'message-font':{'param':'message-font','shape':'font','text':'Text Font','must':'yes','read-only':'no'},
                    'message-colour':{'param':'message-colour','shape':'colour','text':'Text Colour','must':'yes','read-only':'no'},
                    'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'MPlayer Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Other MPlayer Options','must':'no','read-only':'no'},
                    'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'MPlayer Volume','must':'no','read-only':'no'},
                    'next-input':{'param':'next-input','shape':'entry','text':'Next Input','must':'no','read-only':'no'},
                    'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'OMX Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local']},
                    'omx-other-options':{'param':'omx-other-options','shape':'entry','text':'Other OMX Options','must':'no','read-only':'no'},
                    'omx-volume':{'param':'omx-volume','shape':'entry','text':'OMXPlayer Volume','must':'no','read-only':'no'},
                    'omx-window':{'param':'omx-window','shape':'entry','text':'OMXPlayer Window','must':'no','read-only':'no'},


                    'progress':{'param':'progress','shape':'option-menu','text':'Progress','must':'no','read-only':'no',
                                        'values':['auto','manual']},
                    'repeat':{'param':'repeat','shape':'option-menu','text':'Repeat','must':'no','read-only':'no',
                                        'values':['oneshot','interval','single-run']},
                    'repeat-interval':{'param':'repeat-interval','shape':'entry','text':'Repeat Interval (secs.)','must':'no','read-only':'no'},
                    'sequence':{'param':'sequence','shape':'option-menu','text':'Sequence','must':'no','read-only':'no',
                                        'values':['ordered','shuffle']},
                    'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                    'show-text':{'param':'show-text','shape':'text','text':'Show Text','must':'no','read-only':'no'},
                    'show-text-font':{'param':'show-text-font','shape':'font','text':'Show Text Font','must':'no','read-only':'no'},
                    'show-text-colour':{'param':'show-text-colour','shape':'colour','text':'Show Text Colour','must':'no','read-only':'no'},
                    'show-text-x':{'param':'show-text-x','shape':'entry','text':'Show Text x Position','must':'no','read-only':'no'},
                    'show-text-y':{'param':'show-text-y','shape':'entry','text':'Show Text y Position','must':'no','read-only':'no'},
                    'start-show':{'param':'start-show','shape':'entry','text':'Start Shows','must':'no','read-only':'no'},
                    'tab-animation':{'shape':'tab','name':'animation','text':'Animation'},
                    'tab-child':{'shape':'tab','name':'child','text':'Child Show'},
                    'tab-controls':{'shape':'tab','name':'controls','text':'Controls'},
                    'tab-links':{'shape':'tab','name':'links','text':'Links'},
                    'tab-show':{'shape':'tab','name':'show','text':'Show'},
                    'tab-show-text':{'shape':'tab','name':'show-text','text':'Show Text'},
                    'tab-track':{'shape':'tab','name':'track','text':'Track'},
                    'tab-tracks':{'shape':'tab','name':'tracks','text':'Track Defaults'},
                    'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                    'timeout':{'param':'timeout','shape':'entry','text':'Timeout (secs)','must':'no','read-only':'no'},
                    'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                    'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no',
                                 'values':['cut',]},
                    'trigger':{'param':'trigger','shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no',
                                 'values':['start','input','input-quiet','time','time-quiet']},
                    'trigger-start':{'param':'trigger-start','shape':'option-menu','text':'Trigger for Start','must':'no','read-only':'no','values':['start','time','time-quiet']},
                    'trigger-end':{'param':'trigger-end','shape':'option-menu','text':'Trigger for End','must':'no','read-only':'no','values':['none','time','duration']},
                    'trigger-next':{'param':'trigger-next','shape':'option-menu','text':'Trigger for next','must':'no','read-only':'no','values':['continue','input']},
                    'trigger-start-time':{'param':'trigger-start-time','shape':'entry','text':'Start Times','must':'no','read-only':'no'},
                    'trigger-end-time':{'param':'trigger-end-time','shape':'entry','text':'End Times','must':'no','read-only':'no'},
                    'trigger-input':{'param':'trigger-input','shape':'entry','text':'Trigger Input','must':'no','read-only':'no'},
                    'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'},
                          }

    track_types={
        'video':[
            'tab-track','sep',  
                    'type','title','track-ref','location','omx-audio','omx-volume','omx-window','background-colour','background-image',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],
                
        'message':[
            'tab-track','sep',  
                'type','title','track-ref','text','duration','message-font','message-colour','message-justify','message-x','message-y','background-colour','background-image',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],
        
                
        'show':[
            'tab-track','sep',  
                'type','title','track-ref','sub-show'
            ],
        
                 
        'image':[
            'tab-track','sep',  
                'type','title','track-ref','location','duration','transition','image-window','background-colour','background-image',
            'tab-track-text','sep',
                'track-text','track-text-font','track-text-colour','track-text-x','track-text-y',
            'tab-links','sep',
                'links',
            'tab-show-control','sep',
                'show-control-begin','show-control-end',
            'tab-animate','sep',
                'animate-begin','animate-clear','animate-end'
            ],

                       
        'audio':[
            'tab-track','sep',  
                'type','title','track-ref','location','duration','audio-speaker','mplayer-audio','mplayer-volume','mplayer-other-options',
                       'clear-screen','background-colour','background-image',
            'tab-track-text','sep',
                 'track-text','track-text-font','track-text-colour','track-text-x','track-text-y',
            'tab-links','sep',
                 'links',
            'tab-show-control','sep',
                 'show-control-begin','show-control-end',
            'tab-animate','sep',
                 'animate-begin','animate-clear','animate-end'
                 ],

                       
        'menu-background':[
            'tab-track','sep',  
                'type','title','track-ref','location'
            ]
                         }                   

    new_tracks={
        
                'video':{'title':'New Video','track-ref':'','type':'video','location':'','omx-audio':'','omx-volume':'','omx-window':'','background-colour':'','background-image':'','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':''},
                       
                'message':{'title':'New Message','track-ref':'','type':'message','text':'','duration':'5','message-font':'Helvetica 30 bold','message-colour':'white','message-justify':'left','message-x':'','message-y':'',
                           'background-colour':'','background-image':'','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':''},
                
                'show':{'title':'New Show','track-ref':'','type':'show','sub-show':''},   
                
                'image':{'title':'New Image','track-ref':'','type':'image','location':'','duration':'','transition':'','image-window':'','background-colour':'','background-image':'','track-text':'','track-text-font':'',
                       'track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':''},
                       
                'audio':{'title':'New Audio','track-ref':'','type':'audio','location':'', 'duration':'','audio-speaker':'','mplayer-audio':'','mplayer-volume':'',
                          'mplayer-other-options':'','clear-screen':'no','background-colour':'','background-image':'','track-text':'','track-text-font':'','track-text-colour':'','track-text-x':'0','track-text-y':'0','links':'','show-control-begin':'','show-control-end':'','animate-begin':'','animate-clear':'no','animate-end':''},
                
                'menu-background':{'title':'New Menu Background','track-ref':'pp-menu-background','type':'menu-background','location':''},
                
                'child-show': {'title':'New Child Show','track-ref':'pp-child-show','type':'show','sub-show':''}
                         }


    
    track_field_specs={'sep':{'shape':'sep'},
                            'animate-begin':{'param':'animate-begin','shape':'text','text':'Animation at Beginning','must':'no','read-only':'no'},
                            'animate-end':{'param':'animate-end','shape':'text','text':'Animation at End','must':'no','read-only':'no'},
                            'animate-clear':{'param':'animate-clear','shape':'option-menu','text':'Clear Animation','must':'no','read-only':'no',
                                      'values':['yes','no']},
                            'audio-speaker':{'param':'audio-speaker','shape':'option-menu','text':'MPlayer Speaker','must':'no','read-only':'no',
                                       'values':['left','right','stereo','']},
                            'background-image':{'param':'background-image','shape':'browse','text':'Background Image','must':'no','read-only':'no'},
                            'background-colour':{'param':'background-colour','shape':'colour','text':'Background Colour','must':'no','read-only':'no'},
                            'clear-screen':{'param':'clear-screen','shape':'option-menu','text':'Clear Screen','must':'no','read-only':'no',
                                       'values':['yes','no']},
                            'duration':{'param':'duration','shape':'entry','text':'Duration (secs)','must':'no','read-only':'no'},
                            'image-window':{'param':'image-window','shape':'entry','text':'Image Window','must':'no','read-only':'no'},
                            'location':{'param':'location','shape':'browse','text':'Location','must':'no','read-only':'no'},
                            'links':{'param':'links','shape':'text','text':'Links','must':'no','read-only':'no'},
                            'message-font':{'param':'message-font','shape':'font','text':'Text Font','must':'no','read-only':'no'},
                            'message-colour':{'param':'message-colour','shape':'colour','text':'Text Colour','must':'no','read-only':'no'},
                            'message-justify':{'param':'message-justify','shape':'option-menu','text':'Justification','must':'no','read-only':'no',
                                       'values':['left','center','right']},
                            'message-x':{'param':'message-x','shape':'entry','text':'Message x Position','must':'no','read-only':'no'},
                            'message-y':{'param':'message-y','shape':'entry','text':'Message y Position','must':'no','read-only':'no'},
                            'mplayer-audio':{'param':'mplayer-audio','shape':'option-menu','text':'MPlayer Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'mplayer-other-options':{'param':'mplayer-other-options','shape':'entry','text':'Other MPlayer Options','must':'no','read-only':'no'},
                            'mplayer-volume':{'param':'mplayer-volume','shape':'entry','text':'MPlayer Volume','must':'no','read-only':'no'},
                            'links':{'param':'links','shape':'text','text':'Links','must':'no','read-only':'no'},
                            'omx-audio':{'param':'omx-audio','shape':'option-menu','text':'OMX Audio','must':'no','read-only':'no',
                                       'values':['hdmi','local','']},
                            'omx-volume':{'param':'omx-volume','shape':'entry','text':'OMXPlayer Volume','must':'no','read-only':'no'},
                            'omx-window':{'param':'omx-window','shape':'entry','text':'OMXPlayer Window','must':'no','read-only':'no'},
                            'show-ref':{'param':'show-ref','shape':'entry','text':'Show Reference','must':'no','read-only':'no'},
                            'show-control-begin':{'param':'show-control-begin','shape':'text','text':'Show Control at Beginning','must':'no','read-only':'no'},
                            'show-control-end':{'param':'show-control-end','shape':'text','text':'Show Control at End','must':'no','read-only':'no'},
                            'sub-show':{'param':'sub-show','shape':'option-menu','text':'Show to Run','must':'no','read-only':'no'},

                            'tab-animate':{'shape':'tab','name':'animate','text':'Animation'},
                            'tab-show-control':{'shape':'tab','name':'show-control','text':'Show Control'},
                            'tab-links':{'shape':'tab','name':'links','text':'Links'},
                            'tab-track-text':{'shape':'tab','name':'track-text','text':'Track Text'},
                            'tab-track':{'shape':'tab','name':'track','text':'Track'},
                            'text':{'param':'text','shape':'text','text':'Message Text','must':'no','read-only':'no'},
                            'title':{'param':'title','shape':'entry','text':'Title','must':'no','read-only':'no'},
                            'track-ref':{'param':'track-ref','shape':'entry','text':'Track Reference','must':'no','read-only':'no'},
                            'track-text':{'param':'track-text','shape':'text','text':'Track Text','must':'no','read-only':'no'},
                            'track-text-font':{'param':'track-text-font','shape':'entry','text':'Track Text Font','must':'no','read-only':'no'},
                            'track-text-colour':{'param':'track-text-colour','shape':'colour','text':'Track Text Colour','must':'no','read-only':'no'},
                            'track-text-x':{'param':'track-text-x','shape':'entry','text':'Track Text x Position','must':'no','read-only':'no'},
                            'track-text-y':{'param':'track-text-y','shape':'entry','text':'Track Text y Position','must':'no','read-only':'no'},
                            'transition':{'param':'transition','shape':'option-menu','text':'Transition','must':'no','read-only':'no','values':['cut','']},
                            'type':{'param':'type','shape':'entry','text':'Type','must':'no','read-only':'yes'}
                          }
        
