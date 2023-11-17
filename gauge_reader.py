import time
import datetime
import serial
import serial.tools.list_ports

print('Available ports:')
print([comport.device for comport in serial.tools.list_ports.comports()])

#Attempts to establish a serial connection to the specified port
def establishConnection(port):
    try:
        ser = serial.Serial(port, 9600, timeout=1, bytesize=serial.EIGHTBITS, parity='N', stopbits=serial.STOPBITS_ONE)
        return ser
    except:
        print('Could not establish connection to specified port')

#Queries the Pfeiffer TPG 361 gauge controller for the current pressure reading
def getPressure():
    ser.write(b'PR1\r\n')
    response = ser.readline()

    if repr(response) == "b'\\x06\\r\\n'":
        ser.write(b'\x05')
        pressure = repr(ser.readline()).split(',')[1].split('\\')[0]

    return float(pressure)

#Writes a pressure reading and timestamp to a log file
def write2File(filename, time, pressure):
    outputFile = open(filename, 'a')
    outputFile.write(f'{time}\t{pressure}\n')
    outputFile.close()

#Reads the pressure once every "sample_time" seconds and writes to a log file entitled "filename_datetime.txt"
def logPressures(sample_time):
    fileName = 'pressure_log'

    date = datetime.datetime.now().strftime("%m%d%y_%H%M")
    outputFile = open(f'{fileName}_{date}.txt', "w")
    outputFile.write('Time\tPressure (Torr)\n')
    outputFile.close()

    t0 = time.time()

    times = []
    pressures = []
    while True:
        current_time = time.time()
        current_pressure = getPressure()

        times.append(current_time)
        pressures.append(current_pressure)
        print(current_pressure)
        
        write2File(f'{fileName}_{date}.txt', current_time, current_pressure)

        time.sleep(sample_time)


#Attempts to begin logging pressures every 60 seconds using port
port = 'COM7'
ser = establishConnection(port)
logPressures(60)
    


