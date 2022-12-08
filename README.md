# ADL_classes



Main classes

The script contains general classes to be used across different scripts.

#1 class: ADL_Read_XML - parsing paramteres from configuration XML file to each relevant script.

    Methods:
            - get_params(): return the XML parmeter depending on the user input
            
#2 class: ADL_EXIF - extracting GPS data from image(including .HEIC format from Apple) into decimal format, return a tuple with the N and E coordinates.
                   - Important to install both: pyheif and exifread libraries.
                     !pip install pyheif
                     !pip install exifread
                     
    Methods:
            - read_exif(): extracting the GPS data, return a tuple of the coordinates
            
#3 class: ADL_gh - creating an object for a new gh. 

    Methods:
            - setup(): save every image coordinate as a class variable of corner, in case there are only 3 images, the 4th coordinate is approximatelly     
                       created.
            - check_if_in_gh(self, point): check if a point coordinate is in the gh.
            - line_mapping(self, lines_cor): sort and save a dictionary variable into the object which contain every line and its coordinate
            
#4 class: ADL_img_gh - check in which gh the image is coming from, wether current grower or other grower

    Methods:

    

    
