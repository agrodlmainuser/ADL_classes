
import sys
import subprocess

# installing libraries for HEIC image format reading
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
'pyheif'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
'exifread'])
# instal library for google photos gh images 
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
'pyproj'])

import xml.etree.ElementTree as ET
import PIL
import geopy.distance
import numpy as np
import os
import pickle
from PIL import Image
import pyheif # need pip install 
import exifread # need pip install
import io
import ntpath
import math
import pyproj # need pip install
from shapely.geometry import Point, Polygon


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

  def path_leaf(self):

    head, tail = ntpath.split(self.path_to_file)
    return tail or ntpath.basename(head)

  def convert_to_degrees(self, values):
    """values is a list that looks like: [41, 53, 569/20] 
       and each thing is a  exifread.utils.Ratio"""
    degrees, mins, secs = [v.num / v.den for v in values]
    return degrees + (mins / 60.0) + (secs / 3600.0)

  def read_exif(self):

    from PIL import Image
    if self.path_leaf().split('.')[-1] == 'HEIC':
      #print("HEIC")
      heif_file = pyheif.read_heif(self.path_to_file)
      for metadata in heif_file.metadata:
        file_stream = io.BytesIO(metadata['data'][6:])
        tags = exifread.process_file(file_stream, details=False)
        gps_lat  = tags.get("GPS GPSLatitude")
        gps_long = tags.get("GPS GPSLongitude")
        #print(gps_lat,gps_long)
        gps_lat =  self.convert_to_degrees(gps_lat.values)
        gps_long = self.convert_to_degrees(gps_long.values)
      return(gps_lat, gps_long)
    else:
      image = Image.open(self.path_to_file)
      #print(image.format)
      EXIF_data = image._getexif()
      gps_lat = EXIF_data[34853][2]
      gps_lat = gps_lat[0][0]/gps_lat[0][1] + (gps_lat[1][0]/gps_lat[1][1])/60 + (gps_lat[2][0]/gps_lat[2][1])/3600
      gps_long = EXIF_data[34853][4]
      gps_long = gps_long[0][0]/gps_long[0][1] + (gps_long[1][0]/gps_long[1][1])/60 + (gps_long[2][0]/gps_long[2][1])/3600
      return(gps_lat, gps_long)

    
class ADL_gh:

  def __init__(self, gh_corners_coordinates):
    self.gh_corners_coordinates = gh_corners_coordinates

  def setup(self):
    ''' this method order the coordinates in a counter-clockwise direction for future purposes '''
    # Find the centroid of the coordinates
    n = len(self.gh_corners_coordinates)
    x = sum(coordinate[0] for coordinate in self.gh_corners_coordinates) / n
    y = sum(coordinate[1] for coordinate in self.gh_corners_coordinates) / n
    centroid = (x, y)
    # Sort the coordinates by angle relative to the centroid
    sorted_coordinates = sorted(self.gh_corners_coordinates, key=lambda coordinate: math.atan2(coordinate[1] - y, coordinate[0] - x))
    # Check if the coordinates are in a clockwise or counterclockwise order
    clockwise = False
    for i in range(1, n):
      p1 = sorted_coordinates[i-1]
      p2 = sorted_coordinates[i]
      if p2[1] > p1[1] or (p2[1] == p1[1] and p2[0] < p1[0]):
        clockwise = True
        break
    # Reverse the coordinates if they are in a clockwise order
    if clockwise:
      sorted_coordinates = list(reversed(sorted_coordinates))
    self.gh_corners_coordinates = sorted_coordinates
  
  def check_if_in_gh(self, point_to_check):
    ''' this method check if a point is whithin the bounderiess of a gh or not. Do not perform this method unless doing the setup prior '''
    # Latitude and longitude coordinates of the GPS point
    lat, lon = point_to_check
    lon_deg = int(lon)
    # UTM zone for the coordinates
    utm_zone = (lon_deg + 180) // 6 + 1
    # Create a Pyproj transformer object to convert between WGS84 (latitude/longitude)
    # and UTM coordinates
    transformer = pyproj.Transformer.from_crs("EPSG:4326", f"EPSG:326{utm_zone}", always_xy=True)
    # Convert the latitude and longitude coordinates to UTM coordinates
    x, y = transformer.transform(lon, lat)
    # Create a Point object from the UTM coordinates of the GPS point
    point = Point(x, y)
    # Coordinates of the vertices of the polygon in UTM coordinates
    polygon_coords = self.gh_corners_coordinates
    # polygon coordinates should be in a counter-clockwise order that's why setup method is needed before executing this one
    # polygon cords should be in UTM system
    for i, cords in enumerate(polygon_coords):
      lat, lon = cords
      x, y = transformer.transform(lon, lat)
      polygon_coords[i] = (x,y)
    # Create a Polygon object from the UTM coordinates of the polygon
    polygon = Polygon(polygon_coords)
    # Check if the point is within the polygon using the `within` method
    # sometimes a point might be a bit further of the polygon, we set a factor of 0.5
    if point.within(polygon) or point.distance(polygon) < 0.5:
      print("The point is within the gh")
    else:
      print("The point is outside the gh")
  
  def line_mapping(self, lines_cor):
    lines_cor.sort(key = lambda x: float(x[1]))
    line_index = 1
    mapping_dict = {}
    for i, line_cor in enumerate(lines_cor):
      if i == 0 :
        mapping_dict[f"line_{line_index}"] = line_cor
        prev_cor = line_cor 
        line_index += 1
      else:
        if line_cor[0] == prev_cor[0] and line_cor[1] == prev_cor[1]:
          continue
        else:
          mapping_dict[f"line_{line_index}"] = line_cor
          line_index += 1
          prev_cor = line_cor 
    self.gh_lines = mapping_dict


