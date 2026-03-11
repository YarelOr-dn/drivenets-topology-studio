routing-options rpki server source-interface
--------------------------------------------

**Minimum user role:** operator

To set the interface from which the source IP address for the RTR session with a BGP RPKI cache server will be taken.

**Command syntax: source-interface [source-interface]**

**Command mode:** config

**Hierarchies**

- routing-options rpki server

**Note**

- The source IP address type (IPv4 or IPv6) needs to match the IP address-family of the configured server. If such an address doesn't exist, the session will not open.

**Parameter table**

+------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter        | Description                                                                      | Range            | Default |
+==================+==================================================================================+==================+=========+
| source-interface | By default the 'system in-band-management source-interface' for the same VRF is  | | string         | \-      |
|                  | used. If both are not configured, then egress-forwarding resolution shall        | | length 1-255   |         |
|                  | determine the interface and source IP address                                    |                  |         |
+------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server 1.1.1.1
    dnRouter(cfg-routing-options-rpki)# source-interface lo0

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-options)# rpki server rpkiv.drivenets.com
    dnRouter(cfg-routing-options-rpki)# source-interface ge100-0/0/0


**Removing Configuration**

To revert all rpki configuration to the default values:
::

    dnRouter(cfg-routing-options-rpki)# no source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
