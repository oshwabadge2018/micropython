from machine import Pin
import gxgde0213b1
import G_FreeSans24pt7b
import font12
import font16
import font20
import font24
import network
import ubinascii
import urandom
import machine
import time
import os
import imagedata
import struct
import time

import machine
from microWebSrv import MicroWebSrv
from machine import Pin, TouchPad

ipaddress = None
wifipass = None

#initialize the epaper
reset = Pin(16, Pin.OUT)
dc = Pin(25, Pin.OUT)
busy = Pin(4, Pin.IN)
cs = Pin(5, Pin.OUT)
epd = gxgde0213b1.EPD(reset, dc, busy, cs)
epd.init()

#create the frame buffer and set proper screen rotation
fb_size = int(epd.width * epd.height / 8)
fb = bytearray(fb_size)
epd.clear_frame(fb)
epd.set_rotate(gxgde0213b1.ROTATE_90)

# from Magic 8-Ball app by Steve Pomeroy https://hackaday.io/xxv
# github.com/oshwabadge2018/ohs18apps/blob/master/magic8ball.py
class TouchButton(object):
   def __init__(self, pin, on_pressed, threshold=400, debounce_ms=50):
       self._touchpad = machine.TouchPad(pin)
       self._on_pressed = on_pressed
       self._threshold = threshold
       self._debounce_ms = debounce_ms
       self._down_ms = None
       self._pressed = False

   def read(self):
       if self._touchpad.read() < self._threshold:
           if not self._pressed:
               if not self._down_ms:
                   self._down_ms = time.ticks_ms()
               else:
                   if time.ticks_diff(time.ticks_ms(), self._down_ms) > self._debounce_ms:
                       self._on_pressed()
                       self._pressed = True
       else:
           self._pressed = False
           self._down_ms = None

