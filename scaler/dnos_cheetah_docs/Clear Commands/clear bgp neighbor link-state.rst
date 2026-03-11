clear bgp neighbor link-state
-----------------------------

**Minimum user role:** operator

To clear BGP neighbor link-state:

**Command syntax: clear bgp neighbor { [neighbor-address] \| \| group [group-name]} link-state** soft out

**Command mode:** operation

.. **Hierarchies**

**Note**

-  Optional parameters must match the order in the command

-  When performing a hard clear for a bgp neighbor with a specific address-family, for example clear bgp neighbor group BGP_GROUP ipv4, the bgp session will tear affecting  all address families

-  Use soft to apply soft reconfig

-  Applies to ibgp neighbors only

-  When no update-direction is specified, perform a hard clear.

**Parameter table**

+---------------------+---------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                   |                 |             |
| Parameter           | Description                                                                                       | Range           | Default     |
+=====================+===================================================================================================+=================+=============+
|                     |                                                                                                   |                 |             |
| neighbor-address    | Clear link-states from a specific iBGP neighbor                                                   | A.B.C.D         | \ -         |
|                     |                                                                                                   |                 |             |
|                     |                                                                                                   | xx:xx::xx:xx    |             |
+---------------------+---------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                   |                 |             |
| group-name          | Clear link-states from a specific neighbor group                                                  | String          | \ -         |
+---------------------+---------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                   | \ -             | \ -         |
| soft                | Use for soft reconfiguration                                                                      |                 |             |
+---------------------+---------------------------------------------------------------------------------------------------+-----------------+-------------+
|                     |                                                                                                   |                 | \ -         |
| out                 | The update direction. If you do not specify an update direction, hard clear will be performed.    | out             |             |
+---------------------+---------------------------------------------------------------------------------------------------+-----------------+-------------+


**Example**
::

	dnRouter# clear bgp neighbor 7.7.7.7 link-state
	dnRouter# clear bgp neighbor 7.7.7.7 link-state soft
	dnRouter# clear bgp neighbor 7.7.7.7 link-state out
	dnRouter# clear bgp neighbor 7.7.7.7 link-state soft out

	dnRouter# clear bgp neighbor group BGP_GROUP link-state
	dnRouter# clear bgp neighbor group BGP_GROUP link-state soft
	dnRouter# clear bgp neighbor group BGP_GROUP link-state out
	dnRouter# clear bgp neighbor group BGP_GROUP link-state soft out




.. **Help line:**

**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 10.0      | Command introduced    |
+-----------+-----------------------+