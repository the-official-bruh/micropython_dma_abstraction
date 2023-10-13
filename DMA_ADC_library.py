# DMA_ADC_library by Shane Aspenwall
# A continuation of Jeremy P Bentham's test script for DMA on Micropython

# DMA_ADC_configure(ADC channel, samples, sample rate)
    # sets up DMA for the selected ADC

# DMA_ADC_start()
    # send the command to begin the DMA transfer from the ADC to the buffer array
    
# DMA_ADC_wait()
    # will wait until DMA has completed a transfer

# DMA_ADC_getbuffer()
    # returns the buffer array

#==============================================================================================
    
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
#

import time, array, uctypes, rp_devices as devs
import sys

def DMA_ADC_configure(channel, samples, sample_rate):
    global dma_chan
    global adc
    global buffer_array
    global NSAMPLES
    global DMA_CHAN
    
    # Fetch single ADC sample
    if ((channel < 0) or (channel > 2)):
        print(f"ERROR! DMA_ADC_configure - Channel number [{channel}] invalid")
        sys.exit(0)
    if sample_rate > 10000:
        print(f"WARNING! DMA_ADC_configure - Sample rate [{sample_rate}] is > 10000 sam/sec, this is too fast to operate properly!")
        sys.exit(0)
    if samples > sample_rate:
        print(f"WARNING! DMA_ADC_configure - Sample size [{samples}] will store more than 1 second, you risk running out of storage!")
        sys.exit(0)
        
    ADC_CHAN = int(round(channel))
    ADC_PIN  = 26 + ADC_CHAN

    adc = devs.ADC_DEVICE
    pin = devs.GPIO_PINS[ADC_PIN]
    pad = devs.PAD_PINS[ADC_PIN]
    pin.GPIO_CTRL_REG = devs.GPIO_FUNC_NULL
    pad.PAD_REG = 0

    adc.CS_REG = adc.FCS_REG = 0
    adc.CS.EN = 1
    adc.CS.AINSEL = ADC_CHAN
    adc.CS.START_ONCE = 1
    #print(adc.RESULT_REG)

    # Multiple ADC samples using DMA
    DMA_CHAN = 0
    NSAMPLES = int(round(samples))
    RATE = int(round(sample_rate))
    dma_chan = devs.DMA_CHANS[DMA_CHAN]
    dma = devs.DMA_DEVICE

    adc.FCS.EN = adc.FCS.DREQ_EN = 1
    buffer_array = array.array('H', (0 for _ in range(NSAMPLES)))
    adc.DIV_REG = (48000000 // RATE - 1) << 8
    adc.FCS.THRESH = adc.FCS.OVER = adc.FCS.UNDER = 1
    #print(f"ADC [{ADC_CHAN}] -> DMA0 setup successfully")

def DMA_ADC_start():
    global dma_chan
    global buffer_array
    global NSAMPLES
    global DMA_CHAN
    global adc
    
    dma_chan.READ_ADDR_REG = devs.ADC_FIFO_ADDR
    dma_chan.WRITE_ADDR_REG = uctypes.addressof(buffer_array)
    dma_chan.TRANS_COUNT_REG = NSAMPLES

    dma_chan.CTRL_TRIG_REG = 0
    dma_chan.CTRL_TRIG.CHAIN_TO = DMA_CHAN
    dma_chan.CTRL_TRIG.INCR_WRITE = dma_chan.CTRL_TRIG.IRQ_QUIET = 1
    dma_chan.CTRL_TRIG.TREQ_SEL = devs.DREQ_ADC
    dma_chan.CTRL_TRIG.DATA_SIZE = 1
    dma_chan.CTRL_TRIG.EN = 1
    
    while adc.FCS.LEVEL:
        x = adc.FIFO_REG
        
    adc.CS.START_MANY = 1
    
def DMA_ADC_wait():
    global dma_chan
    global adc
    
    while dma_chan.CTRL_TRIG.BUSY:
        time.sleep_us(10)
    adc.CS.START_MANY = 0
    dma_chan.CTRL_TRIG.EN = 0
    #print("DMA Captured Data to buffer_array complete!")
    
def DMA_ADC_getbuffer():
    global buffer_array
    return buffer_array