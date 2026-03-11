services twamp vrf source-interface
-----------------------------------

**Minimum user role:** operator

Set an existing interface as the source interface for the TWAMP service. The source interface is used to send and receive control and test packets.

To set source interface for the TWAMP service:

**Command syntax: source-interface [interface-name]**

**Command mode:** config

**Hierarchies**

- services twamp vrf

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan
  - Loopback

- By default the in-band-management source-interface is used within the VRF context. Configuring source-interface will overide the default interface.
- To the extent that the source-interface to be used does not have an IPv4 address configured, then connections over the VRF will not work.

**Parameter table**

+----------------+-----------------------------------------------------+------------------+---------+
| Parameter      | Description                                         | Range            | Default |
+================+=====================================================+==================+=========+
| interface-name | Specify the source interface for the TWAMP service. | | string         | \-      |
|                |                                                     | | length 1-255   |         |
+----------------+-----------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# services
    dnRouter(cfg-srv)# twamp vrf default
    dnRouter(cfg-srv-twamp-vrf)# source-interface lo5000


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-srv-twamp-vrf)# no source-interface

**Command History**

+---------+---------------------------+
| Release | Modification              |
+=========+===========================+
| 6.0     | Command introduced        |
+---------+---------------------------+
| 16.2    | Moved under VRF hierarchy |
+---------+---------------------------+
