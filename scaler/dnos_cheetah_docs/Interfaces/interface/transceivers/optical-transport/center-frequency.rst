interfaces transceiver optical-transport center-frequency
---------------------------------------------------------

**Minimum user role:** operator

Some coherent optics modules allow setting optical channel frequency. Frequency grid is specified in GHz according to Rec. ITU-T G.694.1. To set the optical channel frequency:

**Command syntax: center-frequency [center-frequency] [units]**

**Command mode:** config

**Hierarchies**

- interfaces transceiver optical-transport

**Note**
- No decimals allowed only whole numbers in mhz,ghz,thz.

**Parameter table**

+------------------+----------------------------------+--------------+---------+
| Parameter        | Description                      | Range        | Default |
+==================+==================================+==============+=========+
| center-frequency | Optical channel center frequency | 0-4294967295 | \-      |
+------------------+----------------------------------+--------------+---------+
| units            |                                  | | mhz        | mhz     |
|                  |                                  | | ghz        |         |
|                  |                                  | | thz        |         |
+------------------+----------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-2/1/1
    dnRouter(cfg-if-ge400-42/1/1)# transceiver
    dnRouter(cfg-if-ge400-4/1/1-trns)# optical-transport
    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# center-frequency 193100


**Removing Configuration**

To revert the center frequency configuration to the default value:
::

    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# no center-frequency

**Command History**

+---------+-------------------------+
| Release | Modification            |
+=========+=========================+
| 16.2    | Command introduced      |
+---------+-------------------------+
| 18.1    | Removed frequency range |
+---------+-------------------------+
