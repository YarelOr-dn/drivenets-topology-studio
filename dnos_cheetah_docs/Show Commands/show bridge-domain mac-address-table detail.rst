show bridge-domain mac-address-table detail
-------------------------------------------

**Minimum user role:** operator

To show the detailed information of each mac-address learned on a Bridge-Domain instance.

**Command syntax: show bridge-domain mac-address-table detail** {ncp [ncp-id]}
**Command syntax: show bridge-domain mac-address-table detail** instance [bridge-domain-name] {ncp [ncp-id]}
**Command syntax: show bridge-domain mac-address-table detail** mac [mac-address] {ncp [ncp-id]}


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

- Specifying a MAC Address will provide the details of that MAC address if it is found in the MAC table of a Bridge Domain.

- Specifying an ncp-id will provide the information from the specified NCP.

**Example**
::

    dnRouter# show bridge-domain mac-address-table detail

    NCP-ID 2
    Bridge-Domain: MyBridge1
    Total Mac Entries: 3

        MacAddress: 00:00:00:00:00:01
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:00:02
        Interface: bundle-2
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:10:94:11:11:11
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 84:40:76:c5:5a:25
        Interface: irb1
        Flags: Static
        Timestamp: 0

    Bridge-Domain: MyBridge2
    Total Mac Entries: 2

        MacAddress: 00:00:00:00:ff:01
        Interface: bundle-10
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:ff:02
        Interface: bundle-10
        Flags: Dynamic
        Timestamp: 0

    dnRouter# show bridge-domain mac-address-table detail ncp 5

    NCP-ID 5
    Bridge-Domain: MyBridge1
    Total Mac Entries: 3

        MacAddress: 00:00:00:00:00:01
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:00:02
        Interface: bundle-2
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:10:94:11:11:11
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

    Bridge-Domain: MyBridge2
    Total Mac Entries: 2

        MacAddress: 00:00:00:00:ff:01
        Interface: bundle-10
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:ff:02
        Interface: bundle-10
        Flags: Dynamic
        Timestamp: 0

    dnRouter# show bridge-domain mac-address-table detail instance MyBridge1

    NCP-ID 2
    Bridge-Domain: MyBridge1
    Total Mac Entries: 3

        MacAddress: 00:00:00:00:00:01
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:00:02
        Interface: bundle-2
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:10:94:11:11:11
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

    dnRouter# show bridge-domain mac-address-table detail instance MyBridge1 ncp 4

    NCP-ID 4
    Bridge-Domain: MyBridge1
    Total Mac Entries: 3

        MacAddress: 00:00:00:00:00:01
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:00:00:00:00:02
        Interface: bundle-2
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:10:94:11:11:11
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

    dnRouter# show bridge-domain mac-address-table detail mac 00:10:94:11:11:11 ncp 4

    NCP-ID 4
    Bridge-Domain: MyBridge1
    Total Mac Entries: 1

        MacAddress: 00:10:94:11:11:11
        Interface: bundle-1
        Flags: Dynamic
        Timestamp: 0

        MacAddress: 00:10:94:11:11:22
        Interface: bundle-1
        Flags: Static, Dynamic
        Timestamp: 0

.. **Help line:** show Detailed MAC Address information for Bridge Domain instances

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 17.2    | Command introduced                  |
+---------+-------------------------------------+