show interfaces transceiver
---------------------------

**Minimum user role:** viewer



To display the list of values and configuration of the interface transceiver, use the following command:

**Command syntax: show interfaces transceiver** [interface-name]

**Command mode:** operational



**Note**

- This command is applicable to physical interfaces.

- "Transceiver not present" means that the transceiver is not connected to the interface.

- For 10GE interfaces the channel number of the parent interface is printed out, as well as the parent's information. 10GE transceiver information is not included in the output if the interface is not specified in 'show interfaces tranceiver' command.


**Parameter table**

+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+---------------+
| Parameter      | Description                                                                                                                                                    | Values                         | Default value |
+================+================================================================================================================================================================+================================+===============+
| interface-name | The name of the interface for which to display the transceiver parameters. If an interface is not specified, all transceivers in the system will be displayed. | ge<interface speed>-<A>/<B>/<C>| \-            |
|                |                                                                                                                                                                | geX-<f>/<n>/<p>/<b>            |               |
+----------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------+---------------+

**Example**
::

	dnRouter# show interfaces transceiver ge100-1/8/1

	Identifier                                : 0x11 (QSFP28)
	Extended identifier                       : 0x8c
	Extended identifier description           : 2.5W max. Power consumption
	Extended identifier description           : CDR present in TX, CDR present in RX
	Extended identifier description           : High Power Class (> 3.5 W) not enabled
	Connector                                 : 0x0c (MPO Parallel Optic)
	Transceiver codes                         : 0x80 0x00 0x00 0x00 0x00 0x00 0x00 0x00
	Transceiver type                          : 100G Ethernet: 100G Base-SR4 or 25GBase-SR
	Encoding                                  : 0x05 (64B/66B)
	BR, Nominal                               : 25500Mbps
	Rate identifier                           : 0x00
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 70m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 50m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Optical transport info                    : NA
	Configured Tx Power                       : NA
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
	Chromatic dispersion (min / avg / max)    : NA
	Pre-fec-ber (curr / min / avg / max)      : NA
	Post-fec-ber (FERC)                       : NA
	Q (curr)                                  : NA
	Osnr (min / avg / max)                    : NA

	Active application: 100GBASE-SR4
	Supported applications: 100GBASE-SR4

	dnRouter# show interfaces transceiver ge10-1/0/1/1

	Interface ge10-1/0/1/1 is a breakup port of its parent interface ge100-1/0/1, using channel 1.

	Transceiver information of parent interface ge100-1/0/1 is shown below.

	Identifier                                : 0x13 (QSFP+)
	Extended identifier                       : 0xD
	Extended identifier description           : 2.5W max. Power consumption
	Extended identifier description           : CDR present in TX, CDR present in RX
	Extended identifier description           : High Power Class (> 3.5 W) not enabled
	Connector                                 : 0x0c (MPO Parallel Optic)
	Transceiver codes                         : 0x80 0x00 0x00 0x00 0x00 0x00 0x00 0x00
	Transceiver type                          : 40G Ethernet: 40G Base-SR4
	Encoding                                  : 0x05 (64B/66B)
	BR, Nominal                               : 25500Mbps
	Rate identifier                           : 0x00
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 70m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 50m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Optical transport info                    : NA
	Configured Tx Power                       : NA
	Laser wavelength                          : 850.000nm
	Laser wavelength tolerance                : 15.000nm
	Vendor name                               : Aperture Science
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

	dnRouter# show interfaces transceiver ge400-0/0/4

	Identifier                                : QSFP_DD
	Connector                                 : 0x23 (No separable connector)
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 0m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 0m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Optical transport info                    : NA
	Configured Tx Power                       : NA
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
	Chromatic dispersion (min / avg / max)    : NA
	Pre-fec-ber (curr / min / avg / max)      : NA
	Post-fec-ber (FERC)                       : NA
	Q (curr)                                  : NA
	Osnr (min / avg / max)                    : NA

	Active application: NA
	Supported applications: NA

	dnRouter# show interfaces transceiver ge400-11/0/2

	Interface ge400-11/0/2
	Identifier                                : QSFP_DD
	Connector                                 : 0x7 (LC type fiber connector)
	Length (SMF,km)                           : 63km
	Length (OM3 50um)                         : 0m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 0m
	Transmitter technology                    : 0x05 1550 nm DFB
	Optical transport info                    : 75MHz-grid, Frequency = 192.15 THz
	Configured tx power                       : -10.00 dBm
	Laser wavelength                          : 1547 nm
	Laser wavelength tolerance                : 166 nm
	Vendor name                               : Acacia Comm Inc.
	Vendor OUI                                : 7C:B2:5C
	Vendor PN                                 : DP04QSDD-E30-001
	Vendor rev                                : A
	Vendor SN                                 : 212254212
	Revision compliance                       : QSFP-DD or QSFP-DD CMIS Rev 4.1
	Firmware version                          : 61.22
	Module temperature                        : 37.0 degrees C / 98.6 degrees F
	Module voltage                            : 3.3 V
	Alarm/warning flags implemented           : Yes
	Laser tx bias current (Channel 0)         : 69.1 mA
	Transmit avg optical power (Channel 0)    : -7.7 dBm / 0.2 mW
	Rcvr signal avg optical power (Channel 0) : -60.0 dBm / 0.0 mW
	Laser bias current high alarm (Chan 0)    : on
	Laser bias current low alarm (Chan 0)     : off
	Laser bias current high warning (Chan 0)  : on
	Laser bias current low warning (Chan 0)   : off
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
	Laser rx power high alarm (Channel 0)     : off
	Laser rx power low alarm (Channel 0)      : on
	Laser rx power high warning (Channel 0)   : off
	Laser rx power low warning (Channel 0)    : on
	Laser bias current high alarm threshold   : 0.0 mA
	Laser bias current low alarm threshold    : 0.0 mA
	Laser bias current high warning threshold : 0.0 mA
	Laser bias current low warning threshold  : 0.0 mA
	Laser output power high alarm threshold   : 0.0 dBm / 1.0 mW
	Laser output power low alarm threshold    : -18.0 dBm / 0.0 mW
	Laser output power high warning threshold : -2.0 dBm / 0.6 mW
	Laser output power low warning threshold  : -16.0 dBm / 0.0 mW
	Module temperature high alarm threshold   : 80.0 degrees C / 176.0 degrees F
	Module temperature low alarm threshold    : -5.0 degrees C / 23.0 degrees F
	Module temperature high warning threshold : 75.0 degrees C / 167.0 degrees F
	Module temperature low warning threshold  : 15.0 degrees C / 59.0 degrees F
	Module voltage high alarm threshold       : 3.5 V
	Module voltage low alarm threshold        : 3.1 V
	Module voltage high warning threshold     : 3.4 V
	Module voltage low warning threshold      : 3.2 V
	Laser rx power high alarm threshold       : 2.0 dBm / 1.6 mW
	Laser rx power low alarm threshold        : -28.2 dBm / 0.0 mW
	Laser rx power high warning threshold     : 0.0 dBm / 1.0 mW
	Laser rx power low warning threshold      : -23.0 dBm / 0.0 mW
	Chromatic dispersion (min / avg / max)    : -217 / 150 / 1700 ps/nm
	Pre-fec-ber (curr / min / avg / max)      : 1.5e-6  / 2.31e-18 / 4.1e-17 / 4.0e-5
	Post-fec-ber (FERC)                       : 0.5e-20 / 1.2e-21  / 2.0e-19 / 1.1e-15
	Q (curr)                                  : 3.4 dB
	Osnr (min / avg / max)                    : 15.2 / 19.0 / 27.5 dB

	Supported applications:
	1. 400ZR, DWDM, amplified
	2. 400ZR, Single Wavelength, Unamplified
	3. ZR400-OFEC-16QAM
	4. ZR300-OFEC-8QAM
	5. ZR200-OFEC-QPSK
	6. ZR100-OFEC-QPSK

	dnRouter# show interfaces transceiver ge100-0/0/4/1

	Interface ge100-0/0/4/1 is a breakup port of its parent interface ge400-0/0/4, using optical channel 1.

	Transceiver information of parent interface ge400-0/0/4 is shown below.

	Identifier                                : QSFP_DD
	Connector                                 : 0x23 (No separable connector)
	Length (SMF,km)                           : 0km
	Length (OM3 50um)                         : 0m
	Length (OM2 50um)                         : 0m
	Length (OM1 62.5um)                       : 0m
	Length (Copper or Active cable)           : 0m
	Transmitter technology                    : 0x00 (850 nm VCSEL)
	Optical transport info                    : NA
	Configured Tx Power                       : NA
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
	Chromatic dispersion (min / avg / max)    : NA
	Pre-fec-ber (curr / min / avg / max)      : NA
	Post-fec-ber (FERC)                       : NA
	Q (curr)                                  : NA
	Osnr (min / avg / max)                    : NA

	Active application: NA
	Supported applications: NA

	dnRouter# show interfaces transceiver ge400-0/0/6

	Interface ge400-0/0/6
	Identifier                                    : QSFP_DD
	Connector                                     : 0x7 (LC type fiber connector)
	Transceiver class                             : active-optical
	Length (SMF,km)                               : 630.0km
	Transmitter technology                        : 0x00 850 nm VCSEL
	Optical transport info                        : Grid 100GHz, Frequency 193.1 THz
	Configured Tx Power                           : 0.0 dBm
	Laser wavelength                              : 1547 nm
	Laser wavelength tolerance                    : 166 nm
	Vendor name                                   : CISCO-ACACIA
	Vendor OUI                                    : 7C:B2:5C
	Vendor PN                                     : DP04QSDD-HE0-001
	Vendor rev                                    : A
	Vendor SN                                     : 231152314
	Firmware version                              : 70.120
	Revision compliance                           : QSFP-DD or QSFP-DD CMIS Rev 5.0
	Module temperature                            : 61.0 degrees C / 141.8 degrees F
	Module voltage                                : 3.2 V
	Alarm/warning flags implemented               : Yes
	Laser tx bias current (Channel 0)             : 246.0 mA
	Transmit avg optical power (Channel 0)        : 0.0 dBm / 1.0 mW
	Rcvr signal avg optical power (Channel 0)     : -0.4 dBm / 0.9 mW
	Laser bias current high alarm (Chan 0)        : on
	Laser bias current low alarm (Chan 0)         : off
	Laser bias current high warning (Chan 0)      : on
	Laser bias current low warning (Chan 0)       : off
	Module temperature high alarm                 : off
	Module temperature low alarm                  : off
	Module temperature high warning               : off
	Module temperature low warning                : off
	Module voltage high alarm                     : off
	Module voltage low alarm                      : off
	Module voltage high warning                   : off
	Module voltage low warning                    : off
	Laser tx power high alarm (Channel 0)         : off
	Laser tx power low alarm (Channel 0)          : off
	Laser tx power high warning (Channel 0)       : off
	Laser tx power low warning (Channel 0)        : off
	Laser rx power high alarm (Channel 0)         : off
	Laser rx power low alarm (Channel 0)          : off
	Laser rx power high warning (Channel 0)       : off
	Laser rx power low warning (Channel 0)        : off
	Laser bias current high alarm threshold       : 0.0 mA
	Laser bias current low alarm threshold        : 0.0 mA
	Laser bias current high warning threshold     : 0.0 mA
	Laser bias current low warning threshold      : 0.0 mA
	Laser output power high alarm threshold       : 6.0 dBm / 4.0 mW
	Laser output power low alarm threshold        : -18.0 dBm / 0.0 mW
	Laser output power high warning threshold     : 4.0 dBm / 2.5 mW
	Laser output power low warning threshold      : -16.0 dBm / 0.0 mW
	Module temperature high alarm threshold       : 83.0 degrees C / 181.4 degrees F
	Module temperature low alarm threshold        : -5.0 degrees C / 23.0 degrees F
	Module temperature high warning threshold     : 78.0 degrees C / 172.4 degrees F
	Module temperature low warning threshold      : 15.0 degrees C / 59.0 degrees F
	Module voltage high alarm threshold           : 3.5 V
	Module voltage low alarm threshold            : 3.1 V
	Module voltage high warning threshold         : 3.4 V
	Module voltage low warning threshold          : 3.2 V
	Laser rx power high alarm threshold           : 8.0 dBm / 6.3 mW
	Laser rx power low alarm threshold            : -32.2 dBm / 0.0 mW
	Laser rx power high warning threshold         : 6.0 dBm / 4.0 mW
	Laser rx power low warning threshold          : -28.2 dBm / 0.0 mW
	Chromatic dispersion (min / avg / max)        : -2 / 0 / 1 ps/nm
	Pre-fec-ber (curr / min / avg / max)          : 2.050e-04 / 1.770e-04 / 2.050e-04 / 2.360e-04
	Post-fec-ber (FERC) (curr / min / avg / max)  : 0.000e+00 / 0.000e+00 / 0.000e+00 / 0.000e+00
	Q (curr)                                      : 10.90 dB
	Osnr (min / avg / max)                        : 356.000 / 356.000 / 356.000 dB

	Transceiver state                             : up
	Supported grids                               : 100 GHz, 75 GHz
	Frequency range supported with 100 GHz grid   : 191.5 THz - 194.3 THz
	Frequency range supported with 75 GHz grid    : 190.75THz - 195.5 THz
	Configurable Tx power supported range         : -18.3 dBm - 3.25 dBm


	Active application                            : ZR400-OFEC-16QAM
	Supported applications:
	1. 400ZR-amplified
	2. 400ZR-unamplified
	3. ZR400-OFEC-16QAM

	Configuration:
	Application                                 : ZR400-OFEC-16QAM
	Frequency                                   : N/A
	Grid spacing                                : N/A
	Target output power                         : 0.0 dBm

.. **Help line:** show interfaces transceiver values

**Command History**

+---------+------------------------------------------------------+
| Release | Modification                                         |
+=========+======================================================+
| 5.1.0   | Command introduced                                   |
+---------+------------------------------------------------------+
| 10.0    | Syntax changed                                       |
+---------+------------------------------------------------------+
| 12.0    | Added support for interfaces breakout                |
+---------+------------------------------------------------------+
| 16.1    | Added support for 400GE breakout                     |
+---------+------------------------------------------------------+
| 16.2    | Added supported applications and coherent parameters |
+---------+------------------------------------------------------+
| 17.1    | Added firmware version for CMIS 4.0 and newer        |
+---------+------------------------------------------------------+
