show interfaces fabric transceiver
----------------------------------

**Minimum user role:** viewer

To display the list of values and configuration of the fabric interface transceiver, use the following command:

**Command syntax: show interfaces fabric transceiver** [interface-name]

**Command mode:** operational

**Note**

- This command is applicable to fabric interfaces.
- Command output will be identical between breakout interfaces of the same physical port.




**Parameter table**

+----------------+----------------------------------------------------------------------+--------------------+
| Parameter      | Description                                                          | Range              |
+================+======================================================================+====================+
| interface-name | Optionally filter the displayed information to a specific interface. | fab-ncp400-X/Y/Z   |
|                |                                                                      | fab-ncf400-X/Y/Z   |
|                |                                                                      | fab-ncp400-X/Y/Z/U |
|                |                                                                      | fab-ncf400-X/Y/Z/U |
+----------------+----------------------------------------------------------------------+--------------------+

**Example**
::

	dnRouter# show interfaces transceiver fab-ncp400-0/0/0

	Identifier                                : QSFP_DD
	Connector                                 : 0x23 (No separable connector)
	Transceiver class                         : Passive electrical
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 0m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 0m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Laser wavelength                          : 850 nm
	Laser wavelength tolerance                : 10 nm
	Vendor name                               : INNOLIGHT
	Vendor OUI                                : 44:7C:7F
	Vendor PN                                 : C-DQ8FNM010-N00
	Vendor rev                                : 1A
	Vendor SN                                 : INJAQ8090025B
	Revision compliance                       : QSFP-DD or QSFP-DD CMIS Rev 3.0
	Module temperature                        : 36.6 degrees C / 97.9 degrees F
	Module voltage                            : 3.3 V
	Alarm/warning flags implemented           : Yes
	Laser tx bias current (Channel 0)         : 7.7 mA
	Laser tx bias current (Channel 1)         : 7.7 mA
	Laser tx bias current (Channel 2)         : 7.7 mA
	Laser tx bias current (Channel 3)         : 7.7 mA
	Laser tx bias current (Channel 4)         : 7.7 mA
	Laser tx bias current (Channel 5)         : 7.7 mA
	Laser tx bias current (Channel 6)         : 7.7 mA
	Laser tx bias current (Channel 7)         : 7.7 mA
	Transmit avg optical power (Channel 0)    : 2.4 dBm
	Transmit avg optical power (Channel 1)    : 2.6 dBm
	Transmit avg optical power (Channel 2)    : 2.6 dBm
	Transmit avg optical power (Channel 3)    : 2.5 dBm
	Transmit avg optical power (Channel 4)    : 2.8 dBm
	Transmit avg optical power (Channel 5)    : 2.9 dBm
	Transmit avg optical power (Channel 6)    : 2.9 dBm
	Transmit avg optical power (Channel 7)    : 2.6 dBm
	Rcvr signal avg optical power (Channel 0) : 3.1 dBm
	Rcvr signal avg optical power (Channel 1) : 2.7 dBm
	Rcvr signal avg optical power (Channel 2) : 2.3 dBm
	Rcvr signal avg optical power (Channel 3) : 2.7 dBm
	Rcvr signal avg optical power (Channel 4) : 2.2 dBm
	Rcvr signal avg optical power (Channel 5) : 3.0 dBm
	Rcvr signal avg optical power (Channel 6) : 3.5 dBm
	Rcvr signal avg optical power (Channel 7) : 2.9 dBm
	Laser bias current high alarm (Chan 0)    : off
	Laser bias current low alarm (Chan 0)     : off
	Laser bias current high warning (Chan 0)  : off
	Laser bias current low warning (Chan 0)   : off
	Laser bias current high alarm (Chan 1)    : off
	Laser bias current low alarm (Chan 1)     : off
	Laser bias current high warning (Chan 1)  : off
	Laser bias current low warning (Chan 1)   : off
	Laser bias current high alarm (Chan 2)    : off
	Laser bias current low alarm (Chan 2)     : off
	Laser bias current high warning (Chan 2)  : off
	Laser bias current low warning (Chan 2)   : off
	Laser bias current high alarm (Chan 3)    : off
	Laser bias current low alarm (Chan 3)     : off
	Laser bias current high warning (Chan 3)  : off
	Laser bias current low warning (Chan 3)   : off
	Laser bias current high alarm (Chan 4)    : off
	Laser bias current low alarm (Chan 4)     : off
	Laser bias current high warning (Chan 4)  : off
	Laser bias current low warning (Chan 4)   : off
	Laser bias current high alarm (Chan 5)    : off
	Laser bias current low alarm (Chan 5)     : off
	Laser bias current high warning (Chan 5)  : off
	Laser bias current low warning (Chan 5)   : off
	Laser bias current high alarm (Chan 6)    : off
	Laser bias current low alarm (Chan 6)     : off
	Laser bias current high warning (Chan 6)  : off
	Laser bias current low warning (Chan 6)   : off
	Laser bias current high alarm (Chan 7)    : off
	Laser bias current low alarm (Chan 7)     : off
	Laser bias current high warning (Chan 7)  : off
	Laser bias current low warning (Chan 7)   : off
	Module temperature high alarm             : off
	Module temperature low alarm              : off
	Module temperature high warning           : off
	Module temperature low warning            : off
	Module voltage high alarm                 : off
	Module voltage low alarm                  : off
	Module voltage high warning               : off
	Module voltage low warning                : off
	Laser tx power high alarm (Channel 0)     : off
	Laser tx power low alarm (Channel 0)      : off
	Laser tx power high warning (Channel 0)   : off
	Laser tx power low warning (Channel 0)    : off
	Laser tx power high alarm (Channel 1)     : off
	Laser tx power low alarm (Channel 1)      : off
	Laser tx power high warning (Channel 1)   : off
	Laser tx power low warning (Channel 1)    : off
	Laser tx power high alarm (Channel 2)     : off
	Laser tx power low alarm (Channel 2)      : off
	Laser tx power high warning (Channel 2)   : off
	Laser tx power low warning (Channel 2)    : off
	Laser tx power high alarm (Channel 3)     : off
	Laser tx power low alarm (Channel 3)      : off
	Laser tx power high warning (Channel 3)   : off
	Laser tx power low warning (Channel 3)    : off
	Laser tx power high alarm (Channel 4)     : off
	Laser tx power low alarm (Channel 4)      : off
	Laser tx power high warning (Channel 4)   : off
	Laser tx power low warning (Channel 4)    : off
	Laser tx power high alarm (Channel 5)     : off
	Laser tx power low alarm (Channel 5)      : off
	Laser tx power high warning (Channel 5)   : off
	Laser tx power low warning (Channel 5)    : off
	Laser tx power high alarm (Channel 6)     : off
	Laser tx power low alarm (Channel 6)      : off
	Laser tx power high warning (Channel 6)   : off
	Laser tx power low warning (Channel 6)    : off
	Laser tx power high alarm (Channel 7)     : off
	Laser tx power low alarm (Channel 7)      : off
	Laser tx power high warning (Channel 7)   : off
	Laser tx power low warning (Channel 7)    : off
	Laser rx power high alarm (Channel 0)     : off
	Laser rx power low alarm (Channel 0)      : off
	Laser rx power high warning (Channel 0)   : off
	Laser rx power low warning (Channel 0)    : off
	Laser rx power high alarm (Channel 1)     : off
	Laser rx power low alarm (Channel 1)      : off
	Laser rx power high warning (Channel 1)   : off
	Laser rx power low warning (Channel 1)    : off
	Laser rx power high alarm (Channel 2)     : off
	Laser rx power low alarm (Channel 2)      : off
	Laser rx power high warning (Channel 2)   : off
	Laser rx power low warning (Channel 2)    : off
	Laser rx power high alarm (Channel 3)     : off
	Laser rx power low alarm (Channel 3)      : off
	Laser rx power high warning (Channel 3)   : off
	Laser rx power low warning (Channel 3)    : off
	Laser rx power high alarm (Channel 4)     : off
	Laser rx power low alarm (Channel 4)      : off
	Laser rx power high warning (Channel 4)   : off
	Laser rx power low warning (Channel 4)    : off
	Laser rx power high alarm (Channel 5)     : off
	Laser rx power low alarm (Channel 5)      : off
	Laser rx power high warning (Channel 5)   : off
	Laser rx power low warning (Channel 5)    : off
	Laser rx power high alarm (Channel 6)     : off
	Laser rx power low alarm (Channel 6)      : off
	Laser rx power high warning (Channel 6)   : off
	Laser rx power low warning (Channel 6)    : off
	Laser rx power high alarm (Channel 7)     : off
	Laser rx power low alarm (Channel 7)      : off
	Laser rx power high warning (Channel 7)   : off
	Laser rx power low warning (Channel 7)    : off
	Laser bias current high alarm threshold   : 15.0 mA
	Laser bias current low alarm threshold    : 4.5 mA
	Laser bias current high warning threshold : 13.0 mA
	Laser bias current low warning threshold  : 5.0 mA
	Laser output power high alarm threshold   : 5.5 dBm
	Laser output power low alarm threshold    : -3.5 dBm
	Laser output power high warning threshold : 4.5 dBm
	Laser output power low warning threshold  : -2.5 dBm
	Module temperature high alarm threshold   : 80.0 degrees C
	Module temperature low alarm threshold    : -10.0 degrees C
	Module temperature high warning threshold : 75.0 degrees C
	Module temperature low warning threshold  : -5.0 degrees C
	Module voltage high alarm threshold       : 3.6 V
	Module voltage low alarm threshold        : 3.0 V
	Module voltage high warning threshold     : 3.5 V
	Module voltage low warning threshold      : 3.1 V
	Laser rx power high alarm threshold       : 63.2 dBm
	Laser rx power low alarm threshold        : 1.3 dBm
	Laser rx power high warning threshold     : 50.2 dBm
	Laser rx power low warning threshold      : 2.0 dBm


.. **Help line:** show interfaces fabric transceiver values

**Command History**

+---------+-------------------------+
| Release | Modification            |
+=========+=========================+
| 11.4    | Command introduced      |
+---------+-------------------------+
| 18.2    | Added transceiver class |
+---------+-------------------------+
