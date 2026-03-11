interfaces ber-sf threshold
---------------------------

**Minimum user role:** operator

Sets the Bit Error Rate threshold for the Signal Failure alarm on the interface.

**Command syntax: threshold [signal-fail-threshold]**

**Command mode:** config

**Hierarchies**

- interfaces ber-sf

**Note**
- The command is applicable only to 400G and 100G physical interfaces with FEC.
- By default the Signal Failure Bit Error Rate threshold is set to 1e-5.
- When enabled and the configured ber-sf threshold is exceeded, then a system event shall be generated to notify of the violation, thus indicating signal failure on the link, the interface shall transition to operational down state, and a remote fault signal shall be sent to the peer.

**Parameter table**

+-----------------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter             | Description                                                                      | Range | Default |
+=======================+==================================================================================+=======+=========+
| signal-fail-threshold | Set the Signal Failure bit error rate threshold on an interface to a value of    | 5-13  | 5       |
|                       | 1e-x, where x is the value passed in here                                        |       |         |
+-----------------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sf threshold 6


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sf threshold

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
