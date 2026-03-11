mpls ttl-propagate
------------------------------

**Minimum user role:** operator

MPLS TTL propagation allows disabling the default TTL propagation in the IP-MPLS architecture. 

When the admin-state is enabled (default), TTL propagation works in uniform mode. Ingress LSR copies the IP TTL to the MPLS header and decrements it by 1. Each transit LSR performing a swap operation decrements the MPLS TTL value in the MPLS header of the packet by 1. MPLS to IP behavior depends on TTL propagation mode and performed operation. When the IP header value reaches 0, the packet is dropped. When the admin-state is disabled, then TTL propagation works in pipe mode, ingress LSR sets the MPLS TTL to 255, and each transit LSR performing a swap operation decrements the MPLS TTL value by 1. MPLS to IP behavior depends on TTL propagation mode and operation performed.

By default, IP MPLS TTL propagation is enabled. To disable it, use the following command in MPLS configuration mode:

**Command syntax: ttl-propagate [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols mpls

.. **Note:**

.. - This command sets the default TTL processing on ingress and egress LSRs both for locally originated and transit IP/MPLS frames (except for locally originated IP and MPLS traceroute probes which is always in uniform mode).

**Parameter table**

+----------------+---------------------------------------------------------+-------------+-------------+
|                |                                                         |             |             |
| Parameter      | Description                                             | Range       | Default     |
+================+=========================================================+=============+=============+
|                |                                                         |             |             |
| admin-state    | Sets the administrative state of the TTL propagation    | Enabled     | Enabled     |
|                |                                                         |             |             |
|                |                                                         | Disabled    |             |
+----------------+---------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# ttl-propagate enabled

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# ttl-propagate disabled

**Removing Configuration**

To remove the MPLS protocol configuration:
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# no ttl-propagate

.. Help line:** Propagate IP TTL into the label stack.

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.0      | Command introduced    |
+-----------+-----------------------+