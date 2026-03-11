interfaces transceiver optical-transport grid-spacing
-----------------------------------------------------

**Minimum user role:** operator

Some coherent optics modules allow setting optical channel grid spacing. Frequency grid is specified in GHz according to Rec. ITU-T G.694.1. To set the optical channel grid-spacing:

**Command syntax: grid-spacing [grid-spacing]**

**Command mode:** config

**Hierarchies**

- interfaces transceiver optical-transport

**Parameter table**

+--------------+------------------------------+--------------+---------+
| Parameter    | Description                  | Range        | Default |
+==============+==============================+==============+=========+
| grid-spacing | Optical channel grid-spacing | | 3.125GHz   | \-      |
|              |                              | | 6.25GHz    |         |
|              |                              | | 12.5GHz    |         |
|              |                              | | 25GHz      |         |
|              |                              | | 33GHz      |         |
|              |                              | | 50GHz      |         |
|              |                              | | 75GHz      |         |
|              |                              | | 100GHz     |         |
+--------------+------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-2/1/1
    dnRouter(cfg-if-ge400-42/1/1)# transceiver
    dnRouter(cfg-if-ge400-4/1/1-trns)# optical-transport
    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# grid-spacing 100GHz


**Removing Configuration**

To revert the grid spacing configuration to the default value:
::

    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# no grid-spacing

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
