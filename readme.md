LG TV AutoPlayer App

This app allows you to create an autoplay folder compatible with LG Commercial TVs that just plays one video file on a loop.  
I've only tested it on one TV - the [LG 43UR640S0TD](https://www.lg.com/au/business/information-display/commercial-tv/43ur640s0td/), but it *should* work on others.

The proper way to actually set these up with multiple videos and other assorted bits is to use the LG Simple Editor - however finding a download link for that is difficult! (You need to be signed up on the LG B2B Partner Portal).  The software for that is also clunky.

# Usage
The short version of how this works:
Open the program -> Select a video file -> select where you want to save the AutoPlay folder (usually to a USB Stick) to and hit the Generate button.

It will try to guess your USB Stick to save it to as well.

:::note[AI Warning]
The code is all AI Generated, but human verified with Gemini.
:::

# Dev Environment Setup
## Dev Setup (Mac)
```bash
cd /to/folder
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install opencv-python pillow pyinstaller
```

Test Run App
`python3 ./lg_autoplay_generator.py`

Build app file
`pyinstaller --noconsole --onedir --icon=icon.png -n "LG Autoplay Generator" lg_autoplay_generatorv3.py`


## Dev Setup (Windows)
```pwsh
winget install Python.Python.3.14
cd \to\folder
python -m venv .\venv
.\venv\Scripts\activate.bat
pip install opencv-python pillow pyinstaller
```

Test Run App
`python3 ./lg_autoplay_generator.py`

Build App
`pyinstaller --noconsole --icon=icon.ico ./lg_autoplay_generator.py`

You can build it on Windows with --onefile, but it got picked up by the Antivirus as potentially malicious.