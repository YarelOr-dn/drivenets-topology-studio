show system snmp communities
----------------------------

**Minimum user role:** viewer

The show snmp community command displays a list of SNMP communities configured in the system. You can display all SNMP communities or filter the display to a specific SNMP community, using the following command:

**Command syntax: show system snmp communities** [community-name]

**Command mode:** operational



.. **Note**

    - vrf "default" represents the in-band management, while vrf "mgmt0" represents the out-of-band management.

**Parameter table**

+----------------+------------------------------------------------------------------+--------+
| Parameter      | Description                                                      | Range  |
+================+==================================================================+========+
| community-name | Filters the displayed information by the specific community name | String |
+----------------+------------------------------------------------------------------+--------+

**Example**
::

    dnRouter# show system snmp communities

    SNMP Communities:

    | Community              | VRF        | Admin-state | Access     | View         | Clients                             |
    |------------------------+------------+-------------+------------+--------------+-------------------------------------|
    | MyPublicSnmpCommunity  | default    | enabled     | read-only  | MySnmpView1  | 192.168.1.0/24 , 2001:db8:2222::/48 |
    | MyPrivateSnmpCommunity | default    | enabled     | read-write | MySnmpView1  |                                     |
    | TestCommunity          | mgmt0      | disabled    | read-only  | viewdefault  | 192.192.100.1/32, 2.2.2.0/24        |
    | MySnmpCommunity        | my_vrf     | enabled     | read-only  | MySnmpView1  | 172.17.1.0/16, 2001:db8:3333::/48   |

    dnRouter# show system snmp communities MyPrivateSnmpCommunity

    SNMP Communities:

    | Community               | VRF       | admin-state | Access     | View         | Clients             |
    |-------------------------+-----------+-------------+------------+--------------+---------------------|
    | MyPrivateSnmpCommunity  | default   | enabled     | read-write | MySnmpView1  |                     |

.. **Help line:** show system snmp servers

**Command History**

+---------+-----------------------------------------------------------------------------------+
| Release | Modification                                                                      |
+=========+===================================================================================+
| 5.1.0   | Command introduced                                                                |
+---------+-----------------------------------------------------------------------------------+
| 13.1    | Added in-band (default VRF) / out-of-band (mgmt0 VRF) configuration per community |
+---------+-----------------------------------------------------------------------------------+
| 15.1    | Added IPv6 support to SNMP                                                        |
+---------+-----------------------------------------------------------------------------------+


