# XP Workshop Part 2

## Setup

The instructions are given for Debian-based Linux distros and for
Windows. For Mac the Linux instructions should work after Python and
virtualenv are installed.

First you need to install Python and some tools and libraries. Do this once.

* Install Python 3 and virtualenv
  * Linux
    * Run: `sudo apt install python3 virtualenv`
  * Windows
    * Download Python 3 from here: https://www.python.org/downloads/
    * Install it and make sure it gets installed on the PATH.
    * Open a command line prompt and run: `pip install virtualenv`
* Create a virtual environment
  * Open a Terminal window and cd into the `xp-workshop-part-2` directory.
  * Linux:
    * `virtualenv --python=python3 env`
  * Windows:
    * `virtualenv env`
* Activate the virtual environment
  * Linux:
    * `source env/bin/activate`
  * Windows:
    * `env/Scripts/activate.bat`
  * As long as (env) is displayed in your terminal, the `python` and `pip` commands will use the versions in the virtual environment.
* Install dependencies into the virtual environment
  * `pip install -r requirements.txt`

## Run the code

* Whenever you start a new terminal, first activate the virtual environment
  * Linux:
    * `source env/bin/activate`
  * Windows:
    * `env/Scripts/activate.bat`
* Then run the client like this: `python client.py`

## Development

Use https://github.com/khalim19/gimp-plugin-export-layers to export the layers of `map.xcf` into the `map` directory.
