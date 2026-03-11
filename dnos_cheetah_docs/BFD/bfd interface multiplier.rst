bfd interface multiplier
------------------------

**Minimum user role:** operator

The multiplier defines the number of min-rx intervals in which a BFD packet is not received before the uBFD session goes down. 

To configure the multiplier:


**Command syntax: multiplier [multiplier]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

**Note**

All micro BFD sessions for the given bundle members will use the same session parameters

.. - the no command returns to default values

**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                                                                                             |           |             |
| Parameter     | Description                                                                                                                                                 | Range     | Default     |
+===============+=============================================================================================================================================================+===========+=============+
|               |                                                                                                                                                             |           |             |
| multiplier    | The number of min-rx intervals in which no BFD packet is received as expected (or the number of missing BFD packets) before the uBFD session goes down.     | 2..16     | 3           |
+---------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# multiplier 5

For example, if min-rx is configured to 100 msec and the multiplier is 5, this means that if BFD packets stop arriving, after 500 msec the session goes down.

**Removing Configuration**

To return to the default value: 
::

	dnRouter(cfg-protocols-bfd-if)# no multiplier

**Command History**

+-------------+--------------------------------------------+
|             |                                            |
| Release     | Modification                               |
+=============+============================================+
|             |                                            |
| 11.2        | Command introduced                         |
+-------------+--------------------------------------------+
|             |                                            |
| 11.4        | Updated multiplier range                   |
+-------------+--------------------------------------------+