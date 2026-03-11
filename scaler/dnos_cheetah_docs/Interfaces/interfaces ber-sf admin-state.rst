interfaces ber-sf admin-state
-----------------------------

**Minimum user role:** operator

Sets the administrative state of the BER Signal Failure alarm on the interface.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces ber-sf

**Note**
- The command is applicable only to 400G and 100G physical interfaces with FEC.
- By default all applicable interfaces are initialized with ber-sf admin-state enabled.
- When enabled and the configured ber-sf threshold is exceeded, then a system event shall be generated to notify of the violation, thus indicating signal failure on the link, the interface shall transition to operational down state, and a remote fault signal shall be sent to the peer.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Disable Signal Failure BER and the generation of an alarm whenever the SF-BER    | | enabled    | disabled |
|             | threshold is crossed for this interface                                          | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sf admin-state disabled

    dnRouter(cfg-if)# ge100-1/1/1
    dnRouter(cfg-if-ge100-1/1/1)# ber-sf admin-state enabled


**Removing Configuration**

To revert to the default state:
::

    dnRouter(cfg-if-ge100-1/1/1)# no ber-sf admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
