
import usb
import struct
import array
import logging
from max2837 import Max2837
from si5351c import SI5351C
from rffc5071 import RFFC5071

logging.basicConfig()
logger = logging.getLogger('HackRf Core')
logger.setLevel(logging.DEBUG)

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def byte_array_to_string(array):
	''' This is used to convert a array() of bytes into a string '''
	return "".join(map(chr, array))

def get_serial(serial_array):
		result = ''
		for byte in serial_array:
			result += '%0.2X' % byte
		return result

def print_bytes(struct):
	print ("".join(["/x%02x" % ord(c) for c in struct])) #


HackRfVendorRequest = enum(
	HACKRF_VENDOR_REQUEST_SET_TRANSCEIVER_MODE = 1,
	HACKRF_VENDOR_REQUEST_MAX2837_WRITE = 2,
	HACKRF_VENDOR_REQUEST_MAX2837_READ = 3,
	HACKRF_VENDOR_REQUEST_SI5351C_WRITE = 4,
	HACKRF_VENDOR_REQUEST_SI5351C_READ = 5,
	HACKRF_VENDOR_REQUEST_SAMPLE_RATE_SET = 6,
	HACKRF_VENDOR_REQUEST_BASEBAND_FILTER_BANDWIDTH_SET = 7,
	HACKRF_VENDOR_REQUEST_RFFC5071_WRITE = 8,
	HACKRF_VENDOR_REQUEST_RFFC5071_READ = 9,
	HACKRF_VENDOR_REQUEST_SPIFLASH_ERASE = 10,
	HACKRF_VENDOR_REQUEST_SPIFLASH_WRITE = 11,
	HACKRF_VENDOR_REQUEST_SPIFLASH_READ = 12,
	HACKRF_VENDOR_REQUEST_CPLD_WRITE = 13,
	HACKRF_VENDOR_REQUEST_BOARD_ID_READ = 14,
	HACKRF_VENDOR_REQUEST_VERSION_STRING_READ = 15,
	HACKRF_VENDOR_REQUEST_SET_FREQ = 16,
	HACKRF_VENDOR_REQUEST_AMP_ENABLE = 17,
	HACKRF_VENDOR_REQUEST_BOARD_PARTID_SERIALNO_READ = 18,
	HACKRF_VENDOR_REQUEST_SET_LNA_GAIN = 19,
	HACKRF_VENDOR_REQUEST_SET_VGA_GAIN = 20,
	HACKRF_VENDOR_REQUEST_SET_TXVGA_GAIN = 21,
	#NULL = 22, // was set_if_freq
	USB_VENDOR_REQUEST_SET_ANTENNA_ENABLE = 23,
	USB_VENDOR_REQUEST_SET_FREQ_EXPLICIT = 24,
	USB_VENDOR_REQUEST_READ_WCID = 25,
	USB_VENDOR_REQUEST_INIT_SWEEP = 26,
	USB_VENDOR_REQUEST_OPERACAKE_GET_BOARDS = 27,
	USB_VENDOR_REQUEST_OPERACAKE_SET_PORTS = 28,
	USB_VENDOR_REQUEST_SET_HW_SYNC_MODE = 29,
	USB_VENDOR_REQUEST_RESET = 30,
	USB_VENDOR_REQUEST_OPERACAKE_SET_RANGES = 31,
	USB_VENDOR_REQUEST_SET_CLKOUT_ENABLE = 32,
	USB_VENDOR_REQUEST_SPIFLASH_STATUS = 33,
	USB_VENDOR_REQUEST_SPIFLASH_CLEAR_STATUS = 34,
	USB_VENDOR_REQUEST_OPERACAKE_GPIO_TEST = 35,
	USB_VENDOR_REQUEST_CPLD_CHECKSUM = 36,
	USB_VENDOR_REQUEST_SET_UI_ENABLE = 37,
	USB_VENDOR_REQUEST_OPERACAKE_SET_MODE = 38,
	USB_VENDOR_REQUEST_OPERACAKE_GET_MODE = 39,
	USB_VENDOR_REQUEST_OPERACAKE_SET_DWELL_TIMES = 40,
	USB_VENDOR_REQUEST_GET_M0_STATE = 41,
	USB_VENDOR_REQUEST_SET_TX_UNDERRUN_LIMIT = 42,
	USB_VENDOR_REQUEST_SET_RX_OVERRUN_LIMIT = 43,
	USB_VENDOR_REQUEST_GET_CLKIN_STATUS = 44,
	USB_VENDOR_REQUEST_READ_BOARD_REV = 45,
	USB_VENDOR_REQUEST_READ_SUPPORTED_PLATFORM = 46,
	USB_VENDOR_REQUEST_SET_LEDS = 47,
	USB_VENDOR_REQUEST_SET_GPIO = 48,)

