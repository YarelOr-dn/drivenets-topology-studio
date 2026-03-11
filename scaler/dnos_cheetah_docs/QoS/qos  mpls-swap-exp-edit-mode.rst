mpls-swap-exp-edit-mode
-----------------------

**Minimum user role:** operator

You can use this command to control whether the MPLS EXP top most label bits (the Traffic Class field) of the swapped header are preserved. 

When the mode is set to **preserve**, EXP bits are always preserved.

When the mode is set to **copy**, the EXP bits are copied from the incoming topmost MPLS header. 

To allow the set mpl-exp command to modify EXP bits, the edit mode must be set to **copy**.

To configure the MPLS swap-exp edit mode:


**Command syntax: mpls-swap-exp-edit-mode [mode]**

**Command mode:** config

**Hierarchies**

- qos

**Parameter table**

+---------------+---------------------------------------------------------------------------------+-----------+-------------+
|               |                                                                                 |           |             |
| Parameter     | Description                                                                     | Range     | Default     |
+===============+=================================================================================+===========+=============+
|               |                                                                                 |           |             |
| mode          | Define the mode to control the action on the   swapped MPLS header EXP bits.    | Preserve  | Preserve    |
|               |                                                                                 |           |             |
|               |                                                                                 | Copy      |             |
+---------------+---------------------------------------------------------------------------------+-----------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# qos
	dnRouter(cfg-qos)# mpls-swap-exp-preserve copy


**Removing Configuration**

To return the parameter to the default:
::

	dnRouter(cfg-qos)# no mpls-swap-exp-preserve

.. **Help line:** rule identifier

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 15.0        | Command introduced    |
+-------------+-----------------------+