import os
import imp
import ConfigParser
from pp_utils import Monitor

class PluginManager:

    def __init__(self,show_id,root,canvas,show_params,track_params,pp_dir,pp_home,pp_profile):
        """
                show_id - show instance that player is run from (for monitoring only)
                canvas - the canvas onto which the image is to be drawn
                show_params -  dictionary of show parameters
                track_params - disctionary of track paramters
                pp_home - data home directory
                pp_dir - path of pipresents directory
                pp_profile - profile name
        """

        self.mon=Monitor()
        self.mon.off()

        self.show_id=show_id
        self.root=root
        self.canvas=canvas
        self.show_params=show_params
        self.track_params=track_params
        self.pp_dir=pp_dir
        self.pp_home=pp_home
        self.pp_profile=pp_profile
        self.plugin=None

 
    # called by players to execute a plugin
    def do_plugin(self,track_file,plugin_cfg):

        # checks existence of and reads the plugin config file
        plugin_cfg_file= self.complete_path(plugin_cfg)
        if not os.path.exists(plugin_cfg_file):
            return 'error','plugin configuration file not found '+ plugin_cfg_file,''
        plugin_params=self.read(plugin_cfg_file)

        # checks the plugin exists
        plugin_dir = self.pp_dir+os.sep+'pp_home'+os.sep+'pp_plugins'
        plugin_file = plugin_dir+os.sep+self.plugin_params['plugin']+'.py'

        if not os.path.exists(plugin_file):
            return 'error','plugin file not found '+ plugin_file,''

        # import and run the plugin
        name = self.plugin_params['plugin']
        self.load_plugin(name, plugin_dir)
        error,message,used_track=self.plugin.do_plugin(track_file)
        if error <>'normal':
            return error,message,''
        else:
            return 'normal','',used_track

    # called by players at the end of a track
    def stop_plugin(self):
        if self.plugin<>None:
            self.plugin.stop_plugin()


# **************************************
# plugin utilities
# **********************************

    def load_plugin(self, name, dir):
        fp, pathname,description = imp.find_module(name,[dir])
        plugin_id =  imp.load_module(name,fp,pathname,description)
        self.plugin=plugin_id.Plugin(self.root,self.canvas,
                                   self.plugin_params,self.track_params,self.show_params,
                                   self.pp_dir,self.pp_home,self.pp_profile)



# ***********************************
# plugin configuration file
# ***********************************

    def read(self,plugin_cfg_file):
            self.plugin_config = ConfigParser.ConfigParser()
            self.plugin_config.read(plugin_cfg_file)
            self.plugin_params =  dict(self.plugin_config.items('plugin'))
        

# ***********************************
# utilities
# ***********************************

    def complete_path(self,track_file):
        #  complete path of the filename of the selected entry
        if track_file[0]=="+":
                track_file=self.pp_home+track_file[1:]
        return track_file     
