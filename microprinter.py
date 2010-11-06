#!/usr/bin/env python

# Taken by Ian (https://github.com/ianozsvald/SocialMicroprinter)
# original with full props to Ben: https://github.com/benosteen/microprinter
# Ben is not responsible for my hacking of his code (sorry Ben for the ugly hack!)

# Ported from code created by Roo Reynolds
# http://rooreynolds.com/category/microprinter/

# See also: http://microprinter.pbwiki.com/

#from serial import Serial

import logging

logger = logging.getLogger("Microprinter")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)

index_filename = "/home/ianozsvald/webapps/app_microprinter/index.html"

class NoSerial(Exception):
  pass

class BarcodeException(Exception):
  pass

class CBM1000Mode(object):
  """CBM1000Mode.E - emphasis
  CBM1000Mode.DH - double height
  CBM1000Mode.DW - double width
  CBM1000Mode.U - underline
  Examples:
  
  # Use font A with double-width
  Microprinter.setPrintMode(0|CBM1000Mode.DW)
  # Use font B with emphasis and double-height
  Microprinter.setPrintMode(1|CBM1000Mode.E|CBM1000Mode.DH)
  """
  E = 1 << 3
  DH = 1 << 4
  DW = 1 << 5
  U = 1 << 7

def decorator_shell(decorator):
  def new_decorator(f):
    g = decorator(f)
    g.__name__ = f.__name__
    g.__doc__ = f.__doc__
    g.__dict__.update(f.__dict__)
    return g
  # Now a few lines needed to make simple_decorator itself
  # be a well-behaved decorator.
  new_decorator.__name__ = decorator.__name__
  new_decorator.__doc__ = decorator.__doc__
  new_decorator.__dict__.update(decorator.__dict__)
  return new_decorator

@decorator_shell
def check_serial_init(func):
  def x(*args, **kwargs):
    # args[0] == self
    #if args[0]._s:
    return func(*args, **kwargs)
    #else:
    #  raise NoSerial
  return x

CBMCOMMON = {
    "COMMAND" : 0x1B,
    "LF" : 0x10,
    "LINEFEED_RATE" : 0x33,
    "FULLCUT" : [0x1B,0x69],
    "PARTIALCUT" : [0x1B,0x6D],
    "PRINT_MODE" : 0x21,
    "DOUBLEPRINT" : 0x47,
    "UNDERLINE" : 0x2D,
    "RESET" : 0x40,
    "COMMAND_IMAGE" : 0x2A,
    "COMMAND_FLIPCHARS" : 0x7B,
    "COMMAND_ROTATECHARS" : 0x56,
    "COMMAND_BARCODE" : 0x1D,
    "COMMAND_BARCODE_PRINT" : 0x6B,
    "COMMAND_BARCODE_WIDTH" : 0x77,
    "COMMAND_BARCODE_HEIGHT" : 0x68,
    "COMMAND_BARCODE_TEXTPOSITION" : 0x48,
    "COMMAND_BARCODE_FONT" : 0x66
    }

CBMBARCODES = {
    "BARCODE_WIDTH_NARROW" : 0x02,
    "BARCODE_WIDTH_MEDIUM" : 0x03,
    "BARCODE_WIDTH_WIDE" : 0x04,
    "BARCODE_TEXT_NONE" : 0x00,
    "BARCODE_TEXT_ABOVE" : 0x01,
    "BARCODE_TEXT_BELOW" : 0x02,
    "BARCODE_TEXT_BOTH" : 0x03,
    "BARCODE_MODE_UPCA" : 0x00,
    "BARCODE_MODE_UPCE" : 0x01,
    "BARCODE_MODE_JAN13AEN" : 0x02,
    "BARCODE_MODE_JAN8EAN" : 0x03,
    "BARCODE_MODE_CODE39" : 0x04,
    "BARCODE_MODE_ITF" : 0x05,
    "BARCODE_MODE_CODEABAR" : 0x06,
    "BARCODE_MODE_CODE128" : 0x07
    }

CBM1000 = {
    "FULLCUT" : [0x1D,0x56,0x01,0x49],
    "PARTIALCUT" : [0x1D,0x56,0x66,0x10]}  # CBM1000 specific codes as necessary
#    "FEED" : 0x64 # IAN mod
#CBM231 = {
#    }  # CBM231 specific codes as necessary

def getMicroprinterCommands(model):
  commands = {}
  if model.lower().startswith("cbm"):
    commands.update(CBMCOMMON)
    commands.update(CBMBARCODES)
  if model.lower() == "cbm1000":
    commands.update(CBM1000)
  return commands

