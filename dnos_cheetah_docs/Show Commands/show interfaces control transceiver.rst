show interfaces control transceiver
-----------------------------------

**Minimum user role:** viewer

To display the list of values and configuration of the control interface transceiver, use the following command:

**Command syntax: show interfaces control transceiver** [interface-name]

**Command mode:** operational

**Parameter table**

+----------------+----------------------------------------------------------------------+--------------+---------+
| Parameter      | Description                                                          | Range        | Default |
+================+======================================================================+==============+=========+
| interface-name | Optionally filter the displayed information to a specific interface. | ctrl-ncp-x/y | \-      |
|                |                                                                      | ctrl-ncf-x/y |         |
|                |                                                                      | ctrl-ncc-x/y |         |
|                |                                                                      | ctrl-ncm-x/y |         |
+----------------+----------------------------------------------------------------------+--------------+---------+

**Example**
::

	dnRouter# show interfaces transceiver ctrl-ncm-A0/51

	Identifier                                : QSFP
	Connector                                 : MPO Parallel Optic
	Transceiver type                          : 10G
	Encoding                                  : 0x05 (64B/66B)
	Laser wavelength                          : 850.000nm
	Vendor name                               : Mellanox
	Vendor OUI                                : 00:02:c9
	Vendor PN                                 : MMA1B00-C100D
	Vendor rev                                : A3
	Vendor SN                                 : MT1652FT00065
	Module temperature                        : 47.11 degrees C / 116.79 degrees F
	Module voltage                            : 3.2531 V
	Laser tx bias current (Channel 0)         : 6.600 mA
	Laser tx bias current (Channel 1)         : 6.600 mA
	Laser tx bias current (Channel 2)         : 6.600 mA
	Laser tx bias current (Channel 3)         : 6.600 mA
	Transmit avg optical power (Channel 0)    : 0.9077 mW / -0.42 dBm
	Transmit avg optical power (Channel 1)    : 0.9700 mW / -0.13 dBm
	Transmit avg optical power (Channel 2)    : 0.9348 mW / -0.29 dBm
	Transmit avg optical power (Channel 3)    : 0.9736 mW / -0.12 dBm
	Rcvr signal avg optical power(Channel 0)  : 0.9522 mW / -0.21 dBm
	Rcvr signal avg optical power(Channel 1)  : 0.9039 mW / -0.44 dBm
	Rcvr signal avg optical power(Channel 2)  : 0.8316 mW / -0.80 dBm
	Rcvr signal avg optical power(Channel 3)  : 0.9042 mW / -0.44 dBm


	dnRouter# show interfaces transceiver ctrl-ncc-0/0

	Identifier                                : 0x11 (QSFP28)
	Extended identifier                       : 0x8c
	Extended identifier description           : 2.5W max. Power consumption
	Extended identifier description           : CDR present in TX, CDR present in RX
	Extended identifier description           : High Power Class (> 3.5 W) not enabled
	Connector                                 : 0x0c (MPO Parallel Optic)
	Transceiver codes                         : 0x80 0x00 0x00 0x00 0x00 0x00 0x00 0x00
	Transceiver type                          : 10G
	Encoding                                  : 0x05 (64B/66B)
	BR, Nominal                               : 25500Mbps
	Rate identifier                           : 0x00
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 70m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 50m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Laser wavelength                          : 850.000nm
	Laser wavelength tolerance                : 15.000nm
	Vendor name                               : Mellanox
	Vendor OUI                                : 00:02:c9
	Vendor PN                                 : MMA1B00-C100D
	Vendor rev                                : A3
	Vendor SN                                 : MT1652FT00065
	Revision Compliance                       : SFF-8636 Rev 2.0
	Module temperature                        : 47.11 degrees C / 116.79 degrees F
	Module voltage                            : 3.2531 V
	Alarm/warning flags implemented           : Yes
	Laser tx bias current (Channel 0)         : 6.600 mA
	Laser tx bias current (Channel 1)         : 6.600 mA
	Laser tx bias current (Channel 2)         : 6.600 mA
	Laser tx bias current (Channel 3)         : 6.600 mA
	Transmit avg optical power (Channel 0)    : 0.9077 mW / -0.42 dBm
	Transmit avg optical power (Channel 1)    : 0.9700 mW / -0.13 dBm
	Transmit avg optical power (Channel 2)    : 0.9348 mW / -0.29 dBm
	Transmit avg optical power (Channel 3)    : 0.9736 mW / -0.12 dBm
	Rcvr signal avg optical power(Channel 0)  : 0.9522 mW / -0.21 dBm
	Rcvr signal avg optical power(Channel 1)  : 0.9039 mW / -0.44 dBm
	Rcvr signal avg optical power(Channel 2)  : 0.8316 mW / -0.80 dBm
	Rcvr signal avg optical power(Channel 3)  : 0.9042 mW / -0.44 dBm
	Laser bias current high alarm   (Chan 0)  : Off
	Laser bias current low alarm    (Chan 0)  : Off
	Laser bias current high warning (Chan 0)  : Off
	Laser bias current low warning  (Chan 0)  : Off
	Laser bias current high alarm   (Chan 1)  : Off
	Laser bias current low alarm    (Chan 1)  : Off
	Laser bias current high warning (Chan 1)  : Off
	Laser bias current low warning  (Chan 1)  : Off
	Laser bias current high alarm   (Chan 2)  : Off
	Laser bias current low alarm    (Chan 2)  : Off
	Laser bias current high warning (Chan 2)  : Off
	Laser bias current low warning  (Chan 2)  : Off
	Laser bias current high alarm   (Chan 3)  : Off
	Laser bias current low alarm    (Chan 3)  : Off
	Laser bias current high warning (Chan 3)  : Off
	Laser bias current low warning  (Chan 3)  : Off
	Module temperature high alarm             : Off
	Module temperature low alarm              : Off
	Module temperature high warning           : Off
	Module temperature low warning            : Off
	Module voltage high alarm                 : Off
	Module voltage low alarm                  : Off
	Module voltage high warning               : Off
	Module voltage low warning                : Off
	Laser tx power high alarm   (Channel 0)   : Off
	Laser tx power low alarm    (Channel 0)   : Off
	Laser tx power high warning (Channel 0)   : Off
	Laser tx power low warning  (Channel 0)   : Off
	Laser tx power high alarm   (Channel 1)   : Off
	Laser tx power low alarm    (Channel 1)   : Off
	Laser tx power high warning (Channel 1)   : Off
	Laser tx power low warning  (Channel 1)   : Off
	Laser tx power high alarm   (Channel 2)   : Off
	Laser tx power low alarm    (Channel 2)   : Off
	Laser tx power high warning (Channel 2)   : Off
	Laser tx power low warning  (Channel 2)   : Off
	Laser tx power high alarm   (Channel 3)   : Off
	Laser tx power low alarm    (Channel 3)   : Off
	Laser tx power high warning (Channel 3)   : Off
	Laser tx power low warning  (Channel 3)   : Off
	Laser rx power high alarm   (Channel 0)   : Off
	Laser rx power low alarm    (Channel 0)   : Off
	Laser rx power high warning (Channel 0)   : Off
	Laser rx power low warning  (Channel 0)   : Off
	Laser rx power high alarm   (Channel 1)   : Off
	Laser rx power low alarm    (Channel 1)   : Off
	Laser rx power high warning (Channel 1)   : Off
	Laser rx power low warning  (Channel 1)   : Off
	Laser rx power high alarm   (Channel 2)   : Off
	Laser rx power low alarm    (Channel 2)   : Off
	Laser rx power high warning (Channel 2)   : Off
	Laser rx power low warning  (Channel 2)   : Off
	Laser rx power high alarm   (Channel 3)   : Off
	Laser rx power low alarm    (Channel 3)   : Off
	Laser rx power high warning (Channel 3)   : Off
	Laser rx power low warning  (Channel 3)   : Off
	Laser bias current high alarm threshold   : 0.000 mA
	Laser bias current low alarm threshold    : 0.000 mA
	Laser bias current high warning threshold : 0.000 mA
	Laser bias current low warning threshold  : 0.000 mA
	Laser output power high alarm threshold   : 0.0000 mW / -inf dBm
	Laser output power low alarm threshold    : 0.0000 mW / -inf dBm
	Laser output power high warning threshold : 0.0000 mW / -inf dBm
	Laser output power low warning threshold  : 0.0000 mW / -inf dBm
	Module temperature high alarm threshold   : 0.00 degrees C / 32.00 degrees F
	Module temperature low alarm threshold    : 0.00 degrees C / 32.00 degrees F
	Module temperature high warning threshold : 0.00 degrees C / 32.00 degrees F
	Module temperature low warning threshold  : 0.00 degrees C / 32.00 degrees F
	Module voltage high alarm threshold       : 0.0000 V
	Module voltage low alarm threshold        : 0.0000 V
	Module voltage high warning threshold     : 0.0000 V
	Module voltage low warning threshold      : 0.0000 V
	Laser rx power high alarm threshold       : 0.0000 mW / -inf dBm
	Laser rx power low alarm threshold        : 0.0000 mW / -inf dBm
	Laser rx power high warning threshold     : 0.0000 mW / -inf dBm
	Laser rx power low warning threshold      : 0.0000 mW / -inf dBm

.. **Help line:** show interfaces fabric transceiver values

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 1.4     | Command introduced |
+---------+--------------------+
