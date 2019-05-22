"""
Ugly table-style interface
"""

import curses

class UI_curses:

    def __init__(self):
        # Load curses
        self.key_pressed = 0
        # Load ui_data
        self.header_str = 'Rebalancer'
        self.statusbar_str = " | Status: Loading | "
        self.index_data = [['NAME', 'PROVIDER', 'TOB ASK', 'TOB BID', 'MID', 'SPREAD', 'SPREAD%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'BASEPRICE', 'MIN%', 'CURRENT%', 'MAX%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        # Init curses screen
        try:
            self.stdscr = curses.initscr()
            curses.cbreak()
            self.stdscr.keypad(1)
            curses.echo()
            self.stdscr.scrollok(1)
            # Start colors in curses
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        except:
            print('-=UI does not work=-')

    def reload_ui(self, **kwargs):
        self.push_data(**kwargs)
        self.print_ui()

    def push_data(self, statusbar_str: str = None, header_str: str = None,
                  index_data: list = None, portfolio_data: list = None, pctchange_data: list = None):
        if header_str is not None: self.header_str = header_str
        if statusbar_str is not None: self.statusbar_str = statusbar_str
        if index_data is not None: self.index_data = index_data
        if portfolio_data is not None: self.portfolio_data = portfolio_data
        if pctchange_data is not None: self.pctchange_data = pctchange_data

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
                    if data_ij >= 0:
                        self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(3))
                    else:
                        self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(2))
                else:
                    self.stdscr.addstr("{:^10s}".format(str(data[i][j])), curses.color_pair(3))
            self.stdscr.addstr("\n")

    def print_ui(self):
        try:
            self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            dash = '─' * (width - 3) + '\n'
            # Header
            if width > len(self.header_str) + 1:
                self.stdscr.addstr(0, int(width / 2 - 5), self.header_str)
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
            # Render status bar
            if width > len(self.statusbar_str) + 1:
                self.stdscr.addstr(height - 1, 0, self.statusbar_str)
            # Refresh the screen
            self.stdscr.refresh()

        except:
            pass
