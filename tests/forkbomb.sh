#!/bin/bash

## NOTE: This program will hang the system after exhausting resources,
##		 it is being used only to test that the watchdog timer kernel
## 		 module is functioning properly; should reboot after timeout.

swapoff -a
f(){ f|f & };f