HackRfConstants = enum(
	HACKRF_DEVICE_OUT = 0x40,
	HACKRF_DEVICE_IN = 0xC0,
	HACKRF_USB_VID = 0x1d50,
	HACKRF_USB_PID = 0x6089,
	HACKRF_SUCCESS = 0,
	#Python defaults to returning none 
	HACKRF_ERROR = None)

HackRfTranscieverMode = enum(
	HACKRF_TRANSCEIVER_MODE_OFF = 0,
	HACKRF_TRANSCEIVER_MODE_RECEIVE = 1,
	HACKRF_TRANSCEIVER_MODE_TRANSMIT = 2)

FREQ_ONE_MHZ = 1000 * 1000

class HackRf():
	''' This is the base object for the HackRf Device, and interaction with it '''
	__JELLYBEAN__ = 'Jellybean'
	__JAWBREAKER__ = 'Jawbreaker'
	__HACK_RF_ONE__ = 'HackRF One'
	NAME_LIST = [__JELLYBEAN__, __JAWBREAKER__, __HACK_RF_ONE__]

	def __init__(self):
		self.name = None
		self.device = None
		self.max2837 = None
		self.si5351c = None
		self.rffc5071 = None

	def setup(self):
		''' This is to setup a hackrf device '''
		self.device = usb.core.find(idVendor=HackRfConstants.HACKRF_USB_VID, idProduct=HackRfConstants.HACKRF_USB_PID)
		if self.device == None:
			logger.error('No Hack Rf Detected!')
		else:
			self.device.set_configuration()
			self.max2837 = Max2837(self)
			self.si5351c = SI5351C(self)
			self.rffc5071 = RFFC5071(self)
			board_id = self.get_board_id()
			if isinstance( board_id, (int)):
				self.name = self.NAME_LIST[board_id]
				logger.debug('Successfully setup HackRf device')

	def get_board_id(self):
		''' Gets the board's id number '''
		board_id = self.device.ctrl_transfer(
			HackRfConstants.HACKRF_DEVICE_IN,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_BOARD_ID_READ,
			0,
			0,
			2)[0]
		if board_id < 1:
			logger.error('Failed to get Board Id')
		else:
			logger.debug('Successfully got Board Id')
			return board_id

	def get_version_string(self):
		''' Returns the version string from the hackrf board '''
		version = byte_array_to_string(self.device.ctrl_transfer(
			HackRfConstants.HACKRF_DEVICE_IN,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_VERSION_STRING_READ,
			0,
			0,
			100))
		if len(version) < 0:
			logger.error('Failed to get Version String')
		else:
			logger.debug('Successfully got HackRf Version String')
			return version

	def get_board_serial_number(self):
		''' Gets the board serial number '''
		number = self.device.ctrl_transfer(
			HackRfConstants.HACKRF_DEVICE_IN,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_BOARD_PARTID_SERIALNO_READ,
			0,
			0,
			100)
		if len(number) > 12:
			#Only get relevant bytes
			serial = number[8:]
			#Get bytes in the right order
			serial.reverse()

			serial_one = get_serial(serial[12:])
			serial_two = get_serial(serial[8:12])
			serial_three = get_serial(serial[4:8])
			serial_four = get_serial(serial[:4])
			logger.debug('Successfully got the HackRf Board Serial Number')
			return (serial_one, serial_two, serial_three, serial_four)
		else:
			logger.error('Failed to get Serial Number')

	def set_baseband_filter_bandwidth(self, bandwidth_hz):
		''' 
		Set baseband filter bandwidth in MHz.
			Possible values: 1.75/2.5/3.5/5/5.5/6/7/8/9/10/12/14/15/20/24/28MHz,
			default < sample_rate_hz. 
		'''
		if isinstance( bandwidth_hz, (int)):
			result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
				HackRfVendorRequest.HACKRF_VENDOR_REQUEST_BASEBAND_FILTER_BANDWIDTH_SET,
				bandwidth_hz & 0xffff,
				bandwidth_hz >> 16)
			if result != 0:
				logger.error('Failed to set Baseband Filter Bandwidth with value [%d]', bandwidth_hz)
			else:
				logger.debug('Successfully set Baseband Filter Bandwidth with value [%d]', bandwidth_hz)
				return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Failed to set Baseband Filter Bandwidth, bandwidth_hz should be of type INT or LONG')

	def set_frequency(self, freq_hz):
		''' Sets the frequency in hz '''
		if isinstance( freq_hz, ( int)):
			l_freq_mhz = int(freq_hz / FREQ_ONE_MHZ)
			l_freq_hz = int(freq_hz - (l_freq_mhz * FREQ_ONE_MHZ));

			logger.debug('Frequency [%d] Mhz | [%d] Hz', l_freq_mhz, l_freq_hz)

			#For some reason we switch endain from freq to sample
			p =  struct.pack(
				'<II',
				l_freq_mhz,
			 	l_freq_hz)
			result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
				HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_FREQ,
				0,
				0,
				p,
				len(p))
			if result < len(p):
				logger.error('Error setting frequency with value [%d]', freq_hz)
			else:
				logger.debug('Successfully set frequency with value [%d]', freq_hz)
				return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Error setting frequency, value should be of type INT or LONG')

	def set_sample_rate(self, freq, div):
		''' Sets the sample rate of the hack rf device '''
		if isinstance( freq, int) and isinstance( div, int):
			#Make a C struct with the values
			p =  struct.pack('>II', freq, div)

			result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
				HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SAMPLE_RATE_SET,
				0,
				0,
				p,
				len(p))
			if result < len(p):
				logger.error('Error setting Sample Rate with Frequency [%d] and Divider [%d]', freq, div)
			else:
				logger.debug('Successfully set Sample Rate with Frequency [%d] and Divider [%d]', freq, div)
				return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Error setting Sample Rate, Frequency and Divider should be of type INT or LONG')

	def set_lna_gain(self, gain):
		''' Sets the LNA gain, in 8Db steps, maximum value of 40 '''
		if isinstance( gain, int ):
			if int(gain) <= 40:
				result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_IN,
					HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_LNA_GAIN,
					0,
					gain,
					1)
				if result[0] != 1:
					logger.debug('Successfully set LNA gain to [%d]', gain)
					return HackRfConstants.HACKRF_SUCCESS
				else:
					logger.error('Failed to set LNA gain to [%d]', gain)
			else:
				logger.error('Failed to set LNA gain, value must be less than 41')
		else:
			logger.error('Failed to set LNA gain, gain should be of type INT or LONG')

	def set_vga_gain(self, gain):
		''' Sets the vga gain, in 2db steps, maximum value of 62 '''
		if isinstance( gain, int ):
			if int(gain) <= 62:
				result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_IN,
					HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_VGA_GAIN,
					0,
					gain,
					1)
				if result[0] == 1:
					logger.debug('Successfully set VGA gain to [%d]', gain)
					return HackRfConstants.HACKRF_SUCCESS
				else:
					logger.error('Failed to set VGA gain to [%d]', gain)
			else:
				logger.error('Failed to set VGA gain, value must be less than 63')
		else:
			logger.error('Failed to set VGA gain, gain should be of type INT or LONG')

	def set_txvga_gain(self, gain):
		''' Sets the txvga gain, in 1db steps, maximum value of 47 '''
		if isinstance( gain, int ):
			if int(gain) <= 47:
				result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_IN,
					HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_TXVGA_GAIN,
					0,
					gain,
					1)
				if result[0] == 1:
					logger.debug('Successfully set TXVGA gain to [%d]', gain)
					return HackRfConstants.HACKRF_SUCCESS
				else:
					logger.error('Failed to set TXVGA gain to [%d]', gain)
			else:
				logger.error('Failed to set TXVGA gain, value must be less than 48')
		else:
			logger.error('Failed to set TXVGA gain, gain should be of type INT or LONG')

	def enable_amp(self):
		''' Turns on the amp for the hackrf device '''
		result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_AMP_ENABLE,
			1,
			0)
		if result == 0:
			logger.debug('Successfully enabled Amp')
			return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Failed to enable Amp')

	def disable_amp(self):
		''' Disable the amp for the hackrf device '''
		result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_AMP_ENABLE,
			0,
			0)
		if result == 0:
			logger.debug('Successfully disabled Amp')
			return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Failed to disable Amp')

	def set_rx_mode(self):
		''' This sets the HackRf in receive mode '''
		result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_TRANSCEIVER_MODE,
			HackRfTranscieverMode.HACKRF_TRANSCEIVER_MODE_RECEIVE, 0)
		if result == 0:
			logger.debug('Successfully set HackRf in Recieve Mode')
			return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Failed to set HackRf in Recieve Mode')

	def set_tx_mode(self):
		''' This sets the HackRf in tranfer mode '''
		result = self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
			HackRfVendorRequest.HACKRF_VENDOR_REQUEST_SET_TRANSCEIVER_MODE,
			HackRfTranscieverMode.HACKRF_TRANSCEIVER_MODE_TRANSMIT, 0)
		if result == 0:
			logger.debug('Successfully set HackRf in Transfer Mode')
			return HackRfConstants.HACKRF_SUCCESS
		else:
			logger.error('Failed to set HackRf in Transfer Mode')

	def write_gpio(self, pin_number, value):
		# Write to the GPIOs of the device
		# GPIO Mapping is
		# 		0: GPIO_3_8, 
		# 		1: GPIO_3_14,
		# 		2: GPIO_3_15,
		# 		3: GPIO_3_12,
		# 		4: GPIO_3_13 
		if pin_number in range(5):
			self.device.ctrl_transfer(HackRfConstants.HACKRF_DEVICE_OUT,
			HackRfVendorRequest.USB_VENDOR_REQUEST_SET_GPIO,
			value,
			pin_number)
		else:
			logger.warning('Invalid Pin Number [%d]' % pin_number)
