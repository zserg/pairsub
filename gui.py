import urwid
import pairsubs


class AppBox(urwid.Frame):
    def __init__(self):
        self.state = 'show'
        self.left_text = urwid.Text('', align='left')
        self.right_text = urwid.Text('', align='left')

        c = urwid.Columns((self.left_text, self.right_text))
        self.app_box = urwid.LineBox(urwid.Filler(c, 'top'))
        self.app_but = urwid.Padding(urwid.Button('Show'), 'center', 8)
        super().__init__(self.app_box, footer=self.app_but, focus_part='footer')

        urwid.connect_signal(self.app_but.original_widget, 'click', self.button_on_click)

        self.subs = []
        self.get_subs()

    def get_subs(self):
        # import ipdb; ipdb.set_trace()
        self.subs = db.get_subs()
        text = '\n'.join([s.content for s in self.subs[0]])
        self.left_text.set_text(text)
        self.right_text.set_text('')

    def button_on_click(self, button):
        if self.state == 'show':
            text = '\n'.join([s.content for s in self.subs[1]])
            self.right_text.set_text(text)
            self.app_but.original_widget.set_label('Next')
            self.state = 'next'
        else:
            self.get_subs()
            self.app_but.original_widget.set_label('Show')
            self.state = 'show'


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


db = pairsubs.SubDb()

app = TopFrame(AppBox(), footer=CtrlButtons(), focus_part='body')
loop = urwid.MainLoop(app)
loop.run()




