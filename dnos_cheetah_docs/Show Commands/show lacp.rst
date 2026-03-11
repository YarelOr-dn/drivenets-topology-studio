show lacp
---------

**Minimum user role:** viewer

The show lacp command displays the global LACP configuration.



**Command syntax: show lacp** [parameters]

**Command mode:** operational




**Parameter table**

+-----------------+----------------------------------------+--------------------+
| Parameter       | Values                                 | Default Value      |
+=================+========================================+====================+
| system-priority | 0..65535                               | 1                  |
+-----------------+----------------------------------------+--------------------+
| system-id       | xx:xx:xx:xx:xx:xx (mac-address format) | Assigned by system |
+-----------------+----------------------------------------+--------------------+

**Example**
::

	dnRouter# show lacp
	
	system-priority: 1
	system-id: 11:22:33:44:55:66
	

.. **Help line:** show global lacp configuration

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 6.0     | Command introduced       |
+---------+--------------------------+
| 9.0     | Updated default priority |
+---------+--------------------------+


