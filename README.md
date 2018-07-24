# pairsubs
This script allows you to dowload a pair of different language subtitles for a movie from [opensubtitles.org](www.opensubtitles.org). You can take a parallel text and practice you translation skill that will help you to learn a foreign language.
All subtitles you've downloaded are stored on the disk and can be used later in the learning process.
# How to use (from Python)
```python
>>> import pairsubs
>>> db = pairsubs.SubDb()
>>> sub = db.download("https://www.imdb.com/title/tt1480055/?ref_=ttep_ep1","rus", "eng")
```
```
Downloading rus ...
Downloading end ...
```
```python
>>> db.learn(sub)
```
```
А вы серьёзно подготовились.              |
Мистер Локвуд очень серьёзно              |
относиться к своей гуманитарной миссии.   |
Где погонщик рапторов?                    |
Специалист по поведению животных.         |
Оуэн Грэйди.                              |
Эй, Оуэн. Кен Уитли.                      |
А ты, знаменитый белый охотник?           |
Да, я руководитель экспедиции.            |
                                          |
                                          |
Press 'Enter' (or 'q' + 'Enter' to quit)

А вы серьёзно подготовились.              |  What kind of operation
Мистер Локвуд очень серьёзно              |  you've got going on here?
относиться к своей гуманитарной миссии.   |  Mr. Lockwood takes his humanitarian
Где погонщик рапторов?                    |  efforts very seriously.
Специалист по поведению животных.         |  Where's the raptor wrangler?
Оуэн Грэйди.                              |  Animal behaviourist. Owen Grady.
Эй, Оуэн. Кен Уитли.                      |  Hey, Owen. Ken Wheatley.
А ты, знаменитый белый охотник?           |  And you're our,
Да, я руководитель экспедиции.            |  great white hunter?
                                          |  Yes, I'm the expedition's
                                          |  facilitator.

Press 'Enter' (or 'q' + 'Enter' to quit)
```



