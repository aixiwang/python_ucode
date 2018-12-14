# -*- coding: utf-8 -*-
"""
UCODE (v01) - Forth like script engine
ported from https://github.com/amnk/forth for Pyboard

BSD 3-clause License applied

Note: python2 only
"""

import sys
import math
import time
import socket

import serial
import minimalmodbus
#from utils import *

f_error = "Operation error for {f} command. Exiting."
s_error = "Not enough elements in stack. Exiting"

# external io mapping
io_array = [0]*32

# internal data buffer
buf_array = [0]*32

ip_point = 0
debug_switch = 0
serial_handle = None

stack = []

#---------------------------------------------------------
# Application specific functions
#---------------------------------------------------------
#------------------------
# read_modbus_register
#------------------------
def read_modbus_register(portname,baudrate,timeout,slaveaddress,offset):
    try:
        inst = minimalmodbus.Instrument(portname,slaveaddress,baudrate,timeout)
        d = inst.read_register(offset)
        
        inst.serial.close()
        return 0,d
        
    except Exception as e:
        print('read_modbus_register exception. ' +str(e))
        return -1,None
        

        
#------------------------
# write_modbus_register
#------------------------
def write_modbus_register(portname,baudrate,timeout,slaveaddress,offset,val):
    try:
        inst = minimalmodbus.Instrument(portname,slaveaddress,baudrate,timeout)
        
        #print('write_modbus_register 2')
        inst.write_register(offset,val,functioncode=6,signed=True)
        inst.serial.close()
        #print('write_modbus_register 3')
        return 0
        
    except Exception as e:
        print('write_modbus_register exception. ' +str(e))
        return -1

#------------------------
# send_data_to_agent
#------------------------        
def send_data_to_agent(data):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('127.0.0.1', 81)
        s.connect(address)
        s.send(data)
        s.close()
    except:
        pass

#------------------------
# rsensor
#------------------------
def rsensor():

    d1 = 65535
    d2 = 65535
    d3 = 65535
    d4 = 65535
    d5 = 65535
    
    ret1,d1 = read_modbus_register('/dev/ttyS1',9600,1,1,0)
    ret2,d2 = read_modbus_register('/dev/ttyS1',9600,1,1,1)
    ret3,d3 = read_modbus_register('/dev/ttyS1',9600,1,1,2)
    ret4,d4 = read_modbus_register('/dev/ttyS1',9600,1,1,3)
    ret5,d5 = read_modbus_register('/dev/ttyS1',9600,1,1,4)


    if ret1 == 0 and ret2 == 0:
        t = time.time()
        s = "%s,%s,%s,%s,%s,%s" % (str(t),str(d1),str(d2),str(d3),str(d4),str(d5))
        print(s)
        
        #showd(pm10 * 100 + pm25)
        do_data_log(s)

        send_data_to_agent(s + '\r\n')
        
        #print('rsensor 4')
    else:
        print('rsensor error')
        
#------------------------
# showd
#------------------------        
def showd(i):
    #print('showd:',i)
    ret1 = write_modbus_register('COM4',9600,3,1,0,i)


#-------------------
# do_data_log
#-------------------
def do_data_log(content):

    try:
        if has_file('data') == False:
            os.system('mkdir data')

        fname = time.strftime('data/%Y-%m-%d.csv', time.localtime(time.time()))
        f = open(fname,'ab')
        
        content = str(content) + '\r\n'
        
        if type(content) == str:
            content_bytes = content.encode('utf-8')
            f.write(content_bytes)
        else:
            f.write(content)
        
        f.close()
        return 0
    except:
        return -1
        
#---------------------------------------------------------
# Core functions
#---------------------------------------------------------
def debug_print(s):
    if debug_switch > 0:
        print(s)
        
def io_read(off):
    return io_array[off]

def io_write(off,dat):
    io_array[off] = dat

def buf_read(off):
    return buf_array[off]

def buf_write(off,dat):
    buf_array[off] = dat


def _value(value):
    """
    Function is used as a helper, to define if value is an int/float or a string
    """
    if value.find('0x') == 0:
        return int(value,16)
        
    if value.find('.') >= 0:
        #print('value 3')
        return float(value)
    elif not value.isdigit():
        return value
    elif value.isdigit() or value.lstrip('-').isdigit():
        #print('value 2')
        return int(value)

def f_put(f_stack, args):
    """
    Should be called with two values: stack and a value to append to the stack
    """
    f_stack.append(_value(args))

def f_add(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their summary back
    """
    if len(f_stack)<2:
        sys.exit(s_error)
    try:
        summary = f_stack[-1] + f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="and"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(summary))

def f_sub(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their difference back
    """
    if len(f_stack)<2:
         sys.exit(s_error)
    try:
        sub = f_stack[-1] - f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="sub"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(sub))
        
def f_mul(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their difference back
    """
    if len(f_stack)<2:
        sys.exit(s_error)
    try:
        temp = f_stack[-1] * f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="mul"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(temp))
        
def f_div(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their difference back
    """
    if len(f_stack)<2:
         sys.exit(s_error)
    try:
        temp = f_stack[-1] / f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="div"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(temp))

