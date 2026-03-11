interfaces transceiver optical-transport
----------------------------------------

**Minimum user role:** operator

"The transceiver hierarchy supports various transceiver configuration options including:
- Different applications (as advertised by the transceiver)
- Coherent transceiver parameters configuration (optical frequency, output power etc.)"

**Command syntax: optical-transport**

**Command mode:** config

**Hierarchies**

- interfaces transceiver

**Note**

- The command is applicable to physical interfaces.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-2/1/1
    dnRouter(cfg-if-ge400-2/1/1)# transceiver
    dnRouter(cfg-if-ge100-2/1/1-trns)# optical-transport
    dnRouter(cfg-if-ge100-2/1/1-trns-optical-transport)#


**Removing Configuration**

To remove the optical-transport configuration:
::

    dnRouter(cfg-if-ge100-2/1/1-trns-optical-transport)# no optical-transport

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
