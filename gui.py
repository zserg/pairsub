import urwid
from random import randint
import pairsubs


def on_show_clicked(button):
    new_text = 'English text:\n'
    for i in range(randint(1, 20)):
        new_text += '{}: text\n'.format(i)
    right_text.set_text(new_text)

# import ipdb; ipdb.set_trace()



class AppBox(urwid.Frame):
    def __init__(self):
        self.left_text = urwid.Text('', align='left')
        self.right_text = urwid.Text('', align='left')
        c = urwid.Columns((self.left_text, self.right_text))
        self.app_box = urwid.LineBox(urwid.Filler(c, 'top'))
        self.app_but = urwid.Padding(urwid.Button('Show'), 'center', 8)
        super().__init__(self.app_box, footer=self.app_but, focus_part='footer')


class SearchBox(urwid.Frame):
    def __init__(self):
        self.left_text = urwid.Text('', align='left')
        self.right_text = urwid.Text('', align='left')
        c = urwid.Columns((self.left_text, self.right_text))
        self.app_box = urwid.LineBox(urwid.Filler(c, 'top'))
        self.app_but = urwid.Padding(urwid.Button('Search'), 'center', 10)
        super().__init__(self.app_box, footer=self.app_but, focus_part='footer')


class CtrlButtons(urwid.Columns):
    def __init__(self):
        self.home_but = urwid.Padding(urwid.Button('Home'), 'center', 8)
        self.align_but = urwid.Padding(urwid.Button('Align'), 'center', 9)
        self.list_but = urwid.Padding(urwid.Button('List'), 'center', 8)
        self.search_but = urwid.Padding(urwid.Button('Search'), 'center', 10)
        super().__init__((
            self.home_but,
            self.align_but,
            self.list_but,
            self.search_but
            ))


class TopFrame(urwid.Frame):
    def keypress(self, size, key):
        if key == 'up':
            self.focus_position = 'body'
        elif key == 'down':
            self.focus_position = 'footer'
        else:
            return self.focus.keypress(size, key)


app = TopFrame(AppBox(), footer=CtrlButtons(), focus_part='footer')
loop = urwid.MainLoop(app)
loop.run()

db = pairsubs.SubDb()



