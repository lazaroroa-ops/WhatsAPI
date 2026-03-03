import curses
import curses.textpad as textpad
import time

import requests
from requests.auth import HTTPBasicAuth
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

JWT = None
API_KEY = None

class MainWindow():
	#def __init__(self, stdscr, JWT_, API_KEY_):
	def __init__(self, stdscr, JWT_):
		global JWT, API_KEY
		JWT = JWT_
		#API_KEY = API_KEY_
		self.stdscr = stdscr
		parent_height, parent_width = self.stdscr.getmaxyx()
		self.height = parent_height
		self.width = parent_width
		self.window = curses.newwin(self.height, self.width, 0, 0)

		self.options_width = 20
		self.options_win = SelectorWindow(self.stdscr, self.window, self.height - 2, self.options_width, 1, 1)

		self.window.refresh()

	def loop(self):
		code = "Main"
		active_win_code = None
		active_win = None

		while code != "Exit":
			self.stdscr.refresh()
			if code == "Main":
				self.options_win.is_focused = True
				self.options_win.change_full_focus()
				code = self.options_win.loop()
				self.options_win.is_focused = False
				self.options_win.change_full_focus()
			elif code == "Inbox":
				if active_win_code != code:
					if active_win:
						active_win.clear()
					active_win = InboxWindow(self.stdscr, self.window, self.height - 2, self.width - self.options_width - 2, 1, self.options_width + 1)
					active_win_code = code
				active_win.change_full_focus(True)
				code = active_win.loop()
				active_win.change_full_focus(False)
			elif code == "New":
				if active_win_code != code:
					if active_win:
						active_win.clear()
					active_win = NewMailWindow(self.stdscr, self.window, self.height - 2, self.width - self.options_width - 2, 1, self.options_width + 1)
					active_win_code = code
				active_win.change_full_focus(True)
				code = active_win.loop()
				active_win.change_full_focus(False)
			elif code == "Options":
				if active_win_code != code:
					if active_win:
						active_win.clear()
					active_win = OptionsWindow(self.stdscr, self.window, self.height - 2, self.width - self.options_width - 2, 1, self.options_width + 1)
					active_win_code = code
				active_win.change_full_focus(True)
				code = active_win.loop()
				active_win.change_full_focus(False)

		return "Exit"


class SelectorWindow():
	def __init__(self, stdscr, main_win, height, width, y, x):
		self.stdscr = stdscr
		self.main_win = main_win
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
		self.window.box()

		self.window.addstr(1, 2, "Inbox")
		self.window.addstr(3, 2, "Write new")
		self.window.addstr(5, 2, "Options")
		self.window.addstr(self.height - 2, 2, "Exit")
		
		self.is_focused = True

		self.focused = 0
		self.change_focus(self.focused)

	def loop(self):
		while True:
			self.change_focus(self.focused)
			key = self.stdscr.getch()

			if key == curses.KEY_DOWN:
				self.focused = min(self.focused + 1, 3)
			elif key == curses.KEY_UP:
				self.focused = max(self.focused - 1, 0)

			elif key in [curses.KEY_ENTER, 10, 13]:
				if self.focused == 0:
					return "Inbox"
				elif self.focused == 1:
					return "New"
				elif self.focused == 2:
					return "Options"
				elif self.focused == 3:
					return "Exit"

	def change_full_focus(self):
		if not self.is_focused:
			self.window.attron(curses.A_DIM)
		self.window.box()
		if not self.is_focused:
			self.window.attroff(curses.A_DIM)
		self.window.refresh()


	def change_focus(self, index):
		rows = [1, 3, 5, self.height - 2]
		for row in rows:
			self.window.chgat(row, 1, self.width - 2, curses.A_NORMAL)
			self.window.chgat(row, 1, self.width - 2, curses.A_DIM)
		
		self.window.chgat(rows[index], 1, self.width - 2, curses.A_NORMAL)
		self.window.chgat(rows[index], 1, self.width - 2, curses.A_REVERSE)

		self.window.refresh()


