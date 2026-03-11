Link Aggregation Control Protocol (LACP) Overview
-------------------------------------------------

The Link Aggregation Control Protocol (LACP) is used for dynamically exchanging information between two bundle partner systems to automatically maintain the links within the bundle. A partner actively sends out a LACP protocol data unit (PDU) to a remote partner containing information about its state, its ports and links, and any information it knows about the remote partner.

A partner can either be an active or passive participant in LACP. An active partner periodically initiates LACPDUs to its remote partner. A passive partner only responds to LACPDUs.

**Note**
-	The ports at both ends must be of the same speed and duplex.

The LACP feature provides a mechanism for automatic link failover within the bundle interface.

**LACP Configuration**

LACP exchanges are made between actors (the transmitting link) and partners (the receiving link). The LACP mode can be either active or passive.

To configure LACP on a predefined bundle interface with associated physical interfaces (ports):

 1. Enter LACP mode. See protocols lacp.

 2. Configure the LACP system identifier. The system identifier is the concatenation of the system priority value and the system ID value.
    a. Configure the system priority. See lacp system-priority.
    b. Configure the system ID. See lacp system-id.
 3. Configure the LACP parameters, using the following general command:

**Example**

::

    dnRouter(cfg-protocols)# lacp interface [interface-name] parameter [parameter-value]


**The parameters are:**

+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Parameter      | Description                                                                                              | Reference             |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Interface-name | The name of the interface on which to configure LACP.                                                    | -                     |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Mode           | The mode for exchanging LACP packets between interfaces.                                                 | lacp interface mode   |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Period         | The frequency of sending LACPDUs.                                                                        | lacp interface period |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+
| Min-links      | The minimum number of interface members that must be active for the aggregate interface to be available. | interfaces min-links  |
+----------------+----------------------------------------------------------------------------------------------------------+-----------------------+

 4. Configure the bundle's members' port priority. See interfaces port-priority.
