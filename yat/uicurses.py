"""
Ugly curses interface, support header, statusbar and
simple table drawing with colouring and table header.

Check print_ui for current ui implementation
"""

import curses
from time import strftime, localtime
from yat.shared import Side, OType, TIFType


class uiCurses:

    def __init__(self):
        # Load curses
        self.key_pressed = 0
        # Load ui_data
        self.header_str = 'Rebalancer'
        self.statusbar_str = 'Loading'
        self.index_data = [['NAME', 'PROVIDER', 'TOB ASK', 'TOB BID', 'MID', 'SPREAD', 'SPREAD%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'BASEPRICE', 'MIN%', 'CURRENT%', 'MAX%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.screen_data = [' ', ]
        # Init curses screen
        try:
            self.stdscr = self.setup()
            # self.stdscr = curses.initscr()
            # curses.cbreak()
            # self.stdscr.keypad(1)
            # curses.echo()
            # self.stdscr.scrollok(1)
            # self.initcolors()
        except Exception as e:
            # TODO Discover new exception behavior if STDOUT is not a TTY.
            # print(type(e).__name__, e.args, str(e))
            pass

    def setup(self):
        """
         Sets environment up and creates main window
         :returns: the main window object
        """
        # setup the console
        mmask = curses.ALL_MOUSE_EVENTS  # for now accept all mouse events
        main = curses.initscr()  # get a window object
        y, x = main.getmaxyx()  # get size
        if y < 24 or x < 80:  # verify minimum size rqmts
            raise RuntimeError("Terminal must be at least 80 x 24")
        curses.noecho()  # turn off key echoing
        curses.cbreak()  # turn off key buffering
        curses.mousemask(mmask)  # accept mouse events
        self.initcolors()  # turn on and set color pallet
        main.keypad(1)  # let curses handle multibyte special keys
        main.scrollok(1)
        curses.curs_set(0)  # hide the cursor
        main.refresh()  # and show everything
        return main

    def teardown(self):
        """
         Returns console to normal state
        """
        # tear down the console
        curses.nocbreak()
        if self.stdscr:
            self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def initcolors(self):
        """
        Initialize color pallet
        """
        curses.start_color()
        if not curses.has_colors():
            raise RuntimeError("Sorry. Terminal does not support colors")
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def reload_ui(self, **kwargs):
        self.push_data(**kwargs)
        self.print_ui()

    def push_data(self, statusbar_str: str = None, header_str: str = None,
                  index_data: list = None, portfolio_data: list = None,
                  pctchange_data: list = None, screen_data: list = None):
        if header_str is not None: self.header_str = header_str
        if statusbar_str is not None: self.statusbar_str = statusbar_str
        if index_data is not None: self.index_data = index_data
        if portfolio_data is not None: self.portfolio_data = portfolio_data
        if pctchange_data is not None: self.pctchange_data = pctchange_data
        if screen_data is not None: self.screen_data = screen_data

    def print_table_header(self, data):
        for i in range(0, len(data[0])):
            self.stdscr.addstr('{:^10s}'.format(str(data[0][i])), curses.color_pair(1))
        self.stdscr.addstr("\n")

    @staticmethod
    def check_string_to_float(s):
        try:
            float(s)
            return True
        except:
            return False

    def print_table_body(self, data: list):
        for i in range(1, len(data)):
            for j in range(0, len(data[i])):
                if self.check_string_to_float(data[i][j]):
                    data_ij = float(data[i][j])
                    if data_ij >= -0.05:
                        self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(3))
                    else:
                        self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(2))
                else:
                    self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(3))
            self.stdscr.addstr("\n")

    def print_screen(self, data: list):
        for s in data:
            self.stdscr.addstr(str(s))
            self.stdscr.addstr("\n")

    def print_ui(self):
        try:
            # region Preparing
            self.stdscr.clear()  # erase everything
            # TODO Add border
            # self.stdscr.attron(curses.color_pair(4))  # make the border red
            # self.stdscr.border(1)  # place the border
            # self.stdscr.attroff(curses.color_pair(4))  # turn off the red
            # self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            dash = '─' * (width - 1) + '\n'
            # Perform safe crop to avoid drawing problem
            header_string = self.header_str[:width-1]
            status_bar_string = self.statusbar_str[:width-1]
            # endregion

            # region Header
            # Turning on attributes for Header
            self.stdscr.attron(curses.color_pair(4))
            self.stdscr.attron(curses.A_BOLD)
            # Draw Header
            if width > len(self.header_str) + 1:
                self.stdscr.addstr(0, 0, " " * (width - 1))
                self.stdscr.addstr(0, int((width / 2) - (len(header_string) / 2)), header_string)
            # Turning off attributes for Header
            self.stdscr.attroff(curses.color_pair(4))
            self.stdscr.attroff(curses.A_BOLD)
            # endregion

            #region Body
            # Portfolio data
            self.stdscr.addstr(1, 0, dash)
            self.print_table_header(self.index_data)
            # Index data body
            self.stdscr.addstr(dash)
            self.print_table_body(self.index_data)
            # Balance data header
            self.stdscr.addstr(dash)
            self.print_table_header(self.portfolio_data)
            # Balance body
            self.stdscr.addstr(dash)
            self.print_table_body(self.portfolio_data)
            # Pctchange data header
            self.stdscr.addstr(dash)
            self.print_table_header(self.pctchange_data)
            # Pctchange body
            self.stdscr.addstr(dash)
            self.print_table_body(self.pctchange_data)
            # Screen body
            self.stdscr.addstr(dash)
            self.print_screen(self.screen_data)
            #endregion

            # region Status bar
            # Prepare statusbar from provided message and other attributes
            statusbar_time_str = strftime("%H:%M:%S", localtime())
            statusbar_p_string = "Server time: {} | Status: {} | ".format(statusbar_time_str, self.statusbar_str)
            # Turning on attributes for status bar
            self.stdscr.attron(curses.color_pair(4))
            self.stdscr.attron(curses.A_BOLD)
            # Render status bar
            if width > len(statusbar_p_string) + 1:
                self.stdscr.addstr(height - 1, 0, statusbar_p_string)
                self.stdscr.addstr(height - 1, len(statusbar_p_string), " " * (width - len(statusbar_p_string) - 1))
            # Turning off attributes for Header
            self.stdscr.attroff(curses.color_pair(4))
            self.stdscr.attroff(curses.A_BOLD)
            # endregion
            # Refresh the screen
            self.stdscr.refresh()

        except Exception as e:
            pass
