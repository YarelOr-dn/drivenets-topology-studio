show mpls forwarding-table vpws
--------------------------------

**Minimum user role:** viewer

To show the MPS forwarding-table:

**Command syntax: show mpls forwarding-table vpws** instance [instance-name] ncp [ncp-id]

.. instance - display detailed view for specific VPWS instance

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
| instance-name | The VPWS instance to display detailed information.                                                | String | Default                |
+---------------+---------------------------------------------------------------------------------------------------+--------+------------------------+
| ncp-id        | Displays information from a specific NCP. By default, the active NCP with lowest ID is displayed. | 0..191 | NCP with the lowest ID |
+---------------+---------------------------------------------------------------------------------------------------+--------+------------------------+

**Example**
::

	dnRouter# show mpls forwarding-table vpws

    NCP-ID: 0

    | service-name       | neighbor        | local-label   | remote-label  | ac                |
    +--------------------+-----------------+---------------+---------------+-------------------+
    | MY_VPWS            | 10.10.10.10     | 11457         | 78711         | ge100-0/0/19      |
    | MY_VPWS_2          | 20.20.20.20     | 11460         | 60441         | ge100-0/0/37      |
    | MY_VPWS_3          | 30.30.30.30     | 11460         | 60441         | ge100-0/0/10      |

	dnRouter# show mpls forwarding-table vpws instance MY_VPWS

    NCP-ID: 0
    VPWS Forwarding Table:
    MY_VPWS
        AC Interface:
            name: ge100-0/0/19, type: port
        PW local label: 11457, remote label: 78711
        PW local encapsulation: RAW, remote encapsulation: RAW
        FAT label negotiation: receive, send
        control word presence: yes
        next-hop(1): 10.10.10.10 Recursive, Active
        mpls label: 70014
            next-hop(1,1): 10.5.200.16 Active
            mpls labels: 4444
            interface: ge100-0/0/8




.. **Help line:** show mpls forwarding-table vpws

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
