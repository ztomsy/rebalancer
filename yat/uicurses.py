"""
Built on curses user interface for console, a hardware ANSI terminal, a Telnet or SSH client,
or similar which support:
 - Header bar
 - Footer bar
 - Simple table printing with colouring
 - Table header printing
 - Spark lines with built-in normalization of data

Check print_ui for current ui implementation
"""

import curses
from time import strftime, localtime
from random import randint
from yat.shared import Side, OType, TIFType


class uiCurses:

    # region Init and setup
    def __init__(self):
        # Load curses
        self.key_pressed = 0
        # Load ui_data
        self.header_str = 'Rebalancer'
        self.statusbar_str = 'Loading'
        self.index_data = [['NAME', 'PROVIDER', 'TOB ASK', 'TOB BID', 'MID', 'SPREAD', 'SPREAD%'],
                           ['-', '-', 0, 0, 0, 0, 0], ]
        self.portfolio_data = [['NAME', 'PROVIDER', 'BALANCE', 'BASEPRICE', 'CURRENT%', 'RECOMMEND%', 'DIF%'],
                               ['-', '-', 0, 0, 0, 0, 0], ]
        self.pctchange_data = [['NAME', 'PROVIDER', '1H%', '3H%', '12H%', '24H%', '72H%'],
                               ['-', '-', 0, 0, 0, 0, 0], ]
        self.portfolio_opt_data = [' ', ]
        self.screen_data = [' ', ]
        self.spark_data = {'': [randint(100, 140) for _ in range(10)], }
        self.block_vertical = [chr(x) for x in range(0x2581, 0x2589)]  # fill with ascii symbols
        self.block_horizontal = [chr(x) for x in range(0x258F, 0x2587, -1)]
        # Init curses screen
        try:
            self.stdscr = self.setup()
        except Exception as e:
            if str(e) == "setupterm: could not find terminal":
                self.stdscr = None
                self.teardown()
            else:
                self.stdscr = None
                self.teardown()
                print("Unexpected behaviour of STDOUT", str(e))

    def setup(self):
        """
         Sets environment up and creates main window

         :returns: the main window object
        """
        # setup the console
        mmask = curses.ALL_MOUSE_EVENTS  # for now accept all mouse events
        main = curses.initscr()  # get a window object
        y, x = main.getmaxyx()  # get size
        if y < 24 or x < 20:  # verify minimum size rqmts
            raise RuntimeError("Terminal must be at least 20 x 24")
        curses.noecho()  # turn off key echoing
        curses.cbreak()  # turn off key buffering
        curses.mousemask(mmask)  # accept mouse events
        self.init_colors()  # turn on and set color pallet
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
        if self.stdscr:
            self.stdscr.keypad(0)
            curses.nocbreak()
            curses.echo()
            curses.endwin()

    def init_colors(self):
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
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
    # endregion

    # region Curses screen printing
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

    def print_table_body(self, data: list, color_b: float = -0.09):
        for i in range(1, len(data)):
            for j in range(0, len(data[i])):
                if self.check_string_to_float(data[i][j]):
                    data_ij = float(data[i][j])
                    if data_ij >= color_b:
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

    @staticmethod
    def normalize_spark_data(d: list):
        """
        Normalize data to exact bound (0, 7)

        :param d: List to normailize
        :type d: list
        :return: normalized list
        :rtype: list
        """
        mean = (max(d) + min(d)) / 2
        d = [round((100 * (float(i) - mean) / mean), 2) for i in d]
        d = [round(x + abs(min(d)) + 1, 2) for x in d]
        d = [round(7 * x / max(d)) for x in d]
        return d

    def print_spark_lines(self, spark_data: dict):
        # Create mask to define if data is out of available container length
        nsd = {x: [0 if i in range(len(self.block_vertical)) else
                   1 for i in spark_data[x]] for x in spark_data.keys()}
        # Filter non null lists and normalize necessary spark_data
        nsd2 = {name: self.normalize_spark_data(spark_data[name]) if sum(spark_mask) != 0 else spark_data[name] for
                name, spark_mask in nsd.items()}
        # Iterate throw dict and print each item on new line
        for name, spark_data in nsd2.items():
            self.stdscr.addstr(f'{name:^10s}', curses.color_pair(3))
            for i, s in enumerate(spark_data):
                if i == 0:
                    self.stdscr.addstr(self.block_vertical[s], curses.color_pair(5))
                else:
                    if spark_data[i] > spark_data[i - 1]:
                        self.stdscr.addstr(self.block_vertical[s], curses.color_pair(3))
                    elif spark_data[i] == spark_data[i - 1]:
                        self.stdscr.addstr(self.block_vertical[s], curses.color_pair(5))
                    else:
                        self.stdscr.addstr(self.block_vertical[s], curses.color_pair(2))
            self.stdscr.addstr('\n')
    # endregion

    # region Update and Compose
    def push_data(self, statusbar_str: str = None, header_str: str = None,
                  index_data: list = None, portfolio_data: list = None,
                  pctchange_data: list = None, portfolio_opt_data: list = None,
                  screen_data: list = None):
        if header_str is not None: self.header_str = header_str
        if statusbar_str is not None: self.statusbar_str = statusbar_str
        if index_data is not None: self.index_data = index_data
        if portfolio_data is not None: self.portfolio_data = portfolio_data
        if pctchange_data is not None: self.pctchange_data = pctchange_data
        if portfolio_opt_data is not None: self.portfolio_opt_data = portfolio_opt_data
        if screen_data is not None: self.screen_data = screen_data

    def reload_ui(self, **kwargs):
        self.push_data(**kwargs)
        self.print_ui()

    def print_ui(self):
        try:
            # region Preparing
            # Clear the screen
            self.stdscr.clear()
            # Place the border
            # self.stdscr.attron(curses.color_pair(4))
            # self.stdscr.border(1)
            # self.stdscr.attroff(curses.color_pair(4))
            height, width = self.stdscr.getmaxyx()
            dash = '─' * (width - 1) + '\n'
            # endregion

            # region Header
            # Perform safe crop to avoid drawing problem
            header_string = self.header_str[:width - 1]
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

            # region Body
            # Index data header
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
            # Pctchange spark lines header
            self.stdscr.addstr(dash)
            self.print_table_header([['NAME', 'LAST EXCHANGE DATA', ], ])
            # Pctchange spark lines body
            self.stdscr.addstr(dash)
            self.print_spark_lines(self.spark_data)
            # Portfolio optimization settings and results
            self.stdscr.addstr(dash)
            self.print_screen(self.portfolio_opt_data)
            # Screen body
            self.stdscr.addstr(dash)
            self.print_screen(self.screen_data)
            # endregion

            # region Status bar
            # Prepare statusbar from provided message and other attributes
            statusbar_time_str = strftime("%H:%M:%S", localtime())
            statusbar_p_string = "Server time: {} | Status: {} | ".format(statusbar_time_str, self.statusbar_str)
            # Perform safe crop to avoid drawing problem
            statusbar_p_string = statusbar_p_string[:width - 1]
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
            print(strftime("%H:%M:%S", localtime()), self.statusbar_str)
    # endregion
