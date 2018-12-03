import urwid
import io

SUBS_CNT_FOR_ALIGN = 12


class SubsLogStream(io.StringIO):
    """Stream for logging into a Text box.
        Attributes:
            `box` (`urwid.Text`): text widget to print into
            `loop` (`urwid.MainLoop`): main loop to redraw
        """
    def __init__(self, box, loop):
        self.box = box
        self.loop = loop

    def write(self, message):
        """Writes message into Text box."""
        self.box.set_text(self.box.text+message)
        self.loop.draw_screen()


class AppBox(urwid.Frame):
    """Frame to show subtitles text."""
    def __init__(self, db, sub_id=None):
        # import ipdb; ipdb.set_trace()
        self.db = db
        self.sub_id = sub_id
        self.random = False if sub_id else True
        self.state = 'show'

        self.title = urwid.Text('Title', align='left')
        self.left_text = urwid.Text('', align='left')
        self.right_text = urwid.Text('', align='left')
        c = urwid.Columns((self.left_text, self.right_text))
        pile = urwid.Pile([self.title, urwid.Divider(' '), c])
        self.app_box = urwid.LineBox(urwid.Filler(pile, 'top'))
        self.app_but = urwid.Padding(urwid.Button('Show'), 'center', 8)
        super().__init__(self.app_box, footer=self.app_but, focus_part='footer')

        urwid.connect_signal(self.app_but.original_widget, 'click', self.button_on_click)

        self.subs = []
        self.get_subs()

    def get_subs(self):
        sub_id = None if self.random else self.sub_id
        self.sub_id, self.subs = self.db.get_subs(sub_id)
        if self.subs:
            text = '\n'.join([s.content for s in self.subs[0]])
            self.left_text.set_text(text)
            self.right_text.set_text('')
            sub_title = '{} ({}, {})'.format(
                    self.db.data[self.sub_id]['subs'][0]['MovieName'],
                    self.db.data[self.sub_id]['subs'][0]['SubLanguageID'],
                    self.db.data[self.sub_id]['subs'][1]['SubLanguageID']
                    )
            self.title.set_text(sub_title)

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

    def get_sub_id(self):
        return self.sub_id


class SearchBox(urwid.Frame):
    """Frame to search subtitles."""
    def __init__(self, db):
        self.db = db
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
            self.log.set_text('')
            url = self.url.get_edit_text()
            lang1 = self.lang1.get_edit_text()
            lang2 = self.lang2.get_edit_text()
            if url and lang1 and lang2:
                self.db.download(url, lang1, lang2)
        else:
            return self.focus.keypress(size, key)

    def get_sub_id(self):
        return None


class SubsListBox(urwid.Frame):
    """Frame to show a list of subtitles."""
    def __init__(self, db, top_frame):
        self.db = db
        self.top_frame = top_frame
        self.subs_list = list(self.db.data.items())
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
        if key == 'down' and self.get_focus_path() == ['body', len(self.subs.body)-1]:
            self.focus_position = 'footer'
        elif key == 'up' and self.focus_position == 'footer' and self.subs.body:
            self.set_focus_path(['body', 0])
        elif key == 'enter' and self.focus_position == 'footer':
            self.delete_subs()
            self.__init__(self.db, self.top_frame)
            self.focus_position = 'body'
            self.focus_position = 'footer'
        elif key == 'enter' and self.focus_position == 'body':
            idx = self.get_focus_path()[1]  # ['body', 0]
            sub_id = self.subs_list[idx][0]
            self.top_frame.set_show_mode(None, sub_id)
        else:
            return self.focus.keypress(size, key)

    def delete_subs(self):
        # import ipdb; ipdb.set_trace()
        for i, e in enumerate(self.subs.body):
            if e.get_state():
                self.db.delete(self.subs_list[i][0])

    def get_sub_id(self):
        return None


