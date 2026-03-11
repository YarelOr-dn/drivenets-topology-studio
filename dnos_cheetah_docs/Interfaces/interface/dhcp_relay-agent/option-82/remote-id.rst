interfaces dhcp relay-agent option-82 remote-id
-----------------------------------------------

**Minimum user role:** operator

To overwrite the default DHCP Relay Agent Information Option (option 82) remote ID sub-option on the interface:

**Command syntax: remote-id [remote-id]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Note**

- Unless explicitly overwritten by the user, the default value is the MAC address of the relaying port.
- User configured string may only contain alphanumeric characters, underscores, hyphens, dots, forward slashes, backslashes and colons.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+-----------------+-------------+
| Parameter | Description                                                                      | Range           | Default     |
+===========+==================================================================================+=================+=============+
| remote-id | Provides a mechanism to identify the remote host end of the circuit. The remote  | | string        | MAC address |
|           | ID should be thought of as an opaque value, but must be globally unique          | | length 1-63   |             |
+-----------+----------------------------------------------------------------------------------+-----------------+-------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# remote-id myRemoteID


**Removing Configuration**

To return DHCP relay agent information option remote ID sub-option configuration on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no remote-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
