#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
import logging
import epd7in3f
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)
def display_image(image_file=None):
  try:
    logging.info("epd7in3f Demo")

    epd = epd7in3f.EPD()   
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    # If no image file is provided, use the default one
    if image_file is None:
       image_file = os.path.join(picdir, 'processed_artwork.bmp')

    # read bmp file 
    logging.info("2.read bmp file")
    Himage = Image.open(image_file)
    epd.display(epd.getbuffer(Himage))
    time.sleep(1)

    logging.info("Goto Sleep...")
    epd.sleep()

  except IOError as e:
    logging.info(e)

  except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd7in3f.epdconfig.module_exit(cleanup=True)
    exit()

if __name__ == "__main__":
    # If the script is executed directly, display the default image
    display_image()
