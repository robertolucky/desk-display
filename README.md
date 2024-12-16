# Desk Display E-Paper 

This project is inspired by the desire to have a small, yet aesthetically pleasing display on the desk that not only provides useful information about upcoming events but also serves as a piece of art. The display is designed to show a work of art when it is not being used to display information.

For the integration with Google Calendar, we have repurposed functions from an existing project. 

To ensure that the `check_and_display.py` script runs every 2 minutes, add the following line to your crontab:
*/2 * * * * /usr/bin/python3 /home/roberto/desk-display/check_and_display.py >> /home/roberto/desk-display/routine.log 2>&1
0 */48 * * * rm /home/roberto/desk-display/routine.logrm 

---

## Original Project Information

The foundation for the Google Calendar connection comes from the [waveshare-epaper-display](https://github.com/mendhak/waveshare-epaper-display) project. This project provides a comprehensive guide on setting up a Raspberry Pi Zero WH with a Waveshare ePaper 7.5 Inch HAT to display various pieces of information including date, time, weather, and calendar entries.

### Acknowledgements

Special thanks to the contributors of the [waveshare-epaper-display](https://github.com/mendhak/waveshare-epaper-display) project for their detailed documentation and code which have been instrumental in the development of this project.

---

## Contributing

Contributions to enhance the functionality or aesthetics of the display are welcome. Please feel free to fork the repository and submit a pull request with your improvements.
