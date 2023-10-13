# Pico MicroPython: ADC test code
# See https://iosoft.blog/pico-adc-dma for description
#
# Copyright (c) 2021 Jeremy P Bentham
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time, array, uctypes, rp_devices as devs
import machine
import utime
import micropython
from machine import I2C, Pin, ADC, SPI, Timer
from time import sleep, sleep_ms
import math
import ulab
import DMA_ADC_library

sampleflag = False

def sampletrigger(Source):
    global sampleflag
    sampleflag = True

micropython.alloc_emergency_exception_buf(100) #interrupt delay which is why high rates can cause problems

spi = SPI(0, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck = Pin(2), mosi = Pin(3))
cs = Pin(1, mode=Pin.OUT, value=1) #chip select for DAC

time = 1 #seconds
samp_rate = 8000
samples = round(time*samp_rate)
send = bytearray([0x00, 0x00])
vals = [0]*samp_rate

global the_sampler
the_sampler = Timer(mode=Timer.PERIODIC, freq=samp_rate, callback=sampletrigger)

cs.value(1)

VR_Analog = ADC(Pin(26 + 1)) #ADC1
DMA_ADC_library.DMA_ADC_configure(1, samples, samp_rate)
    
while True:
    DMA_ADC_library.DMA_ADC_start()
    
    for i in range(len(vals)):
        while sampleflag == False:
            pass
        sampleflag = False
    
        send[0] = 0xF0 | (0x0F & (vals[i]) >> 8)
        send[1] = (vals[i] << 2) & 0xFF        
        cs.value(0)
        spi.write(send)
        cs.value(1)   
    
    DMA_ADC_library.DMA_ADC_wait()
    
    vals = DMA_ADC_library.DMA_ADC_getbuffer()