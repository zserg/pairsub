import urwid
import io
import pairsubs
import logging
import time

class SubsLogStream(io.StringIO):
    ''' Stream for logging into a Text box'''

    def __init__(self, box):
        '''
        Args:
            box (urwid.Text): text widget to print into
        '''
        self.box = box

    def write(self, message):
        '''
        Args:
            message (str): message top print
        '''
        self.box.set_text(self.box.text+message)

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
        if self.subs:
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

        self.url = urwid.Edit('URL:  ')
        self.lang1 = urwid.Edit('Lang #1:  ')
        self.lang2 = urwid.Edit('Lang #2:  ')
        self.log = urwid.Text('')
        s = [
             urwid.LineBox(self.url),
             urwid.LineBox(self.lang1),
             urwid.LineBox(self.lang2),
             self.log
             ]
        self.subs = urwid.ListBox(urwid.SimpleFocusListWalker(s))

        self.app_box = urwid.LineBox(self.subs)
        self.app_but = urwid.Padding(urwid.Button('Search'), 'center', 10)
        super().__init__(self.app_box, footer=self.app_but, focus_part='body')

    def keypress(self, size, key):
        if key == 'down' and self.get_focus_path() == ['body', 2]:
            self.focus_position = 'footer'
        elif key == 'up' and self.focus_position == 'footer':
            self.set_focus_path(['body', 2])
        elif key == 'enter' and self.focus_position == 'footer':
            # import ipdb; ipdb.set_trace()
            self.log.set_text('')
            db.download(self.url.get_edit_text(), self.lang1.get_edit_text(), self.lang2.get_edit_text())
        else:
            return self.focus.keypress(size, key)


class SubsListBox(urwid.Frame):
    def __init__(self):
        self.subs_list = list(db.data.items())
        # import ipdb; ipdb.set_trace()
        s = [urwid.CheckBox(self.sub_format(x[1])) for x in self.subs_list]
        self.subs = urwid.ListBox(urwid.SimpleFocusListWalker(s))
        self.app_box = urwid.LineBox(self.subs)
        self.app_but = urwid.Padding(urwid.Button('Delete'), 'center', 10)
        super().__init__(self.app_box, footer=self.app_but, focus_part='footer')

    def sub_format(self, sub):
        return '{} ({}, {})'.format(
                sub['subs'][0]['MovieName'],
                sub['subs'][0]['SubLanguageID'],
                sub['subs'][1]['SubLanguageID'],
                )

    def keypress(self, size, key):
        # import ipdb; ipdb.set_trace()
        if key == 'down' and self.get_focus_path() == ['body', len(self.subs.body)-1]:
            self.focus_position = 'footer'
        elif key == 'up' and self.focus_position == 'footer' and self.subs.body:
            self.set_focus_path(['body', 0])
        elif key == 'enter' and self.focus_position == 'footer':
            self.delete_subs()
            self.__init__()
            self.focus_position = 'body'
            self.focus_position = 'footer'
        else:
            return self.focus.keypress(size, key)

    def delete_subs(self):
        for i, e in enumerate(self.subs.body):
            if e.get_state():
                db.delete(self.subs_list[i][0])




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

        self.search_box = SearchBox()
        self.app_box = AppBox()

        urwid.connect_signal(self.contents['footer'][0].search_but, 'click', self.set_search_mode)
        urwid.connect_signal(self.contents['footer'][0].home_but, 'click', self.set_show_mode)
        urwid.connect_signal(self.contents['footer'][0].list_but, 'click', self.set_list_mode)

    def keypress(self, size, key):
        if key == 'up' and self.focus_position == 'footer':
            self.focus_position = 'body'
        elif key == 'down' and self.get_focus_path() == ['body', 'footer']:
            self.focus_position = 'footer'
        else:
            return self.focus.keypress(size, key)

    def set_search_mode(self, button):
        body = self.search_box
        body.log.set_text('')
        self.contents['body'] = (body, body.options())

    def set_show_mode(self, button):
        body = self.app_box
        self.contents['body'] = (body, body.options())

    def set_list_mode(self, button):
        body = SubsListBox()
        self.contents['body'] = (body, body.options())

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

db = pairsubs.SubDb()
app = TopFrame(AppBox(), footer=CtrlButtons(), focus_part='footer')

log_box = app.search_box.log
log_handler = logging.StreamHandler(SubsLogStream(log_box))
logging.getLogger('pairsubs').addHandler(log_handler)
logging.getLogger('pairsubs').propagate = False

loop = urwid.MainLoop(app)
loop.run()




