show mpls forwarding-table evpn-vpws
------------------------------------

**Minimum user role:** viewer

To show the MPLS forwarding-table:

**Command syntax: show mpls forwarding-table evpn-vpws** instance [instance-name] ncp [ncp-id]

.. instance - display detailed view for specific EVPN-VPWS instance

.. ncp - display information from a specific ncp. by default, display from active NCP with minimum ID.

**Command mode:** operational

**Note**

.. By default, the information will be sent from the active NCP with the lowest ID.

- The brief view is displayed by service name alphabetically.

.. Technical limitations:

.. On large scale routing tables, the table might not be presented ordered

.. When there are l2vpn table updates while presenting the table, the table might contain duplicate entries and might not contain all entries.

**Parameter table:**

+---------------+---------------------------------------------------------------------------------------------------+--------+------------------------+
| Parameter     | Description                                                                                       | Range  | Default                |
+===============+===================================================================================================+========+========================+
| instance-name | The EVPN-VPWS instance to display detailed information.                                           | String | Default                |
+---------------+---------------------------------------------------------------------------------------------------+--------+------------------------+
| ncp-id        | Displays information from a specific NCP. By default, the active NCP with lowest ID is displayed. | 0..191 | NCP with the lowest ID |
+---------------+---------------------------------------------------------------------------------------------------+--------+------------------------+

**Example**
::

	dnRouter# show mpls forwarding-table evpn-vpws

    NCP-ID: 0

    | service-name       | neighbor        | local-label   | remote-label  | ac                |
    +--------------------+-----------------+---------------+---------------+-------------------+
    | MY_EVPN-VPWS       | 10.10.10.10     | 11457         | 78711         | ge100-0/0/19      |
    | MY_EVPN-VPWS       | 10.10.11.10     | 11457         | 87711         | ge100-0/0/19      |
    | MY_EVPN-VPWS_2     | 20.20.20.20     | 11460         | 60441         | ge100-0/0/37      |
    | MY_EVPN-VPWS_2     | 20.20.21.20     | 11460         | 86441         | ge100-0/0/37      |

	dnRouter# show mpls forwarding-table evpn-vpws instance MY_EVPN-VPWS

    NCP-ID: 0
    EVPN-VPWS Forwarding Table:
    MY_EVPN-VPWS
        AC Interface: 
            ge100-0/0/19
        PW local label: 11457
        next-hop(1): 10.10.10.10 Recursive, Active
        PW label: 78711
            next-hop(1,1): 10.10.10.10 Active
            mpls labels: 4444
            interface: ge100-0/0/10 
        next-hop(2): 10.10.11.10 Recursive, Active
        PW label: 87711
            next-hop(2,1): 10.10.11.10 Active
            mpls labels: 5555
            interface: ge100-0/0/11




.. **Help line:** show mpls forwarding-table evpn-vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
