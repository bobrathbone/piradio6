#!/usr/bin/python
# 
# I2C class based upon Adafruit_I2C Class
# Used for Adafruit RGB plate
# $Id: i2c_class.py,v 1.2 2017/10/17 06:38:36 bob Exp $
# 
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import smbus
import re

class i2c :


	# Get the Raspberry pi bus number
	@staticmethod
	def getPiI2CBusNumber():
		# Gets the I2C bus number /dev/i2c#
		return 1 if i2c.getPiRevision() > 1 else 0

	# Get the Raspberry pi board version from /proc/cpuinfo
	@staticmethod
	def getPiRevision():
		revision = 1
		with open("/proc/cpuinfo") as f:
			cpuinfo = f.read()
		rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo).group(1)
		rev_int = int(rev_hex,16)
		if rev_int > 2:
			revision = 2
		return revision

 
	def __init__(self, address, busnum=1, debug=False):
		self.address = address
		self.busnum = busnum
		self.bus = smbus.SMBus(self.busnum); # Force I2C1 (512MB Pi's)
		self.debug = debug

	def reverseByteOrder(self, data):
		"Reverses the byte order of an int (16-bit) or long (32-bit) value"
		# Courtesy Vishal Sapre
		byteCount = len(hex(data)[2:].replace('L','')[::2])
		val			 = 0
		for i in range(byteCount):
			val		= (val << 8) | (data & 0xff)
			data >>= 8
		return val

	def errMsg(self):
		print "Error accessing 0x%02X: Check your I2C address" % self.address
		return -1

	def write8(self, reg, value):
		"Writes an 8-bit value to the specified register/address"
		try:
			self.bus.write_byte_data(self.address, reg, value)
			if self.debug:
				print "I2C: Wrote 0x%02X to register 0x%02X" % (value, reg)
		except IOError, err:
			return self.errMsg()

	def write16(self, reg, value):
		"Writes a 16-bit value to the specified register/address pair"
		try:
			self.bus.write_word_data(self.address, reg, value)
			if self.debug:
				print ("I2C: Wrote 0x%02X to register pair 0x%02X,0x%02X" %
				 (value, reg, reg+1))
		except IOError, err:
			return self.errMsg()

	def writeList(self, reg, list):
		"Writes an array of bytes using I2C format"
		try:
			if self.debug:
				print "I2C: Writing list to register 0x%02X:" % reg
				print list
			self.bus.write_i2c_block_data(self.address, reg, list)
		except IOError, err:
			return self.errMsg()

	def readList(self, reg, length):
		"Read a list of bytes from the I2C device"
		try:
			results = self.bus.read_i2c_block_data(self.address, reg, length)
			if self.debug:
				print ("I2C: Device 0x%02X returned the following from reg 0x%02X" %
				 (self.address, reg))
				print results
			return results
		except IOError, err:
			return self.errMsg()

	def readU8(self, reg):
		"Read an unsigned byte from the I2C device"
		try:
			result = self.bus.read_byte_data(self.address, reg)
			if self.debug:
				print ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
				 (self.address, result & 0xFF, reg))
			return result
		except IOError, err:
			return self.errMsg()

	def readS8(self, reg):
		"Reads a signed byte from the I2C device"
		try:
			result = self.bus.read_byte_data(self.address, reg)
			if result > 127: result -= 256
			if self.debug:
				print ("I2C: Device 0x%02X returned 0x%02X from reg 0x%02X" %
				 (self.address, result & 0xFF, reg))
			return result
		except IOError, err:
			return self.errMsg()

	def readU16(self, reg):
		"Reads an unsigned 16-bit value from the I2C device"
		try:
			hibyte = self.readU8(reg)
			lobyte = self.readU8(reg+1)
			result = (hibyte << 8) + lobyte
			if (self.debug):
				print "I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
			return result
		except IOError, err:
			return self.errMsg()

	def readS16(self, reg):
		"Reads a signed 16-bit value from the I2C device"
		try:
			hibyte = self.readS8(reg)
			lobyte = self.readU8(reg+1)
			result = (hibyte << 8) + lobyte
			if (self.debug):
				print "I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
			return result
		except IOError, err:
			return self.errMsg()

	def readU16Rev(self, reg):
		"Reads an unsigned 16-bit value from the I2C device with rev byte order"
		try:
			lobyte = self.readU8(reg)
			hibyte = self.readU8(reg+1)
			result = (hibyte << 8) + lobyte
			if (self.debug):
				print "I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
			return result
		except IOError, err:
			return self.errMsg()

	def readS16Rev(self, reg):
		"Reads a signed 16-bit value from the I2C device with rev byte order"
		try:
			lobyte = self.readS8(reg)
			hibyte = self.readU8(reg+1)
			result = (hibyte << 8) + lobyte
			if (self.debug):
				print "I2C: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
			return result
		except IOError, err:
			return self.errMsg()

if __name__ == '__main__':
	try:
		bus = i2c(address=0)
		print "Default I2C bus is accessible"
	except:
		print "Error accessing default I2C bus"

	print "Board revision ", i2c.getPiRevision()
