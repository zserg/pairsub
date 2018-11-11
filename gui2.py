import urwid
from random import randint
import pairsubs


def on_show_clicked(button):
    new_text = 'English text:\n'
    for i in range(randint(1, 20)):
        new_text += '{}: text\n'.format(i)
    right_text.set_text(new_text)

# import ipdb; ipdb.set_trace()
def init_gui():
    left_text = urwid.Text('', align='left')
    right_text = urwid.Text('', align='left')
    text = urwid.Columns((left_text, right_text))
    fill = urwid.Filler(text, 'top')
    box = urwid.LineBox(fill)

    show_button = urwid.Padding(urwid.Button('Show'), 'center', 8)

    # Control
    home_but = urwid.Padding(urwid.Button('Home'), 'center', 8)
    align_but = urwid.Padding(urwid.Button('Align'), 'center', 9)
    list_but = urwid.Padding(urwid.Button('List'), 'center', 8)
    search_but = urwid.Padding(urwid.Button('Search'), 'center', 10)
    ctrl_buttons = urwid.Columns(
       [home_but, align_but, list_but, search_but]
       )


    pile_of_buttons = urwid.Pile((show_button, urwid.Divider(top=1, bottom=1), ctrl_buttons))
    pile = urwid.Frame(box, footer=pile_of_buttons, focus_part='footer')

    urwid.connect_signal(show_button.original_widget, 'click', on_show_clicked)

    loop = urwid.MainLoop(pile)
    loop.run()


db = pairsubs.SubDb()