class InboxWindow():
	def __init__(self, stdscr, main_win, height, width, y, x):
		self.stdscr = stdscr
		self.main_win = main_win
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
		self.window.box()
		self.window.addstr(0, 1, "Inbox")
		self.window.refresh()

		self.mail = []
		self.is_focused = True
		self.focused = 0

	def fetch_mails(self):
		#debug
		response = requests.get(
			"https://localhost:5000/messages",
			headers={
				'Authorization': f'Bearer {JWT}1',
				#'Api-Key': API_KEY,
				'Content-type': 'aplication/json'
			},
			verify=False
		)
		self.mail = [
			{"id": 1, "source": "test@test.es", "subject": "This is a test."},
			{"id": 2, "source": "alberto@gmail.com", "subject": "This is another test."}
		]

		# FETCH MAIL
		if self.mail:
			self.window.addnstr(2, 2, "Source", 30)
			self.window.addnstr(2, 34, "Subject", self.width - 36)

			self.window.addstr(3, 2, f"{"=" * 30}")
			self.window.addstr(3, 34, f"{"=" * (self.width - 36)}")

			for m, row in zip(self.mail, range(5, 5 + 2 * len(self.mail), 2)):
				self.window.addnstr(row, 2, m["source"], 30)
				self.window.addnstr(row, 34, m["subject"], self.width - 36)

		# if not mail
		else:
			self.window.addstr(int(self.height / 2), int(self.width / 2 - len("Wow, such empty") / 2), "Wow, such empty")
		
		self.window.refresh()

	def fetch_mail(self, id):
		# debug
		mail = {
			"id": 1,
			"source": "test@test.es",
			"subject": "This is a test.",
			"body": "Hello.\n\nThis is a test.\n\nGoodbye!"
		}

		mail_window = self.window.derwin(self.height - 2, self.width - 2, 1, 1)
		mail_window.erase()
		mail_window.box()

		textpad.rectangle(mail_window, 2, 1, 4, self.width - 4)
		mail_window.addstr(2, 2, "Source")

		mail_window.addnstr(3, 2, mail["source"], self.width - 4 - 2)

		textpad.rectangle(mail_window, 6, 1, 8, self.width - 4)
		mail_window.addstr(6, 2, "Subject")

		mail_window.addnstr(7, 2, mail["subject"], self.width - 4 - 2)

		textpad.rectangle(mail_window, 10, 1, self.height - 5, self.width - 4)
		mail_window.addstr(10, 2, "Body")
		
		row = 0
		col = 0
		lim_row = self.height - 5 - 10 - 2
		lim_col =  self.width - 4 - 1 - 2
		for ch in mail["body"]:
			if col > lim_col:
				row += 1
				col = 0
			if row > lim_row:
				break
			if ch == "\n":
				row += 1
				col = 0
			else:
				mail_window.addch(row + 11, col + 2, ch)
				col += 1

		mail_window.refresh()

		while True:
			key = self.stdscr.getch()
			if key == 27:
				break
		
		mail_window.erase()
		mail_window.refresh()

	def loop(self):
		self.is_focused = True
		self.focused = 0

		self.fetch_mails()

		while True:
			self.change_focus(self.focused)
			key = self.stdscr.getch()

			if key == curses.KEY_DOWN:
				if self.mail:
					self.focused = min(self.focused + 1, len(self.mail) - 1)
			elif key == curses.KEY_UP:
				if self.mail:
					self.focused = max(self.focused - 1, 0)

			elif key in [curses.KEY_ENTER, 10, 13]:
				if self.mail:
					self.fetch_mail(self.focused)
					self.fetch_mails()

			elif key == 27:		# escape key
				self.change_focus(-1)
				return "Main"

	def change_full_focus(self, is_focused):
		if not is_focused:
			self.window.attron(curses.A_DIM)

		self.window.box()
		self.window.addstr(0, 1, "Inbox")

		if self.mail:
			self.window.addnstr(2, 2, "Source", 30)
			self.window.addnstr(2, 34, "Subject", self.width - 36)

			self.window.addstr(3, 2, f"{"=" * 30}")
			self.window.addstr(3, 34, f"{"=" * (self.width - 36)}")

		if not is_focused:
			self.window.attroff(curses.A_DIM)

		self.window.refresh()

	def change_focus(self, index):
		if self.mail:
			rows = range(5, 5 + 2 * len(self.mail), 2)

			for row in rows:
				self.window.chgat(row, 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(row, 1, self.width - 2, curses.A_DIM)
			
			if index >= 0:
				self.window.chgat(rows[index], 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(rows[index], 1, self.width - 2, curses.A_REVERSE)
		
			self.window.refresh()

	def clear(self):
		self.window.erase()
		self.window.refresh()


class NewMailWindow():
	def __init__(self, stdscr, main_win, height, width, y, x):
		self.stdscr = stdscr
		self.main_win = main_win
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
		
		self.window.attron(curses.A_DIM)
		self.window.addstr(self.height - 3, int(self.width / 2 - len("Send") / 2), "Send")
		self.window.attroff(curses.A_DIM)

		self.body_win = self.window.derwin(self.height - 16, self.width - 4, 11, 2)

		self.text_fields = [
			textpad.Textbox(self.window.derwin(1, self.width - 4, 3, 2)),
			textpad.Textbox(self.window.derwin(1, self.width - 4, 7, 2)),
			textpad.Textbox(self.body_win)
		]
		self.data = [None, None, None]

		self.is_focused = True
		self.focused = 0
		self.change_focus(self.focused)

		self.window.refresh()

	def loop(self):
		self.is_focused = True
		self.focused = 0
		while True:
			self.change_focus(self.focused)

			if self.focused in [0, 1, 2]:
				aux_focus = self.focused
				curses.curs_set(2)
				if self.focused == 2:
					self.body_win.move(0, 0)
				self.text_fields[aux_focus].edit(self._validate_enter)
				message = self.text_fields[aux_focus].gather()
				curses.curs_set(0)

				self.data[aux_focus] = str(message).strip()

				if self.focused == -1:
					self.change_focus(-1)
					return "Main"
			else:
				key = self.stdscr.getch()

				if key == curses.KEY_DOWN:
					self.focused = min(self.focused + 1, 3)
				elif key == curses.KEY_UP:
					self.focused = max(self.focused - 1, 0)

				elif key == 27:		# escape key
					self.change_focus(-1)
					return "Main"

				elif key in [curses.KEY_ENTER, 10, 13]:
					pass # SEND MAIL

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
			self.focused = min(self.focused + 1, 3)
			return 7
		elif ch == 27:
			self.focused = -1
			return 7
		return ch

	def change_full_focus(self, is_focused):
		if not is_focused:
			self.window.attron(curses.A_DIM)
		self.window.box()
		self.window.addstr(0, 1, "New mail")
		if not is_focused:
			self.window.attroff(curses.A_DIM)
		self.window.refresh()

	def change_focus(self, index):
		self._draw_styled_text_box("Destination", 2, 1, 2, self.width - 3, index == 0)
		self._draw_styled_text_box("Subject", 6, 1, 2, self.width - 3, index == 1)
		self._draw_styled_text_box("Body", 10, 1, self.height - 15, self.width - 3, index == 2)

		if index == 3:
			self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
			self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_REVERSE)
		else:
			self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
			self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_DIM)

		self.window.refresh()

	def clear(self):
		self.window.erase()
		self.window.refresh()


