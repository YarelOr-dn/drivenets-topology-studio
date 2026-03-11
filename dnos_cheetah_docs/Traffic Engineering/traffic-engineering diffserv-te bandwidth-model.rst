traffic-engineering diffserv-te bandwidth-model
-----------------------------------------------

**Minimum user role:** operator

The bandwidth model determines the values of the available bandwidth advertised by the interior gateway protocols (IGPs).

To configure the bandwidth model:


**Command syntax: bandwidth-model [bandwidth-model]**

**Command mode:** config

**Hierarchies**

- protocols mpls traffic-engineering diffserv-te

**Note**

- The Russian doll model (RDM) is defined in RFC 4127.

**Parameter table**

+--------------------+----------------------------------------------------------------------+--------------------------------------------------------------------------------+-------------+
|                    |                                                                      |                                                                                |             |
| Parameter          | Description                                                          | Range                                                                          | Default     |
+====================+======================================================================+================================================================================+=============+
|                    |                                                                      |                                                                                |             |
| bandwidth-model    | The bandwidth model to be used by DiffServ   bandwidth allocation    | rdm - different classes may share bandwidth   according to their importance    | rdm         |
+--------------------+----------------------------------------------------------------------+--------------------------------------------------------------------------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# mpls
	dnRouter(cfg-protocols-mpls)# traffic-engineering 
	dnRouter(cfg-protocols-mpls-te)# diffserv-te
	dnRouter(cfg-mpls-te-diffserv)# bandwidth-model rdm

**Removing Configuration**

To revert to the default model:
::

	dnRouter(cfg-mpls-te-diffserv)# no bandwidth-model


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 10.0        | Command introduced    |
+-------------+-----------------------+