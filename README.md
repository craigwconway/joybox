# Joybox 
A digital jukebox concept utilizing small toys to control music selection and playback

## Pre-requisites

 - RaspberryPi 3 or 4, or compatible
 - PN532 module
 - Python 3 

 ## Configuration
  - Configure the pins on the NFC HAT to use `spi`
  - Use `raspi-config` to configure the pi for `i2c`

## Installation
 - Joybox project should be located at `/home/pi/joybox`
 - The following script installs Joybox as a user service:`./install.sh`

## Run
 - Run without installation with `./start.sh`
