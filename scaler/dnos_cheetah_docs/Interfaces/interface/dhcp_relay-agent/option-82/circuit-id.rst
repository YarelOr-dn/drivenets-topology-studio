interfaces dhcp relay-agent option-82 circuit-id
------------------------------------------------

**Minimum user role:** operator

To overwrite the default DHCP Relay Agent Information Option (option 82) circuit ID sub-option on the interface:

**Command syntax: circuit-id [circuit-id]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Note**

- Unless explicitly overwritten by the user, the default value is the interface-name.
- User configured string may only contain alphanumeric characters, underscores, hyphens, dots, forward slashes, backslashes and colons.

**Parameter table**

+------------+----------------------------------------------------------------------------------+-----------------+----------------+
| Parameter  | Description                                                                      | Range           | Default        |
+============+==================================================================================+=================+================+
| circuit-id | Encodes an agent-local identifier of the circuit from which a DHCP               | | string        | interface-name |
|            | client-to-server packet was received. It is intended for use by agents in        | | length 1-63   |                |
|            | relaying DHCP responses back to the proper circuit. The circuit ID is an opaque  |                 |                |
|            | value                                                                            |                 |                |
+------------+----------------------------------------------------------------------------------+-----------------+----------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# circuit-id myCircuit


**Removing Configuration**

To return DHCP relay agent information option circuit ID sub-option configuration on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no circuit-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
