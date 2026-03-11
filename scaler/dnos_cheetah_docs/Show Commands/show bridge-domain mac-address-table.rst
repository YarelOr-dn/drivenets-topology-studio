show bridge-domain mac-address-table
------------------------------------

**Minimum user role:** operator

To show the detailed information of each mac-address learned on a Bridge-Domain instance.


**Command syntax: show bridge-domain mac-address-table** {ncp [ncp-id]}
**Command syntax: show bridge-domain mac-address-table** instance [bridge-domain-name] {ncp [ncp-id]}
**Command syntax: show bridge-domain mac-address-table** mac [mac-address] {ncp [ncp-id]}

**Command mode:** operational

**Parameter table:**

+--------------------+-----------------------------------------+-------------------+---------------+
| Parameter          | Description                             | Values            | Default value |
+====================+=========================================+===================+===============+
| bridge-domain-name | The name of the Bridge Domain           | String | all      | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+
| ncp-id             | The ID of the NCP for which to display  | 0..255 characters | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+
| mac-address        | A specific mac-address                  | xx:xx:xx:xx:xx:xx | \-            |
+--------------------+-----------------------------------------+-------------------+---------------+

**Note:**

- Specifying a bridge-domain-name will display the specified Bridge-Domain's mac-addresses

- Specifying 'all' will result in the listing of the mac addresses of all BDs


**Example**
::

    dnRouter# show bridge-domain mac-address-table
    Legend: S - Static, D - Dynamic

    NCP-ID 0
    Bridge-Domain: bd1
    Total Mac Entries: 2

    | MacAddress         | Interface  | Timestamp       | Flags |
    +--------------------+------------+-----------------+-------+
    | 00:10:94:11:11:11  | bundle-1   | Jan 23 19:39:21 |   D   |
    | 00:12:9a:b1:dc:ae  | bundle-1   | Jan 23 19:39:22 |   D   |
    | 84:40:76:c5:5a:25  | irb1       | Jan 23 19:39:23 |   S   |


    Bridge-Domain: bd2
    Total Mac Entries: 3

    | MacAddress         | Interface  |  Timestamp      | Flags |
    +--------------------+------------+-----------------+-------+
    | 00:10:94:22:23:41  | bundle-2   | Jan 23 19:39:21 |   D   |
    | 00:62:ea:a1:c9:f1  | bundle-3   | Jan 23 19:39:22 |   D   |
    | 00:62:ea:a1:c9:42  | bundle-3   | Jan 23 19:39:22 |  S, D |

    dnRouter# show bridge-domain mac-address-table ncp 2
    Legend: S - Static, D - Dynamic

    NCP-ID 2

    Bridge-Domain: MyBridge1
    Total Mac Entries: 2

    |  MAC Address       | Interface  | Entry Date and Time   |  Flags |
    |-------------------+-------------+-----------------------+--------|
    | 00:00:00:00:00:01 | bundle-1    | Jan 23 19:39:21       |   D    |
    | 00:00:00:00:00:02 | bundle-2    | Jan 23 19:39:22       |   D    |

    Bridge-Domain: MyBridge2
    Total Mac Entries: 2

    | MAC Address       | Interface   | Entry Date and Time   |  Flags |
    |-------------------+-------------+-----------------------|--------|
    | 00:00:00:00:ff:01 | bundle-10   | Jan 23 19:49:21       |   D    |
    | 00:00:00:00:ff:02 | bundle-10   | Jan 23 19:50:22       |   D    |


    dnRouter# show bridge-domain mac-address-table instance MyBridge1
    Legend: S - Static, D - Dynamic

    NCP-ID 0

    Bridge-Domain: MyBridge1
    Total Mac Entries: 2

    | MAC Address       | Interface   | Entry Date and Time   |  Flags |
    |-------------------+-------------+-----------------------+--------|
    | 00:00:00:00:00:01 | bundle-1    | Jan 23 19:39:21       |    D   |
    | 00:00:00:00:00:02 | bundle-2    | Jan 23 19:39:22       |    D   |


    dnRouter# show bridge-domain mac-address-table mac 00:00:00:00:00:02
    Legend: S - Static, D - Dynamic

    NCP-ID 0

    Bridge-Domain: MyBridge1
    Total Mac Entries: 1

    | MAC Address       | Interface   | Entry Date and Time   |  Flags |
    |-------------------+-------------+-----------------------+--------|
    | 00:00:00:00:00:02 | bundle-2    | Jan 23 19:39:22       |    D   |


.. **Help line:** show MAC Address information for Bridge Domain instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 17.2    | Command introduced                  |
+---------+-------------------------------------+