class ADL_img_gh(ADL_EXIF):

  def check_in_current_gh(self, gh_dir, img_path):
    point = self.read_exif()
    for file1 in os.listdir(f"{gh_dir}/gh_details"):
        if file1.endswith("pkl"):
          file2 = open(f'{gh_dir}/gh_details/{file1}', 'rb')
          gh_object = pickle.load(file2)
          if gh_object.check_if_in_gh(point):
            return True 
          else:
            return False 
  
  def check_in_grower_dir(self, grower_dir, img_path):
    ''' check if the photo comes from one of the grower's gh's'''
    point = self.read_exif()
    flag = 0
    for gh in os.listdir(grower_dir):
      for file1 in os.listdir(f"{grower_dir}/{gh}/gh_details"):
        if file1.endswith("pkl"):
          file2 = open(f'{grower_dir}/{gh}/gh_details/{file1}', 'rb')
          gh_object = pickle.load(file2)
          if gh_object.check_if_in_gh(point):
            flag = 1
            return gh
          else:
            continue
    if flag == 0:
      print("no matching with grower's gh's") 
      return False
  
  def check_in_all_ghs(self, point):
    '''check all gh's in the system to find a match with the point '''
    flag = 0
    root_dir = "/content/drive/MyDrive/AgroDL/AgroDL_Data/Input/Image_countings"
    for crop in os.listdir(root_dir):
      for grower in os.listdir(f"{root_dir}/{crop}"):
        for gh in os.listdir(f"{root_dir}/{crop}/{grower}"):
          for file1 in os.listdir(f"{root_dir}/{crop}/{grower}/{gh}/gh_details"):
            if file1.endswith("pkl"):
              file2 = open(f'{root_dir}/{crop}/{grower}/{gh}/gh_details/{file1}', 'rb')
              gh_object = pickle.load(file2)
              if gh_object.check_if_in_gh(point):
                flag = 1
                return gh
              else:
                continue
    if flag == 0:
      print("no matching with any gh is the system.") 
      return False

class ADL_GH_analytics:

  def show_all_ghs(self):
    gh_dict = {}
    root_dir = "/content/drive/MyDrive/AgroDL/AgroDL_Data/Input/Image_countings"
    c = 0
    for crop in os.listdir(root_dir):
      for grower in os.listdir(f"{root_dir}/{crop}"):
        for gh in os.listdir(f"{root_dir}/{crop}/{grower}"):
          c += 1
          gh_dict[f"{grower}"] = f"{gh} crop:{crop}" 
          print(f"grower name: {grower}, GH name: {gh}, crop: {crop}")
    print(f"\n")
    print(f"in total there are {c} number of GHs that have been set in the system so far")

gh_obj = ADL_GH_analytics()
gh_obj.show_all_ghs()
      
      

