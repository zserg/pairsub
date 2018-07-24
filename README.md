# pairsubs
This script allows you to dowload a pair of different language subtitles for a movie from [opensubtitles.org](www.opensubtitles.org). You can take a parallel text and practice you translation skill that will help you to learn a foreign language.
All subtitles you've downloaded are stored on the disk and can be used later in the learning process.
# How to use
```python
import pairsubs

# initialise subtitles database
db = pairsubs.SubDb()

# Take a whole URL of some movie from www.imdb.com and
# download subtitles from opensubtitles.org
sub = db.download("https://www.imdb.com/title/tt1480055/?ref_=ttep_ep1","rus", "eng")
#Downloading rus ...
#Downloading end ...

# start learning
db.learn(sub)

# Куда он ?!                                |
# - Церемония закончена.                    |
# - Но он ничего не сказал.                 |
# - Она ему понравилась?                    |
# - Поверьте мне, ваша Милость,             |
# если бы она ему не нравилась, мы бы       |
# знали.                                    |

Press 'Enter' (or 'q' + 'Enter' to quit)

# Куда он ?!                                |  Where is he going?!
# - Церемония закончена.                    |  - The ceremony is over.
# - Но он ничего не сказал.                 |  - But he didn't say anything.
# - Она ему понравилась?                    |  - Did he like her?
# - Поверьте мне, ваша Милость,             |  - Trust me, your Grace,
# если бы она ему не нравилась, мы бы       |  if he didn't like her,
# знали.                                    |  we'd know.
Press 'Enter' (or 'q' + 'Enter' to quit)
`

