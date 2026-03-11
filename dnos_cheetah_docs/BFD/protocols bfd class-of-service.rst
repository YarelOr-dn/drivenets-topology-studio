protocols bfd class-of-service
------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure the DSCP value for all locally generated BFD packets:

**Command syntax: class-of-service [dscp]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

.. **Note**

.. - the no command returns to default values



**Parameter table**

+---------------+-----------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                         |           |             |
| Parameter     | Description                                                                             | Range     | Default     |
+===============+=========================================================================================+===========+=============+
|               |                                                                                         |           |             |
| dscp          | The DSCP value that is used in the BFD packet to classify it and give it a priority.    | 0..63     | 48          |
+---------------+-----------------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# class-of-service 16


**Removing Configuration**

To return to the default value: 
::

	dnRouter(cfg-protocols)# no class-of-service 



**Command History**

+-------------+-------------------------+
|             |                         |
| Release     | Modification            |
+=============+=========================+
|             |                         |
| 11.2        | Command reintroduced    |
+-------------+-------------------------+