# from Magic 8-Ball app by Steve Pomeroy https://hackaday.io/xxv
# github.com/oshwabadge2018/ohs18apps/blob/master/magic8ball.py
class MagicBall():
   def clear_screen():
       epd.initPart()
       epd.clear_frame(fb)
       epd.display_frame(fb)

   def show_message(message):
       epd.init()
       epd.clear_frame(fb)
       epd.display_string_at(fb, 0, 52, message, font16, gxgde0213b1.COLORED)
       epd.display_frame(fb)

   def read_accel(i2c):
       i2c.writeto_mem(30, 0x18, b'\x80')
       x = struct.unpack("h", i2c.readfrom_mem(30, 0x6, 2))
       y = struct.unpack("h", i2c.readfrom_mem(30, 0x8, 2))
       z = struct.unpack("h", i2c.readfrom_mem(30, 0xA, 2))
       return (x[0], y[0], z[0])

   def get_orientation(i2c):
       new_orientation = None
       pos = MagicBall.read_accel(i2c)

       if pos[2] > 13000:
           new_orientation = "upright"
       elif pos[2] < -13000:
           new_orientation = "prone"

       return new_orientation

   def main(f):
           phrases = ["It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.", "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.", "Reply hazy, try again", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very doubtful."]
           i2c = machine.I2C(scl=Pin(22), sda=Pin(21))
           epd.init()
           epd.set_rotate(gxgde0213b1.ROTATE_270)
           epd.clear_frame(fb)
           epd.display_frame(fb)
           prev_orientation = None

           keep_on = [True]

           def exit_loop():
               keep_on[0] = False

           exit_button = TouchButton(Pin(32), exit_loop)

           while keep_on[0]:
               exit_button.read()
               orientation = MagicBall.get_orientation(i2c)

               if orientation and orientation != prev_orientation:
                   if orientation == 'upright':
                       MagicBall.show_message(urandom.choice(phrases))
                   elif orientation == 'prone':
                       MagicBall.clear_screen()
               prev_orientation = orientation

# from accelerometer demo app
# github.com/oshwabadge2018/ohs18apps/blob/master/accelerometer.py
class Accelerometer():
   def clear_screen():
       epd.initPart()
       epd.clear_frame(fb)
       epd.display_frame(fb)

   def show_message(message):
       epd.init()
       epd.clear_frame(fb)
       epd.display_string_at(fb, 0, 52, message, font16, gxgde0213b1.COLORED)
       epd.display_frame(fb)

   def read_accel(i2c):
       i2c.writeto_mem(30, 0x18, b'\x80')
       x = struct.unpack("h", i2c.readfrom_mem(30, 0x6, 2))
       y = struct.unpack("h", i2c.readfrom_mem(30, 0x8, 2))
       z = struct.unpack("h", i2c.readfrom_mem(30, 0xA, 2))
       return (x[0], y[0], z[0])

   def get_orientation(i2c):
       pos = Accelerometer.read_accel(i2c)
       return pos

   def main(f):
       i2c = machine.I2C(scl=Pin(22), sda=Pin(21))
       epd.init()
       epd.set_rotate(gxgde0213b1.ROTATE_270)
       epd.clear_frame(fb)
       epd.display_frame(fb)
       keep_on = [True]

       def exit_loop():
           keep_on[0] = False

       exit_button = TouchButton(Pin(32), exit_loop)

       while keep_on[0]:
           exit_button.read()
           orientation = Accelerometer.get_orientation(i2c)
           x = "x={0}".format(orientation[0])
           y = "y={0}".format(orientation[1])
           z = "z={0}".format(orientation[2])
           print(x, y, z)
           epd.clear_frame(fb)
           epd.set_rotate(gxgde0213b1.ROTATE_270)
           epd.display_string_at(fb, 10,  0, x, font16, gxgde0213b1.COLORED)
           epd.display_string_at(fb, 10, 24, y, font16, gxgde0213b1.COLORED)
           epd.display_string_at(fb, 10, 48, z, font16, gxgde0213b1.COLORED)
           epd.display_frame(fb)
           time.sleep(1)

                    

def start_ap_mode():
	global ipaddress
	ap = network.WLAN(network.AP_IF)
	ap.active(True)

	essid = 'ohsbadge-' + ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
	global wifipass
	if wifipass == None:
		wifipass = str(urandom.getrandbits(30))
	ap.config(essid=essid)
	ap.config(authmode=3, password=wifipass)
	ipaddr = ap.ifconfig()[0]
	#set global var.
	ipaddress = ipaddr
  
	epd.clear_frame(fb)
	epd.set_rotate(gxgde0213b1.ROTATE_270)
	epd.display_string_at(fb, 0, 0, "Welcome to OHS 2018!", font16, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 20, "ESSID = " + essid, font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 32, "PASSWORD = " + wifipass, font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 44, "IP ADDR = " + ipaddr, font12, gxgde0213b1.COLORED)

	epd.display_frame(fb)

def start_ftp_server_app(f):
	start_ap_mode()
	startFTPServer()
	wait_for_button(TouchPad(Pin(32)))

def startFTPServer():
	global ipaddress
	epd.display_string_at(fb, 0, 84, "FTP Server at" + ipaddress , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 96, "No Username or Password" , font12, gxgde0213b1.COLORED)
	epd.display_frame(fb)
	import uftpd
	

@MicroWebSrv.route('/setup')
def _httpHandlerTestGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>OHS Badge Configuration Page</title>
        </head>
        <body>
            <h1>Enter your name</h1>
            Client IP address = %s
            <br />
			<form action="/setup" method="post" accept-charset="ISO-8859-1">
				First name: <input type="text" name="firstname"><br />
				Last name: <input type="text" name="lastname"><br />
				<input type="submit" value="Submit">
			</form>
        </body>
    </html>
	""" % httpClient.GetIPAddr()
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

@MicroWebSrv.route('/setup', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
	formData  = httpClient.ReadRequestPostedFormData()
	firstname = formData["firstname"]
	lastname  = formData["lastname"]
	content   = """\
	<!DOCTYPE html>
	<html lang=en>
		<head>
			<meta charset="UTF-8" />
            <title>OHS Badge Configuration Post</title>
        </head>
        <body>
            <h1>Name sent to badge</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
	""" % ( MicroWebSrv.HTMLEscape(firstname),
		    MicroWebSrv.HTMLEscape(lastname) )
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )
	writeName(firstname,lastname)

	epd.set_rotate(gxgde0213b1.ROTATE_90)
	namestr=firstname+"\n"+lastname
	epd.clear_frame(fb)
	epd.G_display_string_at(fb,0,0,namestr,G_FreeSans24pt7b,1,gxgde0213b1.COLORED)
	epd.display_frame(fb)
	goto_deepsleep()

def goto_deepsleep():
	#go to deepsleep wait for user to press one of the buttons
	#button1 = machine.TouchPad(machine.Pin(33))
	#time.sleep_ms(100)
	#reading = button1.read()
	#button1.config(int(2/3 * reading))
	#button1.callback(lambda t:print("Pressed 33"))

	#button2 = machine.TouchPad(machine.Pin(12))
	#time.sleep_ms(100)
	#reading = button2.read()
	#button2.config(int(2/3 * reading))
	#button2.callback(lambda t:print("Pressed 12"))

	button3 = machine.TouchPad(machine.Pin(32))
	time.sleep_ms(100)
	reading = button3.read()
	button3.config(int(2/3 * reading))
	button3.callback(lambda t:print("Pressed 32"))
	print("Sleepytime.. zz")
	time.sleep(1)
	machine.deepsleep()

def start_web_server_app(f):
	start_ap_mode()
	start_web_server()
	wait_for_button(TouchPad(Pin(32)))
	

def start_web_server():
	global ipaddress
	epd.display_string_at(fb, 0, 60, "Connect to badge AP to configure." , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 72, "Enter this URL in your browser:" , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 84, "http://" + ipaddress + "/setup", font12, gxgde0213b1.COLORED)
	epd.display_frame(fb)
	srv = MicroWebSrv(webPath='www/')
	srv.MaxWebSocketRecvLen     = 256
	srv.WebSocketThreaded		= False
	#srv.AcceptWebSocketCallback = _acceptWebSocketCallback
	srv.Start(threaded=False)

def start():
	if not 'provisioned' in os.listdir():
		print("First Boot REPL")
		#15 27 39 51 63 75 87 99
		epd.set_rotate(gxgde0213b1.ROTATE_270)
		epd.clear_frame(fb)
		epd.display_string_at(fb, 0, 0, "First Boot!", font16, gxgde0213b1.COLORED)
		epd.display_string_at(fb, 4, 15,      "Badge will drop to REPL", font12, gxgde0213b1.COLORED)
		epd.display_string_at(fb, 4, 39,   "Configure Via REPL", font12, gxgde0213b1.COLORED)
		
		#hw stats
		adc = machine.ADC(machine.Pin(35))
		adc.atten(adc.ATTN_11DB)
		Voltage = (adc.read()/4096)*3.3
		epd.display_string_at(fb, 4, 63, "Bat V:", font12, gxgde0213b1.COLORED)
		epd.display_string_at(fb, 60, 63, str(Voltage), font12, gxgde0213b1.COLORED)
	
		i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
		devl = i2c.scan()
		
		epd.display_string_at(fb, 4, 75, "i2c:", font12, gxgde0213b1.COLORED)
		epd.display_string_at(fb, 60, 75, str(devl), font12, gxgde0213b1.COLORED)
		epd.display_frame(fb)
		f = open("provisioned","w")
		f.write("")
		f.close()
		return

	# i2c bus address of the Kionix KX122-1037 Accelerometer
	addr = 30
	i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
	devl = i2c.scan()
	print("detected i2c addresses: {0}".format(str(devl)))
	if addr in devl:
		print("accelerometer detected: {0}".format(addr))
		i2c.writeto_mem(addr,0x18,b'\x80')
		# read X-axis accelerometer output least significant byte
		acclx = struct.unpack("h",i2c.readfrom_mem(addr,0x6,2))
		# use only the first element of tuple
		acclx = acclx[0]
		print("accelerometer: x={0}".format(acclx))

	# only enter menu if badge is held horizontal or inverted
	# this will prevent errant cap touch press from taking the
	# badge out of name display mode while being worn
	# acclx < 0: badge is hanging from lanyard
	# acclx = 0: badge is hortizontal
	# acclx > 0: badge is being held by user
	if machine.wake_reason() == machine.TOUCHPAD_WAKE and acclx >= 0:
		print(machine.TouchPad.wake_reason())
		#if machine.TouchPad.wake_reason() == 9:
		#	#go into AP mode
		#	#TODO add support for detecting which button cause the wakeup
		#	start_ap_mode()
		#	start_web_server()
		if machine.TouchPad.wake_reason() == 8:
			m = buildMenu()

			app = TouchPad(Pin(32))
			card = TouchPad(Pin(33))
			right = TouchPad(Pin(13))
			left = TouchPad(Pin(14))
			down = TouchPad(Pin(27))
			up = TouchPad(Pin(12))

			m.menuloop(up,down,left,right,app,card)
			machine.reset()

		else:
			epd.clear_frame(fb)
 			epd.display_string_at(fb, 0, 0, "OHS 2018", font24, gxgde0213b1.COLORED)
 			epd.display_string_at(fb, 0, 24, "Serial REPL Mode", font16, gxgde0213b1.COLORED)
 			epd.display_frame(fb)
	else:
		try:
			import d_name
			print("Printing Name")
			namestr=d_name.first+"\n"+d_name.last
			epd.clear_frame(fb)
			epd.G_display_string_at(fb,0,0,namestr,G_FreeSans24pt7b,1,gxgde0213b1.COLORED)
			epd.display_frame(fb)
		except:
			print("No Name, Showing Logo")
			epd.display_frame(imagedata.ohslogo)
		goto_deepsleep()

def buildMenu():
	import menusys as menu
	epd.set_rotate(gxgde0213b1.ROTATE_270)
	m = menu.Menu("Available Apps")

	#does apps dir exist
	if not 'apps' in os.listdir():
		print("Apps Dir is missing, Populating new one")
		os.mkdir('apps')

	#add static items
	m.addItem("Change Name",start_web_server_app)
	m.addItem("Start FTP Server",start_ftp_server_app)
	m.addItem("Web REPL",start_web_repl_app)
	m.addItem("Serial REPL",start_repl_app)
	m.addItem("Magic 8-ball",start_magic_app)
	m.addItem("Accelerometer",start_accel_app)

	for a in os.listdir('apps'):
		m.addItem(a,execapp)
		print("Adding App '%s'"%a)
	return m

def start_magic_app(f):
    ball = MagicBall()
    ball.main()

def start_accel_app(f):
    accel = Accelerometer()
    accel.main()

def start_repl_app(f):
	epd.clear_frame(fb)
	epd.display_string_at(fb, 0, 0, "OHS 2018", font24, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 24, "Serial REPL Mode", font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 48, "Batteries must be Removed", font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 48+12, "or machine.reset() must be sent over", font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 48+24, "serial port to reset badge", font12, gxgde0213b1.COLORED)
 	epd.display_frame(fb)
	# this is a hack to drop to the REPL
	# by creating a runtime error
	[][0]

def start_web_repl_app(f):
	start_ap_mode()
	import webrepl
	webrepl.start()
	epd.display_string_at(fb, 0, 60, "Download WebREPL client from:" , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 72, "github.com/micropython/webrepl" , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 88, "To exit WebREPL, remove batteries", font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 100, "or type machine.reset()", font12, gxgde0213b1.COLORED)
	epd.display_frame(fb)
	# this is a hack to drop to the REPL
	# by creating a runtime error
	[][0]

def execapp(f):
	f = "/apps/"+f
	print("Running '%s'"%f)
	try:
		exec(open(f).read(), globals(), globals())
	except:
		pass			

def writeName(first,last,socialmedia='',email=''):
	try:
		fh = open("d_name.py","w")
		fh.write("first='%s'\n"%first)
		fh.write("last='%s'\n"%last)
		fh.write("socialmedia='%s'\n"%socialmedia)
		fh.write("email='%s'\n"%email)
		fh.close()
	except:
		print("Could not Write personal info")

def wait_for_button(b):
	print("Waiting for press of %s"%b)
	while b.read()>400:
		time.sleep(0.1)
	print("Waiting release of %s"%b)
	while b.read()<400:
		time.sleep(0.1)
