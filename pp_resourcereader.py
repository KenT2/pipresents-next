import os
import ConfigParser
from pp_utils import Monitor


class ResourceReader:
    config=None

    def __init__(self):
        self.mon=Monitor()
        self.mon.on()
        
    def read(self,pp_dir,pp_home):
        if ResourceReader.config==None:
            tryfile=pp_home+os.sep+"resources.cfg"
            if os.path.exists(tryfile):
                 filename=tryfile
            else:
                self.mon.log(self,"Resources not found at "+ tryfile)
                tryfile=pp_dir+os.sep+'pp_home'+os.sep+"resources.cfg"
                if os.path.exists(tryfile):
                    filename=tryfile
                else:
                    self.mon.log(self,"Resources not found at "+ tryfile)
                    self.mon.err(self,"resources.cfg not found")
                    return False   
            ResourceReader.config = ConfigParser.ConfigParser()
            ResourceReader.config.read(filename)
            self.mon.log(self,"Read resources from "+ filename)
            return True

    def get(self,section,item):
        if ResourceReader.config.has_option(section,item)==False:
            return False
        else:
            return ResourceReader.config.get(section,item)
    

        


