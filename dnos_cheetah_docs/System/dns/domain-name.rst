system dns domain-name
----------------------

**Minimum user role:** operator

Configure domain name

**Command syntax: domain-name [domain-name]**

**Command mode:** config

**Hierarchies**

- system dns

**Parameter table**

+-------------+----------------------------------------------------------------------------------+-------+---------+
| Parameter   | Description                                                                      | Range | Default |
+=============+==================================================================================+=======+=========+
| domain-name | The domain-name of the system's management network. The domain-name is           | \-    | \-      |
|             | configured per system.                                                           |       |         |
+-------------+----------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# domain-name abcd.com


**Removing Configuration**

To remove domain name:
::

    dnRouter(cfg-system-dns)# no domain-name

**Command History**

+---------+----------------------------------------------------------------------------------------+
| Release | Modification                                                                           |
+=========+========================================================================================+
| 11.4    | Command introduced                                                                     |
+---------+----------------------------------------------------------------------------------------+
| 13.1    | Command from the "system out-of-band" hierarchy merged with the "system dns" hierarchy |
+---------+----------------------------------------------------------------------------------------+
