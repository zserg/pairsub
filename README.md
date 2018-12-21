# pairsubs
This script allows you to dowload a pair of different language subtitles for a movie from [opensubtitles.org](www.opensubtitles.org). You can take a parallel text and practice you translation skill that will help you to learn a foreign language.
All subtitles you've downloaded are stored on the disk and can be used later in the learning process.

## Learning process
![Alt text](/images/pairsubs_show.gif "Image#1")
# Download subtitles
![Alt text](/images/pairsubs_search.gif "Image#1")
# List of subtitles
![Alt text](/images/pairsubs_list.gif "Image#1")
# Align the subtitles
![Alt text](/images/pairsubs_align.gif "Image#1")

## Requirements
python3

SRT processing library (https://github.com/cdown/srt)

urwid (Console user interface library)

## Installation (virtualenv)
```bash
# clone repo
git clone https://github.com/zserg/pairsubs.git
cd pairsubs

# create virtual environment
virtualenv -p python3 venv
. venv/bin/activate
pip install -r requirements.txt

# run app
python pairsubs.py
```
## Local subtitles database
The information about the all downloaded subtitles is stored in ~/.pairsubs/cache.json.
The subtitles files are stored in ~/.pairsubs/files/
.

