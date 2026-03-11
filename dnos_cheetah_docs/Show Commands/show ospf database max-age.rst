show ospf database max-age
--------------------------

**Minimum user role:** viewer

To display the OSPF link state database for LSAs in MaxAge list:

**Command syntax: show ospf** instance [ospf-instance-name] **database max-age**

**Command mode:** operational


..
	**Internal Note**

	- use "instance [ospf-instance-name]" to display information from a specific OSPF instance, when not specified, display information from all OSPF instances

**Parameter table**

+--------------------+----------------------------------------------------------------+----------------------------+
| Parameter          | Description                                                    | Values                     |
+====================+================================================================+============================+
| ospf-instance-name | Filters the displayed information to a specific OSPF instance  | Configured instances names |
+--------------------+----------------------------------------------------------------+----------------------------+

**Example**
::

	dnRouter# show ospf database max-age

	OSPF Instance instance1

	    OSPF Router with ID (100.70.1.45)


                MaxAge Link States:


	dnRouter# show ospf instance instance1 database max-age

	OSPF Instance instance1

       OSPF Router with ID (100.70.1.45)


                MaxAge Link States:


.. **Help line:** OSPF max-age information

**Command History**

+-------------+--------------------------+
| Release     | Modification             |
+=============+==========================+
| 11.6        | Command introduced       |
+-------------+--------------------------+
| 18.2        | Added instance parameter |
+-------------+--------------------------+
