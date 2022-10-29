
import xml.etree.ElementTree as ET
import PIL
import geopy.distance
import numpy as np
import os
import pickle


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
    from PIL import Image
    image = PIL.Image.open(self.path_to_file)
    EXIF_data = image._getexif()
    gps_lat = float(EXIF_data[34853][2][0][0])
    gps_long = float(EXIF_data[34853][4][0][0])
    return (gps_lat/1000000, gps_long/1000000)


class ADL_gh:

  def __init__(self, gh_corners_coordinates):
    self.gh_corners_coordinates = gh_corners_coordinates

  def setup(self):
    # comlete missing corner in case of input of 3
    if len(self.gh_corners_coordinates) == 3:
      rr = np.array(self.gh_corners_coordinates)
      a = geopy.distance.distance(rr[0], rr[1]).km
      b = geopy.distance.distance(rr[0], rr[2]).km
      c = geopy.distance.distance(rr[1], rr[2]).km

      if a > b and a > c:
        self.max_dist = a
        flag = 2
        self.corner = rr[2]
        if b > c:
          self.near_corner = rr[1]
          self.far_corner = rr[0]
        else:
          self.near_corner = rr[0]
          self.far_corner = rr[1]
      elif b > a and b > c:
        self.max_dist = b
        flag = 1
        self.corner = rr[1]
        if a > c:
          self.near_corner = rr[2]
          self.far_corner = rr[0]
        else:
          self.near_corner = rr[0]
          self.far_corner = rr[2]    
      else:
        self.max_dist = c
        flag = 0
        self.corner = rr[0]
        if a > b:
          self.near_corner = rr[2]
          self.far_corner = rr[1]
        else:
          self.near_corner = rr[1]
          self.far_corner = rr[2]
      fourth_corner = self.near_corner - self.corner + self.far_corner
      self.fourth_corner = tuple(fourth_corner)
      # adding fourth corner to the input coordinates list
      self.gh_corners_coordinates.append(self.fourth_corner)
    # in case of input of 4
    else:
      corner = self.gh_corners_coordinates[0]
      near_corner = self.gh_corners_coordinates[0]
      far_corner = self.gh_corners_coordinates[0]
      fourth_corner = self.gh_corners_coordinates[0]
  
  def check_if_in_gh(self, point):
    n_points = [self.gh_corners_coordinates[0][0], self.gh_corners_coordinates[1][0], 
                self.gh_corners_coordinates[2][0], self.gh_corners_coordinates[3][0]]
    e_points = [self.gh_corners_coordinates[0][1], self.gh_corners_coordinates[1][1],
                self.gh_corners_coordinates[2][1], self.gh_corners_coordinates[3][1]]
    for i in range(4):
      dist = geopy.distance.distance(point, self.gh_corners_coordinates[i]).km
      # checking the distance from the current corner to the provided point
      # cheching if the provided point in out of the max/min limits from both north/south and east/west
      if dist > 0.9 * self.max_dist or point[0] > max(n_points) or point[0] < min(n_points) or point[1] > max(e_points) or point[1] < min(e_points):
        return False 
        break
      else:
        continue 
    return True 
  
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

