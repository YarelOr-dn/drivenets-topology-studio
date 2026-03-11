interfaces ber-sd threshold
---------------------------

**Minimum user role:** operator

Sets the Bit Error Rate threshold for the Signal Degrade alarm on the interface.

**Command syntax: threshold [signal-degrade-threshold]**

**Command mode:** config

**Hierarchies**

- interfaces ber-sd

**Note**
- The command is applicable only to 400G and 100G physical interfaces with FEC.
- By default the Signal Degrade Bit Error Rate threshold is set to 1e-8.
- When enabled and the configured ber-sd threshold is exceeded, then a system event shall be generated to notify of the violation, thus indicating signal degradation on the link.

**Parameter table**

+--------------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter                | Description                                                                      | Range | Default |
+==========================+==================================================================================+=======+=========+
| signal-degrade-threshold | Set the Signal Degrade bit error rate threshold on an interface to a value of    | 5-13  | 8       |
|                          | 1e-x, where x is the value passed in here                                        |       |         |
+--------------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sd threshold 11


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sd threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
