#!/usr/bin/env python
import dbus
import gobject
import time
import datetime
import os
import shutil
import subprocess

MINSIZE = 2000000000
UBUNTU = "ubuntu-11.04-desktop-amd64.iso"
FEDORA = "Fedora-15-x86_64-Live-Desktop.iso"
runBackup = 0
backupFile = ""
email = ""

class InstallOnDevice:
	def __init__(self, obj, dev):
		while True:
			self.distro = raw_input("Would you like Ubuntu 11.04 (64 bit) or Fedora Core 15 (64 bit)? (U/f): ")
			if (self.distro == "" or self.distro == "u" or self.distro == "U"):
				self.distro = "ubuntu"
				break
			elif (self.distro == "f" or self.distro == "F"):
				self.distro = "fedora"
				break
			else:
				print "That is not a valid option. Please try again."
		self.Install(obj, self.distro)
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
			global runBackup
			while True:
				overwrite = raw_input("Device is not empty. Do you want to overwrite, backup, or cancel? (o/b/C): ")
				if (overwrite == "" or overwrite == "c" or overwrite == "C"):
					EjectDrive(dev)
					self.cont = False
					break
				elif (overwrite == "b" or overwrite == "B"):
					runBackup = 1
					self.cont = self.Backup(devFile, dev)
					break
				elif (overwrite == "o" or overwrite == "O"):
					#self.cont = self.Backup(devFile, dev)
					self.cont = True
					break
				else:
					print "Invalid input, please try again."
			if self.cont == True:
				InstallOnDevice(obj, dev)
		else:
			InstallOnDevice(obj, dev)

	def Backup(self, devFile, dev):
		global backupFile, email
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