def f_and(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their difference back
    """
    if len(f_stack)<2:
         sys.exit(s_error)
    try:
        temp = f_stack[-1] and f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="and"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(temp))

def f_or(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and puts their difference back
    """
    if len(f_stack)<2:
         sys.exit(s_error)
    try:
        temp=f_stack[-1] or f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="or"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(temp))        
        

def f_pow(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and calculat m ** n
    """
    if len(f_stack)<2:
         sys.exit(s_error)
    try:
        temp=f_stack[-1] ** f_stack[-2]
    except TypeError:
        sys.exit(f_error.format(f="pow"))
    finally:
        f_pop(f_stack, n=2)
        f_put(f_stack, str(temp))    


def f_sqrt(f_stack, args=None):
    """
    Takes two values from f_stack (simple list), and calculat sqrt(m)
    """
    if len(f_stack)<1:
         sys.exit(s_error)
    try:
        temp = math.sqrt(f_stack[-1])
    except TypeError:
        sys.exit(f_error.format(f="sqrt"))
    finally:
        f_pop(f_stack, n=1)
        f_put(f_stack, str(temp))    

        
def f_dup(f_stack, args=None):
    """
    duplicate the nearest    
    """
    if len(f_stack)<1:
        sys.exit(s_error)

    #print('stack:',f_stack)
    f_put(f_stack, str(f_stack[-1]))


def f_dup2(f_stack, args=None):
    """
    duplicate the nearest    
    """
    if len(f_stack)<1:
        sys.exit(s_error)

    try:
        temp = f_stack[-1]
        #print('temp:' + str(temp))        
        f_pop(f_stack, n=1)
        #print('stack:',f_stack)       
        n = len(f_stack)
        #print('n:' + str(n))
        if n < int(temp):
            #print('error')
            sys.exit(s_error)
        
        f_put(f_stack, str(f_stack[-int(temp)]))
        #print('stack:',f_stack)
        
    except TypeError:
        sys.exit(f_error.format(f="dup2"))
        
    finally:
        pass
        
        
def f_swap(f_stack, args=None):
    """
    swap data in stack
    """
    if len(f_stack)<2:
        sys.exit(s_error)
    t1 = f_stack.pop()
    t2 = f_stack.pop()
    f_put(f_stack, str(t1))
    f_put(f_stack, str(t2))

    
def f_print(f_stack, args=None):
    """
    Accepts f_stack (simple list), pops a value from it and prints that value
    """
    if len(f_stack)<1:
        sys.exit(s_error)
    print(f_stack.pop())

def f_pop(f_stack, args=None, n=1):
    """
    Accepts f_stack (simple list), deletes n elements and returns them 
    """
    if len(f_stack)<n:
        sys.exit(s_error)
    elements = f_stack[-n::]
    del(f_stack[-n::])
    return elements
   
def f_ior(f_stack, args=None):
    """
    read data from external io device
    usage: ior offset
    """
    try:
        temp= io_read(_value(args))
    except TypeError:
        sys.exit(f_error.format(f="ior"))
    finally:
        f_put(f_stack,str(temp))
        

def f_iow(f_stack, args=None):
    """
    write io data to external io device, offset, data is push to stack as parameter
    """
    if len(f_stack)<2:
        sys.exit(s_error)
    try:
        io_write(f_stack[-1],f_stack[-2])
    except TypeError:
        sys.exit(f_error.format(f="iow"))
    finally:
        f_pop(f_stack,n=2)
    

def f_bufr(f_stack, args=None):
    """
    bufr -- read data from internal buffer
    """
    try:
        temp= buf_read(_value(args))
    except TypeError:
        sys.exit(f_error.format(f="bufr"))
    finally:
        f_put(f_stack,str(temp))
        

def f_bufw(f_stack, args=None):
    """
    bufw -- write io data to internal buffer, offset, data is push to stack as parameter
    """
    if len(f_stack)<2:
        sys.exit(s_error)
    try:
        
        buf_write(_value(args))
    except TypeError:
        sys.exit(f_error.format(f="bufw"))
    finally:
        f_pop(f_stack,n=2)

def f_ifs(f_stack, args=None):
    global ip_point
    """
    ifs -- if n > 0, skip steps
    """
    if len(f_stack)<1:
        sys.exit(s_error)
    try:
        if f_stack[-1] > 0:
            ip_point = _value(args)
            
    except TypeError:
        sys.exit(f_error.format(f="ifs"))
    finally:
        f_pop(f_stack,n=1)

def f_dbg(f_stack, args=None):
    global debug_switch
    """
    dbg 1 -- turn on debug
    dbg 0 -- turn off debug
    """

    try:
        if _value(args) > 0:
            debug_switch = 1
        else:
            debug_switch = 0
            
    except TypeError:
        sys.exit(f_error.format(f="dbg"))
    finally:
        pass

def f_jmp(f_stack, args=None):
    global ip_point
    
    """
    dbg 1 -- turn on debug
    dbg 0 -- turn off debug
    """

    try:
        ip_point = _value(args)
            
    except TypeError:
        sys.exit(f_error.format(f="jmp"))
    finally:
        pass
        
def f_sleep(f_stack, args=None):
    """
    usage: sleep n
    """
    try:
        #print('args:' + args)
        time.sleep(_value(args))    
    except TypeError:
        sys.exit(f_error.format(f="sleep"))
    finally:
        pass
        
def f_showd(f_stack, args=None):
    """
    usage: display digital in 7 seg display device
    """
    global ip_point
    """
    ifs -- if n > 0, skip steps
    """
    if len(f_stack)<1:
        sys.exit(s_error)
    try:
        showd(int(f_stack[-1]))
            
    except TypeError:
        sys.exit(f_error.format(f="showd"))
    finally:
        f_pop(f_stack,n=1)
        
        
        
def f_uinit(f_stack, args=None):
    global serial_handle
    """
    usage: uinit(9600,1)
    """
    
    if len(f_stack)<2:
        sys.exit(s_error)
    try:
        serial_handle = serial.Serial(port='/dev/ttyUSB0',baudrate=f_stack[-1],timeout=(f_stack[-2]))
    except TypeError:
        sys.exit(f_error.format(f="uinit"))
    finally:
        f_pop(f_stack,n=2)
        
def f_uwrite(f_stack, args=None):
    global serial_handle
    m = 0
    """
    usage: uwrite(xn,x...,x1,n)
    """
    try:
        m = f_stack[-1]
        debug_print('uwrite m:' + str(m))        
        if len(f_stack)<m+1:
            sys.exit(s_error)
        for i in range(2,m+1):
            debug_print('uwrite i:' + str(i))
            serial_handle.write(bytes([f_stack[(-1)*(i)]]))
    except TypeError:
        sys.exit(f_error.format(f="uwrite"))
    finally:
        f_pop(f_stack,n=m+1)
        pass

def f_uread(f_stack, args=None):
    global serial_handle
    """
    usage: uread
    """
    try:
        buf = serial_handle.read(1)
        if len(buf) > 0:
            f_put(f_stack,buf)
            f_put(f_stack,'1')            
        else:
            f_put(f_stack,'0')
            
    except TypeError:
        sys.exit(f_error.format(f="uread"))
    finally:
        pass

def f_rsensor(f_stack, args=None):
    """
    usage: rsensor
    """
    try:
        #print 'f_rsensor 1'
        rsensor()
        #print 'f_rsensor 2'
    except Exception as e:
        print('exception:',str(e))
        sys.exit(f_error.format(f="rsensor"))
    finally:
        #print 'f_rsensor 3'
        pass

        
def run_line(s, v_dict):
    s.strip()
    line = s.split()
    check = len(line)
    
    if check > 0 and line[0] == '#':
        return
        
    if (line[0] not in def_commands.keys()) or (check>2):
        sys.exit("Bad command syntax in \n\t{0}".format(s))
    command = line[0]
    if check>1:
        arguments = line[1]
    else:
        arguments = None
    

    def_commands[command](f_stack=v_dict, args=arguments)

def execute(lines):
    global ip_point
    global debug_switch
    #print('lines:' + str(lines))
    line_cnt = len(lines)
    i = 0
    while True:
    
        ip_point = None

        debug_print('DBG-> L%d-----------------------------' % i)
        debug_print('DBG-> line:' + str(lines[i]))
        debug_print('DBG-> before run stack:' + str(stack))
            
        run_line(lines[i],stack)
        

        debug_print('DBG-> after run stack:' + str(stack))        
            
        if (ip_point != None):
            i += int(ip_point)
        else:
            i += 1
            if i >= line_cnt:
                return
                
def_commands = { 
                 'put':f_put, 
                 'add':f_add,
                 'sub':f_sub,
                 'mul':f_mul,
                 'div':f_div,
                 'and':f_and,
                 'or':f_or,
                 'print':f_print,
                 'pop':f_pop,
                 'dup':f_dup,
                 'swap':f_swap,
                 'pow':f_pow,
                 'sqrt':f_sqrt,
                 'ior':f_ior,
                 'iow':f_iow,
                 'dup2':f_dup2,
                 'bufr':f_bufr,
                 'bufw':f_bufw,
                 'ifs':f_ifs,
                 'jmp':f_jmp,
                 'slp':f_sleep,
                 'dbg':f_dbg,
                 'uinit':f_uinit,
                 'uread':f_uread,
                 'uwrite':f_uwrite,
                 'rsensor':f_rsensor,
                 'showd':f_showd
               } 

def test_console():
    global ip_point
    lines = []
    print("Input file was not specified!")
    print("Going to command line mode. Enter 'q' or 'quit' to exit.")
    while True:
        command = raw_input("Please enter a command: ")
        lines.append(command)
        
        if command=='q' or command=='quit':
          sys.exit("Bye!")
        else:
            run_line(command, stack)

def execute_file(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    execute(lines)

if __name__ == '__main__':
    execute_file('ucode.txt')

