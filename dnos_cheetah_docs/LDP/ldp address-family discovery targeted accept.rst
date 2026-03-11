ldp address-family discovery targeted accept
--------------------------------------------

**Minimum user role:** operator

This command enables the router to accept targeted hello messages from a remote peer, to open an LDP session. In the event of bi-directional LDP tunneling between two LDP peers that send and receive hellos, an LDP session will be formed:

**Command syntax: accept [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ldp address-family discovery-targeted

.. **Note:**

	- In case of LDP tunneling headend, LDP speaker will send targeted hello regardless of this configuration. If both sides sends and receive hellos a LDP session will be form, e.g in case of bi-directional LDP tunneling between two LDP peers

	- no command returns admin-state to default value

**Parameter table**

+----------------+------------------------------------------------------------------------------+-------------+-------------+
|                |                                                                              |             |             |
| Parameter      | Description                                                                  | Range       | Default     |
+================+==============================================================================+=============+=============+
|                |                                                                              |             |             |
| admin-state    | Defines whether to enable or disable the router to accept targeted hellos    | Enabled     | Disabled    |
|                |                                                                              |             |             |
|                |                                                                              | Disabled    |             |
+----------------+------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# ldp
	dnRouter(cfg-protocols-ldp)# address-family ipv4-unicast
	dnRouter(cfg-protocols-ldp-afi)# discovery targeted
	dnRouter(cfg-ldp-afi-disc-tar)# accept enabled

**Removing Configuration**

To revert to the default value:
::

	dnRouter(cfg-ldp-afi-disc-tar)# no accept

.. **Help line:** Accept TLDP discovery admin-state

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.0      | Command introduced    |
+-----------+-----------------------+