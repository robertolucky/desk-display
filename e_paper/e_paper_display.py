#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import logging
from e_paper.epd7in3f import EPD
import time
from PIL import Image,ImageDraw,ImageFont

#logging.basicConfig(level=logging.DEBUG)
def display_image(image_file=None):
  try:
    epd = EPD()   
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    # read bmp file 
    logging.info("2.read bmp file")
    Himage = Image.open(image_file)
    epd.display(epd.getbuffer(Himage))
    time.sleep(1)

    logging.info("Goto Sleep...")
    epd.sleep()
    return True

  except IOError as e:
    logging.info(e)
    return False


if __name__ == "__main__":
    # If the script is executed directly, display the default image
    display_image()