class SubsAlignBox(urwid.Frame):
    """Frame to align subtitles."""
    def __init__(self, db, top_frame, sub_id):
        self.db = db
        self.top_frame = top_frame
        self.subs_id = sub_id
        self.subs = self.db.get_subs_to_align(sub_id, SUBS_CNT_FOR_ALIGN)

        bg_lt = []
        bg_rt = []
        bg_lb = []
        bg_rb = []
        self.left_top = [urwid.RadioButton(bg_lt, x.content) for x in self.subs[0]]
        self.right_top = [urwid.RadioButton(bg_rt, x.content) for x in self.subs[1]]
        self.left_bot = [urwid.RadioButton(bg_lb, x.content) for x in self.subs[2]]
        self.right_bot = [urwid.RadioButton(bg_rb, x.content) for x in self.subs[3]]

        left_top_box = urwid.ListBox(urwid.SimpleFocusListWalker(self.left_top))
        right_top_box = urwid.ListBox(urwid.SimpleFocusListWalker(self.right_top))
        left_bot_box = urwid.ListBox(urwid.SimpleFocusListWalker(self.left_bot))
        right_bot_box = urwid.ListBox(urwid.SimpleFocusListWalker(self.right_bot))

        c_top = urwid.Columns([left_top_box, right_top_box])
        c_bot = urwid.Columns([left_bot_box, right_bot_box])

        p = urwid.Pile([c_top, urwid.Filler(urwid.Divider('-'), 'middle'), c_bot])
        self.app_box = urwid.LineBox(p)
        self.app_but = urwid.Padding(urwid.Button('Align'), 'center', 10)
        super().__init__(self.app_box, footer=self.app_but, focus_part='body')

    def sub_format(self, sub):
        return '{} ({}, {})'.format(
                sub['subs'][0]['MovieName'],
                sub['subs'][0]['SubLanguageID'],
                sub['subs'][1]['SubLanguageID'],
                )

    def keypress(self, size, key):
        if key == 'down' and self.get_focus_path() == ['body', 2, 0, len(self.subs[0])-1]:
            self.focus_position = 'footer'
        elif key == 'down' and self.get_focus_path() == ['body', 2, 1, len(self.subs[1])-1]:
            self.focus_position = 'footer'
        elif key == 'up' and self.focus_position == 'footer':
            self.focus_position = 'body'
        elif key == 'enter' and self.focus_position == 'footer':
            self.db.align_subs(self.subs_id,
                               self.subs[0][self._find_rbutton(self.left_top)].index,
                               self.subs[1][self._find_rbutton(self.right_top)].index,
                               self.subs[2][self._find_rbutton(self.left_bot)].index,
                               self.subs[3][self._find_rbutton(self.right_bot)].index)
            self.top_frame.set_show_mode(None, self.subs_id)
        else:
            return self.focus.keypress(size, key)

    def _find_rbutton(self, a):
        for e in enumerate(a):
            if e[1].state is True:
                return e[0]

    def get_sub_id(self):
        return None


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
    """Top application frame."""
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = db
        self.search_box = SearchBox(self.db)
        # self.app_box = AppBox()

        urwid.connect_signal(self.contents['footer'][0].search_but, 'click', self.set_search_mode)
        urwid.connect_signal(self.contents['footer'][0].home_but, 'click', self.set_show_mode)
        urwid.connect_signal(self.contents['footer'][0].list_but, 'click', self.set_list_mode)
        urwid.connect_signal(self.contents['footer'][0].align_but, 'click', self.set_align_mode)

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

    def set_show_mode(self, button, sub_id=None):
        body = AppBox(self.db, sub_id)
        self.contents['body'] = (body, body.options())
        self.focus_position = 'body'

    def set_list_mode(self, button):
        body = SubsListBox(self.db, self)
        self.contents['body'] = (body, body.options())

    def set_align_mode(self, button):
        sub_id = self.contents['body'][0].get_sub_id()
        if sub_id:
            body = SubsAlignBox(self.db, self, sub_id)
            self.contents['body'] = (body, body.options())


class App:
    """Main application."""
    def __init__(self, db):
        self.db = db
        self.top = TopFrame(self.db, AppBox(self.db), footer=CtrlButtons(), focus_part='footer')
        self.loop = urwid.MainLoop(self.top)

    def get_search_box(self):
        return self.top.search_box.log

    def get_loop(self):
        return self.loop

    def run(self):
        self.loop.run()




