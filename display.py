#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import pango

class showWindow:
	def delete_event(self, widget, event, data=None):
		gtk.main_quit()
		return False

	def __init__(self):
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		
		self.window.set_title("PLUG Device Installer")
		self.window.connect("delete_event", self.delete_event)
		self.window.set_border_width(0)

		self.mainBox = gtk.VBox(False, 0)
		self.window.add(self.mainBox)

		self.Header = gtk.Label("PLUG Device Installer")
		self.Header.modify_font(pango.FontDescription("sans 40"))
		self.mainBox.pack_start(self.Header, True, True, 0)
		self.Header.show()

		self.mainBox.show()
		self.window.show()

def main():
	gtk.main()

if __name__=="__main__":
	run = showWindow()
	main()
