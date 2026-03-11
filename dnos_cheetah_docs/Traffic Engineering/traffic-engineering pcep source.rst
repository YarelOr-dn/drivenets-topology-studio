traffic-engineering pcep source
-------------------------------

**Minimum user role:** operator

To configure the PCEP source (either an IPv4 address or an interface):

**Command syntax: source {ipv4-address [ip-address] \| interface [interface-name]}**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering pcep

**Parameter table**

+-------------------+-------------------------------+-------------------------------------+--------------------------------------+
|                   |                               |                                     |                                      |
| Parameter         | Description                   | Range                               | Default                              |
+===================+===============================+=====================================+======================================+
|                   |                               |                                     |                                      |
| ip-address        | The PCEP source IP address    | A.B.C.D                             | The traffic-engineering router-id    |
+-------------------+-------------------------------+-------------------------------------+--------------------------------------+
|                   |                               |                                     |                                      |
| interface-name    | The PCEP source interface     | configured interface name.          | \-                                   |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               | lo<0-65535>                         |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               | ge{/10/25/40/100}-X/Y/Z             |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               | bundle-<bundle-id>                  |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               |                                     |                                      |
|                   |                               | bundle-<bundle-id.sub-bundle-id>    |                                      |
+-------------------+-------------------------------+-------------------------------------+--------------------------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# pcep 
	dnRouter(cfg-mpls-te-pcep)# source ipv4-address 2.2.2.2
	
	dnRouter(cfg-mpls-te-pcep)# source interface lo0

**Removing Configuration**

To revert to the default source address (the MPLS TE router-id):
::

	dnRouter(cfg-protocols-mpls-te)# no source


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+
