import os
import sys
import copy

class ShowManager:
    
# ShowManager manages PiPresents concurrent shows. It does not manage sub-shows or child-shows.
# concurrent shows are always 'top level' shows:
# They can be started by the start show or by 'myshow start' in the Show Control field in the ShowPlayer
# They can be stopped either by 'myshow stop' in the Show Control field in the ShowPlayer
# or in the case of mediashows by making them single-run in its  Repeat field

# a show with the same reference should not be run twice as ther is no way to reference an individual instance when stopping
# ??? this could be changed as ther is sinlge-run to stop them, the stop command could stop all instances.

# Constants for list of shows
    shows=[]
    SHOW_TEMPLATE=['',None]
    SHOW_REF= 0   # show-reference  - name of the show as in editor
    SHOW_OBJ = 1   # the python object


# Initialise, first time through only in pipresents.py

    def init(self):
        ShowManager.shows=[]


#adds a new concurrent show to the list if not already there, returns an index for use by start and stop

    def register_show(self,ref):
        registered=self.show_registered(ref)
        if registered==-1:
            ShowManager.shows.append(copy.deepcopy(ShowManager.SHOW_TEMPLATE))
            index=len(ShowManager.shows)-1
            ShowManager.shows[index][ShowManager.SHOW_REF]=ref
            ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
            return index
        else:
            return registered

# can be used to return the index to the show
    def show_registered(self,show_ref):
        index=0
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_REF]==show_ref:
                return index
            index+=1
        return -1

# needs calling program to check that the show is not already running
    def set_running(self,index,show_obj):
         ShowManager.shows[index][ShowManager.SHOW_OBJ]=show_obj
         # print 'running', ShowManager.shows
         # print "started show ", ShowManager.shows[index][ShowManager.SHOW_REF]


    def show_running(self,index):
        if ShowManager.shows[index][ShowManager.SHOW_OBJ]<>None:
                return ShowManager.shows[index][ShowManager.SHOW_OBJ]
        else:
            return None
 
    def set_stopped(self,index):
        ShowManager.shows[index][ShowManager.SHOW_OBJ]=None
        # print "stopped show ", ShowManager.shows[index][ShowManager.SHOW_REF]
        #print 'stopping', ShowManager.shows

    def all_shows_stopped(self):
        all_stopped=True
        for show in ShowManager.shows:
            if show[ShowManager.SHOW_OBJ]<>None:
                all_stopped=False
        return all_stopped




