# Caption Fletcher

A simple app to create and edit captions for your image datasets, intended for use with machine learning (e.g. training Stable Diffusion LoRAs).

You can load a folder of images, and all captions stored in .txt files will be loaded too. If there's no caption for any of the images it uses BLIP to analyse them and automatically add the caption.

## Features

- Fast and simple to use
- Missing captions automatically get added using BLIP
- Need to edit an image? Copy & paste the image buffer directly!
- Send an image and its caption to trash

![Caption Fletcher Screenshot](https://github.com/MakingMadness/caption-fletcher/blob/main/images/screenshot.png?raw=true)

## Installation

### Linux

```
git clone https://github.com/MakingMadness/caption-fletcher.git
cd caption-fletcher
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows

```
git clone https://github.com/MakingMadness/caption-fletcher.git
cd caption-fletcher
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Usage

From within the caption-fletcher directory:

### Linux

```
source venv/bin/activate
python caption-fletcher.py
```

### Windows

```
venv\Scripts\activate.bat
python caption-fletcher.py
```
