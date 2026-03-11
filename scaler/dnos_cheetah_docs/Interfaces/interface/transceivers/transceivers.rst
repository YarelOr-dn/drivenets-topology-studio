interfaces transceiver
----------------------

**Minimum user role:** operator

The transceiver hierarchy supports various transceiver configuration options including:
- Different applications (as advertised by the transceiver)
- Coherent transceiver parameters configuration (optical frequency, output power etc.)

**Command syntax: transceiver**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to physical interfaces.

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-2/1/1
    dnRouter(cfg-if-ge400-2/1/1)# transceiver


**Removing Configuration**

::

    dnRouter(cfg-if-ge100-2/1/1-trns)# no transceiver

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.2    | Command introduced |
+---------+--------------------+
