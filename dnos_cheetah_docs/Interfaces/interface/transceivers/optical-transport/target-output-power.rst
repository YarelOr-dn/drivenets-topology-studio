interfaces transceiver optical-transport target-output-power
------------------------------------------------------------

**Minimum user role:** operator

Some coherent optics modules allow setting optical channel target output power. Power range is -20..10 and specified in dbm (dbm). To set the optical channel output power:

**Command syntax: target-output-power [target-output-power]**

**Command mode:** config

**Hierarchies**

- interfaces transceiver optical-transport

**Parameter table**

+---------------------+----------------------------------------------------+--------------+---------+
| Parameter           | Description                                        | Range        | Default |
+=====================+====================================================+==============+=========+
| target-output-power | Target optical output power range is -20..10 (dbm) | -20.00-10.00 | \-      |
+---------------------+----------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge400-2/1/1
    dnRouter(cfg-if-ge400-42/1/1)# transceiver
    dnRouter(cfg-if-ge400-4/1/1-trns)# optical-transport
    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# target-output-power -10


**Removing Configuration**

To revert target output power configuration to the default value:
::

    dnRouter(cfg-if-ge400-4/1/1-trns-optical-transport)# no target-output-power

**Command History**

+---------+--------------------------------+
| Release | Modification                   |
+=========+================================+
| 16.2    | Command introduced             |
+---------+--------------------------------+
| 18.0    | Units changed from dmbm to dbm |
+---------+--------------------------------+
