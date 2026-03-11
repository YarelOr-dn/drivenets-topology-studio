interfaces dhcp relay-agent option-82 allow-untrusted
-----------------------------------------------------

**Minimum user role:** operator

To allow untrusted client requests with DHCP Relay Agent Information Option (option 82) on the interface:

**Command syntax: allow-untrusted [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Note**

- Default behavior when the relay agent receives a DHCP packet with giaddr zero is to drop it, unless allow-untrusted mode is enabled.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | Received DHCP packets may contain Relay Agent Information Option with giaddr     | | enabled    | disabled |
|             | zero                                                                             | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# allow-untrusted enabled


**Removing Configuration**

To return DHCP relay agent information option allow-untrusted configuration on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no allow-untrusted

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
