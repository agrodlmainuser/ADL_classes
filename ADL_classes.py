import xml.etree.ElementTree as ET
import PIL

class ADL_Read_XML:

  def __init__(self, script_name):
    self.script_name = script_name

  def get_params(self, param):
    
    dir_to_xml = "/content/drive/MyDrive/AgroDL/ADL_xml_main_file.xml"
    tree = ET.parse(dir_to_xml)
    scripts = tree.getroot()
    # loop over system params and script names
    for scripts_count,script in enumerate(scripts):
      # system params are located at iteration num 0
      if scripts_count == 0:
        for classification_models in script:
          for clf_param in classification_models:
              clf_param_name = str(clf_param).split()[1][1:-1]
              if clf_param_name == param:
                return clf_param.text

      # scripts are located at iterations 1 and up
      else:
        dir_name = str(script)
        dir_name = dir_name.split()[1][1:-1]
        if script.attrib["Name"] == self.script_name:
          # loop over directories and other script parameters
            for i, params in enumerate(script):
              for current_param in params:
                param_name = str(current_param).split()[1][1:-1]
                if param_name == param:
                  return current_param.text


class ADL_EXIF:

  def __init__(self, path_to_file):
    self.path_to_file = path_to_file

  def read_exif(self):
    image = PIL.Image.open(self.path_to_file)
    EXIF_data = image._getexif()
    gps_lat = float(EXIF_data[34853][2][0][0])
    gps_long = float(EXIF_data[34853][4][0][0])
    return (gps_lat/1000000, gps_long/1000000)
    


             