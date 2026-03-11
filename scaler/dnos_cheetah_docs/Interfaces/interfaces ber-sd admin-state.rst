interfaces ber-sd admin-state
-----------------------------

**Minimum user role:** operator

Sets the administrative state of the BER Signal Degrade alarm on the interface.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces ber-sd

**Note**
- The command is applicable only to 400G and 100G physical interfaces with FEC.
- By default all applicable interfaces are initialized with ber-sd admin-state disabled.
- When enabled and the configured ber-sd threshold is exceeded, then a system event shall be generated to notify of the violation, thus indicating signal degredation on the link.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Enable Signal Degrade BER and generate an alarm whenever the SD-BER threshold is | | enabled    | disabled |
|             | crossed for this interface                                                       | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sd admin-state enabled
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sd admin-state disabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sd admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
