import curses
import curses.textpad as textpad

import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

class RegisterWindow():
	def __init__(self, stdscr):
		self.main_win = stdscr
		parent_height, parent_width = self.main_win.getmaxyx()
		self.height, self.width = 19, 60
		self.window = curses.newwin(self.height, self.width, int(parent_height / 2 - self.height / 2), int(parent_width / 2 - self.width / 2))
		self.window.box()
		self.window.attron(curses.A_BOLD)
		self.window.addstr(1, int(self.width / 2 - len("WhatsAPI") / 2), "WhatsAPI")
		self.window.attroff(curses.A_BOLD)
		self.window.addstr(2, int(self.width / 2 - len("Nice to meet you") / 2), "Nice to meet you")


		self.text_fields = [
			textpad.Textbox(self.window.derwin(1, self.width - 4, 5, 2)),
			textpad.Textbox(self.window.derwin(1, self.width - 4, 9, 2))
		]
		self.data = [None, None]

		self.focused = 0
		self.change_focus(self.focused)

	def loop(self):
		while True:
			self.change_focus(self.focused)
			if self.focused in [0, 1]:
				aux_focus = self.focused
				curses.curs_set(2)
				self.text_fields[aux_focus].edit(self._validate_enter)
				message = self.text_fields[aux_focus].gather()
				curses.curs_set(0)

				self.data[aux_focus] = str(message).strip()
			else:
				key = self.main_win.getch()
				if key in [curses.KEY_ENTER, 10, 13]:
					if self.focused == 2:
						response = requests.post(
							"https://localhost:5000/register",
							json={
								"username": self.data[0],
								"password": self.data[1]
							},
							verify=False
						)
						if response.status_code == 201:
							response = requests.post(
								"https://localhost:5000/login",
								json={
									"username": self.data[0],
									"password": self.data[1]
								},
								verify=False
							)
							return "", response.json()["access_token"]
						else:
							self.window.attron(curses.color_pair(1))
							error_msg = list(response.json()["error"].values())[0]
							if type(error_msg) == list:
								error_msg = error_msg[0]
							self.window.addstr(11, 2, f"{" " * (self.width - 4 - len(error_msg))}{error_msg}")
							self.window.attroff(curses.color_pair(1))

					elif self.focused == 3:
						return "Login"
					
					elif self.focused == 4:
						return "Exit"

				if key == curses.KEY_DOWN:
					self.focused = min(self.focused + 1, 4)
				elif key == curses.KEY_UP:
					self.focused = max(self.focused - 1, 0)


	def _draw_styled_text_box(self, label, y, x, height, width, is_focused):
		if not is_focused:
			self.window.attron(curses.A_DIM)
		
		textpad.rectangle(self.window, y, x, y + height, x + width)
		self.window.addstr(y, x + 1, label)

		if not is_focused:
			self.window.attroff(curses.A_DIM)

	def _draw_styled_text(self, label, y, x, is_focused):
		if is_focused:
			self.window.attron(curses.A_REVERSE)
		else:
			self.window.attron(curses.A_DIM)
		
		self.window.addstr(y, x, label)

		if is_focused:
			self.window.attroff(curses.A_REVERSE)
		else:
			self.window.attroff(curses.A_DIM)

	def _validate_enter(self, ch):
		if ch == curses.KEY_UP:
			self.focused = max(self.focused - 1, 0)
			return 7
		elif ch == curses.KEY_DOWN:
			self.focused = min(self.focused + 1, 4)
			return 7
		return ch

	def change_focus(self, index):
		self._draw_styled_text_box("Username (email)", 4, 1, 2, self.width - 3, index == 0)

		self._draw_styled_text_box("Password", 8, 1, 2, self.width - 3, index == 1)

		self._draw_styled_text("Register", 13, int(self.width / 2 - len("Register") / 2), index == 2)
		self._draw_styled_text("Already registered?", 15, int(self.width / 2 - len("Already registered?") / 2), index == 3)
		self._draw_styled_text("Exit", 17, int(self.width / 2 - len("Exit") / 2), index == 4)

		self.window.refresh()