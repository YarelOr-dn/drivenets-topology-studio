show debugging
--------------

**Minimum user role:** viewer

To display persistent and non-persistent debugging availability:

**Command syntax: show debugging [category]**

**Command mode:** operational




**Parameter table**

+-----------+-------------------------------------------------------------------+----------------------+---------+
| Parameter | Description                                                       | Range                | Default |
+===========+===================================================================+======================+=========+
| category  | The category for which to show the available debugging parameters | See "Debug Commands" | \-      |
+-----------+-------------------------------------------------------------------+----------------------+---------+

**Example**
::

	dnRouter# show debugging ospf

	OSPF debugging status:
	  OSPF event debugging is on
	  OSPF ISM debugging is on
	  OSPF NSM debugging is on
	  OSPF NSSA debugging is on

	dnRouter# show debugging bgp

	BGP debugging status:
	  General-events non-persistant on
	  AS4 debugging non-persistant on
	  FSM debugging non-persistant on

	dnRouter# show debugging rib-manager

	RIB-Manager debugging status:
	  Events debugging non-persistant on
	  NHT debugging non-persistant on

.. **Help line:** Displays debugging availability

**Command History**

+---------+------------------------------------------+
| Release | Modification                             |
+=========+==========================================+
| 11.2    | Command introduced                       |
+---------+------------------------------------------+
| 11.5    | Updated syntax for debugging by category |
+---------+------------------------------------------+

