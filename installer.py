#!/usr/bin/env python
import dbus, termios, sys, os, gobject, time, datetime, shutil, subprocess, fcntl 

TERMIOS = termios
MINSIZE = 2000000000
UBUNTU = "ubuntu-11.04-desktop-amd64.iso"
FEDORA = "Fedora-15-x86_64-Live-Desktop.iso"
KDSETLED = 0x4B32
SCR_LED = 0x01
NUM_LED = 0x02
CAP_LED = 0x04
ALL_LED = SCR_LED | NUM_LED | CAP_LED
NO_LED = 0
email = ""
fileExists = 0
backupFile = ""
console_fd = os.open('/dev/console', os.O_NOCTTY)

def getkey():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~TERMIOS.ICANON & ~TERMIOS.ECHO
        new[6][TERMIOS.VMIN] = 1
        new[6][TERMIOS.VTIME] = 0
        termios.tcsetattr(fd, TERMIOS.TCSANOW, new)
        c = None
        try:
                c = os.read(fd, 1)
        finally:
                termios.tcsetattr(fd, TERMIOS.TCSAFLUSH, old)
        return c

class InstallOnDevice:
	def __init__(self, obj, dev, devFile):
		cancel = 0
		runBackup = 0
		while True:
			if fileExists == 1 and runBackup == 0 and cancel == 0:
				fcntl.ioctl(console_fd, KDSETLED, ALL_LED)
				print "Would you like Ubuntu 11.04 (64 bit) or Fedora Core 15 (64 bit), or would you like to backup your device?"
				self.distro = getkey()
				if (self.distro == "" or self.distro == "u" or self.distro == "U"):
					self.Install(obj, "ubuntu")
					break
				elif (self.distro == "f" or self.distro == "F"):
					self.Install(obj, "fedora")
					break
				elif (self.distro == "b" or self.distro == "B"):
					runBackup = 1
					runBck = self.Backup(runBackup, devFile, dev)
					if not runBck:
						cancel = 1
				elif (self.distro == "c" or self.distro == "C"):
					break
				else:
					print "That is not a valid option. Please try again."
			if fileExists == 1 and runBackup == 1 and cancel == 0:
				print "Would you like Ubuntu 11.04 (64 bit) or Fedora Core 15 (64 bit)?"
				self.distro = getkey()
				if (self.distro == "" or self.distro == "u" or self.distro == "U"):
					self.Install(obj, "ubuntu")
					break
				elif (self.distro == "f" or self.distro == "F"):
					self.Install(obj, "fedora")
					break
				elif (self.distro == "c" or self.distro == "C"):
					break
				else:
					print "That is not a valid option. Please try again."

		#insert backup email code here.
		EjectDrive(dev)
		if backupFile != "":
			if runBackup == 0:
				print "Deleting unecessary backup file."
				#shutil.rmtree("./"+backupFile+"/")
		
	def Install(self, obj, distro):
		print "Beginning installation."
		if distro == "ubuntu":
			self.distFile = UBUNTU
		elif distro == "fedora":
			self.distFile = FEDORA
		subprocess.call(['unetbootin', 'rootcheck=no', 'method=diskimage', 'isofile='+os.getcwd()+'/'+self.distFile, 'installtype=USB', 'targetdrive='+obj, 'autoinstall=yes'])
		print "Installation complete."

	def Backup(self, runBackup, devFile, dev):
		global email
		global backupFile
		if runBackup == 1:
			email = raw_input("Enter your email address (your backup will be emailed to you, or a link to it will be provided): ")
			backupFile = email + str(datetime.datetime.now())
		else:
			backupFile = "JICBackup" + str(datetime.datetime.now())
		if os.path.isdir("./" + backupFile + "/"):
			print "Warning! Could not create backup. " ,
			if (runBackup == 1):
				print "Cancelling and ejecting drive..."
				EjectDrive(dev)
				return False
			else:
				print "Continuing anyway. All data will be permenantly lost in case of error."
				return True
		else:
			try:
				print "Starting backup..."
				shutil.copytree(devFile, "./" + backupFile + "/", True)
				print "Backup completed."
				return True
			except:
				print "Error! Backup could not complete. " ,
				if (runBackup == 1):
					print "Aborting and ejecting drive..."
					EjectDrive(dev)
					return False
				else:
					print "Continuing anyway. All data will be permenantly lost in case of error."
					return True



class CheckIfEmpty:
	def __init__(self, obj, dev):
		counter = 0
		while True:
			time.sleep(1)
			mtab = open('/etc/mtab', 'r')
			for line in mtab:
				if line.split(' ')[0] == obj:
					devFile = line.split(' ')[1]
			if not devFile:
				counter = counter + 1
			elif counter == 10:
				print "Could not get device's mounted directory"
				EjectDrive(dev)
				break
			else:
				break

		if os.listdir(devFile):
				global fileExists
				fileExists = 1
				InstallOnDevice(obj, dev, devFile)
		else:
			InstallOnDevice(obj, dev, devFile)

			

class EjectDrive:
	def __init__(self, dev):
		self.bus = dbus.SystemBus()
		self.obj = self.bus.get_object("org.freedesktop.UDisks", dev)
		self.iface = dbus.Interface(self.obj, 'org.freedesktop.UDisks.Device')
		self.iface.FilesystemUnmount([])
		self.props = dbus.Interface(self.obj, dbus.PROPERTIES_IFACE)
		self.drive = self.props.Get('org.freedesktop.UDisks.Device', "PartitionSlave")
		self.drive_obj = self.bus.get_object("org.freedesktop.UDisks", self.drive)
		self.drive_if = dbus.Interface(self.drive_obj, 'org.freedesktop.UDisks.Device')
		self.drive_if.DriveEject([])
		print "The device is now safe to remove."

class GetDeviceInfo:
	def __init__(self, dev):
		self.obj = dbus.SystemBus().get_object("org.freedesktop.UDisks", dev)
		self.props = dbus.Interface(self.obj, dbus.PROPERTIES_IFACE)
		self.File = self.props.Get('org.freedesktop.UDisks.Device', "DeviceFile")
		self.ReadOnly = self.props.Get('org.freedesktop.UDisks.Device', "DeviceIsReadOnly")
		self.Size = self.props.Get('org.freedesktop.UDisks.Device', "DeviceSize")
		if self.CheckInfo(self.ReadOnly, self.Size) == False:
			print "Device not capable of ISO install"
			EjectDrive(dev)
		else:
			CheckIfEmpty(self.File, dev)
	
	def CheckInfo(self, ro, s):
		if (ro != 0) or (s <= MINSIZE):
			return False
		else:
			return True

class DeviceAddedListener:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.ud_manager_obj = self.bus.get_object("org.freedesktop.UDisks", "/org/freedesktop/UDisks")
        self.ud_manager = dbus.Interface(self.ud_manager_obj, "org.freedesktop.UDisks")
        devices = self.ud_manager.get_dbus_method('EnumerateDevices')()
        self.ud_manager.connect_to_signal('DeviceAdded', self._added)
    def _added(self, dev):
        if (dev[len(dev)-1].isdigit()):
           GetDeviceInfo(dev)
	
if __name__ == '__main__':
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()
    DeviceAddedListener()
    loop.run()