class Microprinter(object):
  def __init__(self, serialport='/dev/ttyUSB0', speed = 19200, model="CBM"):
    """ >>> m = Microprinter("/dev/ttyUSB0", "CBM1000") 
     >>> m.write("Mwuhahahahah!")
     >>> m.feed(5)
     >>> m.cut()
     >>> m.close()
    """
    self._speed = speed
    self._s = None
    self.commands = {}
    self._serialport = serialport
    print "Config", serialport, speed
    self.c = getMicroprinterCommands(model)
    if model.lower() == "cbm1000":
      self.printMarkup = self.CBM1000_printMarkup
      self.feed = self.CBM1000feed
    elif model.lower().startswith("cbm"):
      self.feed = self.CBMfeed
    self.reconnect()

  def reconnect(self):
    print "IAN'S HACK - NOT CONNECTING!"
    #try:
    #  self._s = Serial(self._serialport, self._speed)#9600)
    #except Exception, e:
    #  logger.error("Couldn't open serial port %s" % self._serialport)
    #  logger.error(e)
    self._s = file(index_filename, 'a')
    
  @check_serial_init
  def close(self):
    if self._s:
      self._s.close()

  @check_serial_init
  def sendcodes(self, *args):
    """Will turn any set of integers to the printer directly:
    
    >>> m.sendcodes(*list_of_commands)
    >>> """
    self._s.write("".join(map(chr, args)))

  @check_serial_init
  def write(self, *args):
    """Basic command to write text to the printer.
    >>> m.write("Writing a string")
    >>> m.write(*["Writing a string", "and another", "and another/n/n"])
    """
    if len(args) == 1 and isinstance(args[0], basestring):
      logger.debug("Treating the 'write' argument as a string")
      logger.debug("Printing '%s'" % args[0])
      self._s.write(args[0])
    else:
      logger.debug("Treating the 'write' arguments as a list of strings")
      logger.debug("Printing '%s'" % "".join(args))
      self._s.write("".join(args))
    self._s.flush()

  @check_serial_init
  def flush(self):
    self._s.flush()

  @check_serial_init
  def CBM1000feed(self, lines=1):
    """"""
    if lines and isinstance(lines, int):
      lines = lines % 256
      self.sendcodes(self.c['COMMAND'], self.c['FEED'], lines)
      self.flush()
    else:
      self.sendcodes(self.c['COMMAND'], self.c['FEED'], 1)
      self.flush()

  @check_serial_init
  def CBMfeed(self, lines=1):
    """"""
    if lines and isinstance(lines, int):
      lines = lines % 256
      for x in xrange(lines):
        self.write("\n\n")
      self.flush()
    else:
      self.write("\n\n") # IAN EDIT
      self.flush()

  @check_serial_init
  def setPrintMode(self, mode):
    """Sets the printmode (0x1B 0x21 n == COMMAND PRINT_MODE mode)
    'mode' is a byte of flags:
    
    CBM1000
    bit 0 = font select - 0 - font A, 1 - font B
    bit 3 = 'Emphasis' (0/1 -> off/on)
    bit 4 = Double Height 
    bit 5 = Double width
    bit 7 = Underline
    
    see also the CBM1000Mode class
    """
    self.sendcodes(self.c['COMMAND'], self.c['PRINT_MODE'], mode)
    self.flush()
  
  @check_serial_init
  def printUPCABarcode(self, barcode):
    #if 10 < len(barcode) < 13:
    if len(barcode) < 11 or len(barcode) > 12:
      logger.error("UPC-A barcodes must be between 11 and 12 'digits'")
      raise BarcodeException
    allowed = "0123456789"
    barcode = "".join([x for x in barcode if x in allowed])
    self.printBarcode(barcode, self.c['BARCODE_MODE_UPCA'])
  
  @check_serial_init
  def printBarcode(self, barcode, barcode_mode = None):
    if not barcode_mode:
      barcode_mode = self.c['BARCODE_MODE_UPCA']
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_PRINT'])
    self.sendcodes(barcode_mode)
    self.write(barcode)
    self.sendcodes(0x00) # NUL code

  @check_serial_init
  def setBarcodeDimensions(self, height=162, width=3):
    self.setBarcodeHeight(height)
    self.setBarcodeWidth(width)

  @check_serial_init
  def setBarcodeHeight(self, height=162):
    height = height % 256
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_HEIGHT'])
    self.sendcodes(height)
    self.flush()
  
  @check_serial_init
  def setBarcodeWidth(self, width=3):
    if (width < 2): width = 2
    if (width > 4): width = 4
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_WIDTH'])
    self.sendcodes(width)
    self.flush()
  
  @check_serial_init
  def resetState(self):
    self.sendcodes(self.c['COMMAND'], self.c['RESET'])
    self.flush()
  
  @check_serial_init
  def cut(self):
    self.sendcodes(*self.c['FULLCUT'])
  
  @check_serial_init
  def partialCut(self):
    """Even though this is what the data sheet states as being a partial cut
    on the CBM1000, I haven't got it working."""
    self.sendcodes(*self.c['PARTIALCUT'])

  @check_serial_init
  def setDoubleprint(self, state=True):
    self.sendcodes(self.c['COMMAND'], self.c['DOUBLEPRINT'])
    if state:
      self.sendcodes(0x01)
    else:
      self.sendcodes(0x00)
    self.flush()

  @check_serial_init
  def setUnderline(self, state=True):
    self.sendcodes(self.c['COMMAND'], self.c['UNDERLINE'])
    if state:
      self.sendcodes(0x01)
    else:
      self.sendcodes(0x00)
    self.flush()

  @check_serial_init
  def CBM1000_printMarkup(self, markeduptext):
    """Print some marked up text to the printer. (Similar to Roo's markup function but with differing functionality.
    
    ^ ... ^ = Apply Double Height to anything inbetween the '^' marks
    ~ ... ~ = Double Width
    * ... * = Emphasis/bold
    _ ... _ = Underline
    
    Eg:
    
    '^This is text rendered at double height^ and this is not.'
    '~Double width~ and *bold text*'
    '_~*Underlined, double width and bold text*~_'"""
    
    old_flags, state_flags = 0, 0
    off_flags = 0
    self.setPrintMode(state_flags)
    for line in markeduptext.split("\n"):
      for token in [x for x in line.split(" ") if x]:
        old_flags = state_flags
        while (token and token[0] in "*_^~"):
          if token.startswith("*"):
            token = token[1:]
            state_flags = state_flags | CBM1000Mode.E
          if token.startswith("_"):
            token = token[1:]
            state_flags = state_flags | CBM1000Mode.U
          if token.startswith("^"):
            token = token[1:]
            state_flags = state_flags | CBM1000Mode.DH
          if token.startswith("~"):
            token = token[1:]
            state_flags = state_flags | CBM1000Mode.DW
        
        while (token and token[-1] in "*_^~"):
          if token.endswith("*"):
            token = token[:-1]
            off_flags = off_flags | CBM1000Mode.E
          if token.endswith("_"):
            token = token[:-1]
            off_flags = off_flags | CBM1000Mode.U
          if token.endswith("^"):
            token = token[:-1]
            off_flags = off_flags | CBM1000Mode.DH
          if token.endswith("~"):
            token = token[:-1]
            off_flags = off_flags | CBM1000Mode.DW
        
        if old_flags != state_flags:
          self.setPrintMode(state_flags)
        
        self.write(token)
        
        if off_flags:
          state_flags = state_flags & (255 ^ (off_flags))
          self.setPrintMode(state_flags)
          off_flags = 0
        
        self.write(" ")
      self.feed(1)
    self.feed()

  def setBarcodeTextPosition(self, position):
    if position < 0: position = 0
    if position > 3: position = 3
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_TEXTPOSITION'])
    self.sendcodes(position)
    self.flush()
  
  def setBarcodeFont(self, fontcode):
    if fontcode < 0: fontcode = 0
    if fontcode > 1: fontcode = 1
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_FONT'])
    self.sendcodes(fontcode)
    self.flush()

  def print_imagebytes(self, m, data):
    self.sendcodes(self.c['COMMAND'], self.c['COMMAND_IMAGE'])
    density = 1
    if m == 1 or m == 33:
      density = 3
    datalength = len(data) / density
    self.sendcodes(m, datalength%256, datalength/256)
    self.sendcodes(*data)
    self.flush()

  def setLineFeedRate(self, feedlength):
    # <1B>H<33>H<n>
    self.sendcodes(self.c['COMMAND'], self.c['LINEFEED_RATE'])
    self.sendcodes(feedlength)
    self.flush()
  """
	void printSparkline(String label, int[] data) throws IOException { //works well with 255 bytes of data
		printer.write(label.substring(0, 7))
		printer.flush()
		fileout.write(COMMAND)
		fileout.write(COMMAND_IMAGE)
		fileout.write((byte) 0x0); 
		fileout.write((byte) 0x0); 
		fileout.write((byte) 0x01);		
		//convert the scale...
		int max = Integer.MIN_VALUE
		int min = Integer.MAX_VALUE
		for (int i = 0; i < data.length; i++) {
			if (data[i] > max) max = data[i]
			if (data[i] < min) min = data[i]
		}
		for (int i = 0; i < data.length; i++) {
			data[i] = (data[i] - min) * 7 / (max - min)
			int value = (int) Math.pow(2, data[i])
			fileout.write(value)
		}
	}

	void printDateBarcode() throws IOException {
		String dateStamp = new SimpleDateFormat("/yyyy/MM/dd/").format(new Date())
		setBarcodeHeight((byte) 50)
		setBarcodeWidth(BARCODE_WIDTH_MEDIUM)
		setBarcodeTextPosition(BARCODE_TEXT_BELOW)
		setBarcodeFont((byte) 0x01)
		printBarcode(dateStamp)
	}
"""

if __name__ == "__main__":
    m = Microprinter('/dev/tty', 1200)
    m.write("Hello, this is the CBM 231!\n")
    m.setUnderline(True)
    m.write('This might be a title\n\n')
    m.setUnderline(False)
    m.setDoubleprint(True)    
    m.write('This is important\n')
    m.setDoubleprint(False)
    m.write('And this would be the regular content...\n')
    m.printUPCABarcode('012345678910')
    m.flush()
    m.feed(5)
    m.cut()
    m.flush()
