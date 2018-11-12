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
        self.home_but = urwid.Button('Home')
        self.align_but = urwid.Button('Align')
        self.list_but = urwid.Button('List')
        self.search_but = urwid.Button('Search')
        super().__init__((
            urwid.Padding(self.home_but, 'center', 8),
            urwid.Padding(self.align_but, 'center', 9),
            urwid.Padding(self.list_but, 'center', 8),
            urwid.Padding(self.search_but, 'center', 10),
            ))


class TopFrame(urwid.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # import ipdb; ipdb.set_trace()
        urwid.connect_signal(self.contents['footer'][0].search_but, 'click', self.set_search_mode)
        urwid.connect_signal(self.contents['footer'][0].home_but, 'click', self.set_show_mode)

    def keypress(self, size, key):
        if key == 'up':
            self.focus_position = 'body'
        elif key == 'down':
            self.focus_position = 'footer'
        else:
            return self.focus.keypress(size, key)

    def set_search_mode(self, button):
        body = SearchBox()
        self.contents['body'] = (body, body.options())

    def set_show_mode(self, button):
        body = AppBox()
        self.contents['body'] = (body, body.options())


db = pairsubs.SubDb()

app = TopFrame(AppBox(), footer=CtrlButtons(), focus_part='body')
loop = urwid.MainLoop(app)
loop.run()




