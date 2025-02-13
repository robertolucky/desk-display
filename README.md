# Desk Display E-Paper 

This project is designed to create a charming desk display that shows upcoming events alongside beautiful artwork. It changes the art daily and automatically adds a Google Calendar event each morning at 7 am, listing the painting's name and artist. There is a helper function to create an appropriate list of artworks using the API from the [Art institute of Chicago](https://api.artic.edu/docs/). The list provided as an example is for impressionism artworks.

Creating google events named "Display code:1" trigger a new art piece, while "Display code:2" displays a random photo from a personal image collection.

Functions from an existing project have been tweaked for an easy connection with Google Calendar.

To ensure that the `check_and_display.py` script runs every 2 minutes, add the following line to your crontab:

`
*/2 * * * * /usr/bin/python3 /home/roberto/desk-display/check_and_display.py >> /home/roberto/desk-display/routine.log 2>&
`

`
    10 */48 * * * rm /home/roberto/desk-display/routine.logrm 
`

And this in the sudo crontab:

`
    @reboot /usr/bin/python3 /home/roberto/desk-display/startup.py
`


---

## Original Project Information

The foundation for the Google Calendar connection comes from the [waveshare-epaper-display](https://github.com/mendhak/waveshare-epaper-display) project. This project provides a comprehensive guide on setting up a Raspberry Pi Zero WH with a Waveshare ePaper 7.5 Inch HAT to display various pieces of information including date, time, weather, and calendar entries. Also for the display driver I have used the [official waveshare repo](https://github.com/waveshareteam/e-Paper/tree/af4d8b49ccef5f8f5fb88e9a836b86bd3f0bbfe3)

### Acknowledgements

Special thanks to the contributors of the [waveshare-epaper-display](https://github.com/mendhak/waveshare-epaper-display) project for their detailed documentation and code which have been instrumental in the development of this project.

---

## Contributing

Contributions to enhance the functionality or aesthetics of the display are welcome. Please feel free to fork the repository and submit a pull request with your improvements.
