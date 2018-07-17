# pairsub
This script allows you to dowload a pair of different language subtitles for a movie from [opensubtitles.org](www.opensubtitles.org). You can take a parallel text and practice you translation skill that will help you to learn a foreign language
# How to use
```python
import pairsubs

# downloads a pair of subtitles by IMDB id
s = pairsubs.SubPair.download("926084","rus", "eng")
#Downloading rus ...
#Downloading end ...

# start learning,  20 - duration of a fragment (seconds)
pairsubs.learn(s, 20)

# Вы до сих пор...                          |             
# Лейтенант Дэн.                            |                 
# Посмотри на меня.                         |             
# Что мне теперь делать?                    |                            
# Что мне теперь делать?                    |                            
# Press Enter...

# Вы до сих пор...                          |  Y-You still
# Лейтенант Дэн.                            |  Lieutenant Dan.
# Посмотри на меня.                         |  Look at me.
# Что мне теперь делать?                    |  What am I going to do now?
# Что мне теперь делать?                    |  What am I going to do now?
# Press Enter...

```
You can also search subtittels by a whole URL from www.imdb.com
```python
s = pairsubs.SubPair.download("https://www.imdb.com/title/tt1480055/?ref_=ttep_ep1","rus", "eng")
```

