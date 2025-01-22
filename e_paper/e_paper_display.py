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

def display_text(text):
  try:
    epd = EPD()   
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    font40 = ImageFont.truetype(os.path.join(os.path.realpath(__file__), 'Font.ttc'), 40)
    Himage = Image.new('RGB', (epd.width, epd.height), epd.WHITE)  # 255: clear the frame
    draw = ImageDraw.Draw(Himage)
    draw.text((5, 20), text, font = font40, fill = epd.BLUE)
    epd.display(epd.getbuffer(Himage))
    time.sleep(3)
    return True

  except IOError as e:
    logging.info(e)
    return False


if __name__ == "__main__":
    # If the script is executed directly, display the default image
    display_image()
