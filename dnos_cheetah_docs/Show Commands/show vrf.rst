show vrf
--------

**Minimum user role:** viewer

Use the show vrf command to display all the configured VRFs:



**Command syntax: show vrf**

**Command mode:** operational



**Note**

- This command displays a list of all configured VRFs. The names displayed are the names of the VRFs that you assigned during VRF creation.


**Example**
::

	dnRouter# show vrf
	
	| Name           | 
	|----------------|
	| default        |
	| my_vrf-2       |
	| my_vrf-3       |
	

.. **Help line:** show vrf instances

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 5.1.0   | Command introduced |
+---------+--------------------+