class OptionsWindow():
	def __init__(self, stdscr, main_win, height, width, y, x):
		self.stdscr = stdscr
		self.main_win = main_win
		self.height = height
		self.width = width
		self.y = y
		self.x = x
		self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
		self.window.box()
		self.window.addstr(0, 1, "Options")

		self.window.addstr(2, 2, "Change password")
		self.window.addstr(4, 2, "Delete account")
		
		self.is_focused = True

		self.focused = 0
		self.change_focus(self.focused)

		self.window.refresh()

	def loop(self):
		self.focused = 0
		self.is_focused = True

		while True:
			self.change_focus(self.focused)
			key = self.stdscr.getch()

			if key == curses.KEY_DOWN:
				self.focused = min(self.focused + 1, 1)
			elif key == curses.KEY_UP:
				self.focused = max(self.focused - 1, 0)

			elif key == 27:		# escape key
				self.change_focus(-1)
				return "Main"

			elif key in [curses.KEY_ENTER, 10, 13]:
				if self.focused == 0:
					active_win = self.change_password(self.stdscr, self.window, 14, self.width - 20, 9, 10)
					active_win.loop()
					active_win.clear()
				if self.focused == 1:
					active_win = self.delete_account(self.stdscr, self.window, 10, self.width - 20, 9, 10)
					if active_win.loop():
						return "Exit"

	def change_full_focus(self, is_focused):
		if not is_focused:
			self.window.attron(curses.A_DIM)
		self.window.box()
		self.window.addstr(0, 1, "Options")
		if not is_focused:
			self.window.attroff(curses.A_DIM)
		self.window.refresh()

	def change_focus(self, index):
		rows = [2, 4]
		for row in rows:
			self.window.chgat(row, 1, self.width - 2, curses.A_NORMAL)
			self.window.chgat(row, 1, self.width - 2, curses.A_DIM)
		
		if index >= 0:
			self.window.chgat(rows[index], 1, self.width - 2, curses.A_NORMAL)
			self.window.chgat(rows[index], 1, self.width - 2, curses.A_REVERSE)

		self.window.refresh()

	def clear(self):
		self.window.erase()
		self.window.refresh()


	class change_password():
		def __init__(self, stdscr, main_win, height, width, y, x):
			self.stdscr = stdscr
			self.main_win = main_win
			self.height = height
			self.width = width
			self.y = y
			self.x = x
			self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
			self.window.box()

			self.text_fields = [
				textpad.Textbox(self.window.derwin(1, self.width - 4, 3, 2)),
				textpad.Textbox(self.window.derwin(1, self.width - 4, 7, 2))
			]

			self.window.addstr(11, int(self.width / 2 - len("Confirm") / 2), "Confirm")

			self.data = [None, None]

			self.focused = 0
			self.change_focus(self.focused)

			self.window.refresh()

		def loop(self):
			self.focused = 0
			while True:
				self.change_focus(self.focused)

				if self.focused in [0, 1]:
					aux_focus = self.focused
					curses.curs_set(2)
					self.text_fields[aux_focus].edit(self._validate_enter)
					message = self.text_fields[aux_focus].gather()
					curses.curs_set(0)

					self.data[aux_focus] = str(message).strip()

					if self.focused == -1:
						return 
				else:
					key = self.stdscr.getch()

					if key == curses.KEY_DOWN:
						self.focused = min(self.focused + 1, 2)
					elif key == curses.KEY_UP:
						self.focused = max(self.focused - 1, 0)

					elif key == 27:		# escape key
						return

					elif key in [curses.KEY_ENTER, 10, 13]:
						pass # CHANGE PASSWORD

		def _validate_enter(self, ch):
			if ch == curses.KEY_UP:
				self.focused = max(self.focused - 1, 0)
				return 7
			elif ch == curses.KEY_DOWN:
				self.focused = min(self.focused + 1, 2)
				return 7
			elif ch == 27:
				self.focused = -1
				return 7
			return ch

		def change_focus(self, index):
			if index != 0:
				self.window.attron(curses.A_DIM)
			textpad.rectangle(self.window, 2, 1, 4, self.width - 2)
			self.window.addstr(2, 2, "Old password")
			if index != 0:
				self.window.attroff(curses.A_DIM)

			if index != 1:
				self.window.attron(curses.A_DIM)
			textpad.rectangle(self.window, 6, 1, 8, self.width - 2)
			self.window.addstr(6, 2, "New password")
			if index != 1:
				self.window.attroff(curses.A_DIM)

			if index == 2:
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_REVERSE)
			else:
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_DIM)

			self.window.refresh()
		
		def clear(self):
			self.window.erase()
			self.window.refresh()


	class delete_account():
		def __init__(self, stdscr, main_win, height, width, y, x):
			self.stdscr = stdscr
			self.main_win = main_win
			self.height = height
			self.width = width
			self.y = y
			self.x = x
			self.window = self.main_win.derwin(self.height, self.width, self.y, self.x)
			self.window.box()
			textpad.rectangle(self.window, 2, 1, 4, self.width - 2)
			self.pass_field = textpad.Textbox(self.window.derwin(1, self.width - 4, 3, 2))
			self.window.addstr(7, int(self.width / 2 - len("DELETE") / 2), "DELETE")

			self.focused = 0

		def loop(self):
			password = None

			while True:
				self.change_focus(self.focused)

				if self.focused == 0:
					curses.curs_set(2)
					self.pass_field.edit(self._validate_enter)
					message = self.pass_field.gather()
					curses.curs_set(0)

					password = str(message).strip()

					if self.focused == -1:
						self.clear()
						return False

				elif self.focused == 1:
					key = self.stdscr.getch()

					if key == curses.KEY_UP:
						self.focused = 0

					elif key == 27:		# escape key
						self.clear()
						return False

					elif key in [curses.KEY_ENTER, 10, 13]:
						pass # DELETE

		def _validate_enter(self, ch):
			if ch == curses.KEY_DOWN:
				self.focused = 1
				return 7
			elif ch == 27:
				self.focused = -1
				return 7
			return ch

		def change_focus(self, index):
			if index != 0:
				self.window.attron(curses.A_DIM)

			textpad.rectangle(self.window, 2, 1, 4, self.width - 2)
			self.window.addstr(2, 2, "Confirm your password")

			if index != 0:
				self.window.attroff(curses.A_DIM)

			if index == 0:
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_DIM)
			else:
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_NORMAL)
				self.window.chgat(self.height - 3, 1, self.width - 2, curses.A_REVERSE)

			self.window.refresh()
		
		def clear(self):
			self.window.erase()
			self.window.refresh()