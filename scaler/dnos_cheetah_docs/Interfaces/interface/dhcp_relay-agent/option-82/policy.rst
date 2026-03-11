interfaces dhcp relay-agent option-82 policy
--------------------------------------------

**Minimum user role:** operator

To set the DHCP relay agent policy for the Relay Agent Information Option (option 82) on the interface:

**Command syntax: policy [policy]**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent option-82

**Parameter table**

+-----------+--------------------------------------------+-------------+---------+
| Parameter | Description                                | Range       | Default |
+===========+============================================+=============+=========+
| policy    | Define the Relay Agent's forwarding policy | | replace   | replace |
|           |                                            | | keep      |         |
|           |                                            | | drop      |         |
+-----------+--------------------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# policy replace


**Removing Configuration**

To return DHCP relay agent information option policy configuration on the interface to its default value:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)# no policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
