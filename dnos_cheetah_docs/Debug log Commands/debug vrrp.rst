debug vrrp
----------

**Minimum user role:** operator for persistent; viewer for non-persistent debug logging

To debug VRRP events:

**Command syntax: vrrp** [parameter] ; **set debug vrrp** [parameter]

**Command mode:** config - for persistent; operational for non-persistent debug logging

**Hierarchies**

- debug

**Note**

- When no parameter is set, then all VRRP events will be debugged.

- Each command can be negated using the no or unset command prefix.

- When debug is enabled, the logs are found in a trace file, which can be viewed with the show file traces command.

- The debug information is written in the vrrpd log file.


**Parameter table**

+-------------------+------------------------------------------------------------+
| Parameter         | Description                                                |
+===================+============================================================+
| arp-packets       | Debug VRRP ARP handling                                    |
+-------------------+------------------------------------------------------------+
| ndisc             | Debug VRRP IPv6 neighbor discovery handling                |
+-------------------+------------------------------------------------------------+
| packets           | Debug VRRP sent and received packets                       |
+-------------------+------------------------------------------------------------+
| protocol          | Debug VRRP protocol events                                 |
+-------------------+------------------------------------------------------------+
| sockets           | Debug VRRP sockets                                         |
+-------------------+------------------------------------------------------------+
| rib               | Debug VRRP-RIB messages                                    |
+-------------------+------------------------------------------------------------+
| tracking          | Debug VRRP objects tracking actions                        |
+-------------------+------------------------------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# debug
	dnRouter(cfg-debug)# vrrp
	dnRouter(cfg-debug)# vrrp arp-packets
	dnRouter(cfg-debug)# vrrp ndisc
	dnRouter(cfg-debug)# vrrp packets
	dnRouter(cfg-debug)# vrrp protocol
	dnRouter(cfg-debug)# vrrp sockets
	dnRouter(cfg-debug)# vrrp rib
	dnRouter(cfg-debug)# vrrp tracking

	dnRouter# set debug vrrp tracking
	dnRouter# set debug vrrp protocol
	dnRouter# set debug vrrp

**Removing Configuration**

To remove debug configuration:
::

	dnRouter(cfg-debug)# no vrrp rib
	dnRouter(cfg-debug)# no vrrp arp
	dnRouter(cfg-debug)# no vrrp tracking
	dnRouter(cfg-debug)# no vrrp sockets
	dnRouter(cfg-debug)# no vrrp

	dnRouter# unset debug vrrp ndisc
	dnRouter# unset debug vrrp packets

.. **Help line:** Debug VRRP events

**Command History**

+---------+---------------------------------------------------------------------------+
| Release | Modification                                                              |
+=========+===========================================================================+
| 17.2    | Command introduced                                                        |
+---------+---------------------------------------------------------------------------+
