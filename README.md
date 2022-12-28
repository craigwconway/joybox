# Joybox 
A physical jukebox concept utilizing small toys to control music selection and playback
![Joybox demo](/assets/joybox.jpg)

## Hardware
 - RaspberryPi 4, SD card, power supply
 - PN532 module with pins configured to use `spi`
 - Speaker (wired or Bluetooth)
 - RFID tags (~$20 for 50 on Amazon)
 - Assorted small toys

## Setup
 - Use the `raspi-config` utility to enable `spi` under Peripherals
 - Clone the Joybox project at `/home/pi/joybox`
 - Install as a user service: `install.sh`
 - Run without installation: `start.sh`

## App
 - Open the webapp at `http://raspberrypi.local:8050/` 
 - Associate RFID tags to YouTube and Spotify playlists
 - Control playback