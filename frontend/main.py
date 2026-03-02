import curses
import curses.textpad as textpad

from loginWindow import LoginWindow
from registerWindow import RegisterWindow

JWT = None

def main(stdscr):
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_RED, -1)
	curses.curs_set(0)
	stdscr.clear()
	stdscr.refresh()

	code = "Login"
	active_win = None
	
	while code != "Exit":
		stdscr.clear()
		stdscr.refresh()

		if code == "Login":
			active_win = LoginWindow(stdscr)
			code, JWT = active_win.loop()
		elif code == "Register":
			active_win = RegisterWindow(stdscr)
			code = active_win.loop()

		active_win.window.erase()
		active_win.window.refresh()
		del active_win
	
	
if __name__ == "__main__":
	curses.wrapper(main)

