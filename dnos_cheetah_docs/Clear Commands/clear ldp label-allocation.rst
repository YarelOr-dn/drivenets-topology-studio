clear ldp label-allocation
--------------------------

**Minimum user role:** operator

 Restart the ldp label allocation, as a result, ldp  withdraws the allocated label and re-runs binding and allocation logic for requested prefix / fec.
 To reset the ldp label allocations:

**Command syntax: clear ldp label-allocation** {ipv4 [ipv4-prefix] | pw-binding neighbor-address [neighbor-address] fec-value [fec-value] | p2mp root-address [root-address] opaque-value [opaque-value]}

**Command mode:** operation

.. **Hierarchies**

.. **Note**

 - clear ldp label-allocation - restart all ldp labels.

 - clear ldp label-allocation ipv4 [ipv4-prefix] - restart the ldp label of a given unicast prefix.

 - clear ldp label-allocation pw-binding - restart the ldp label of a given vpws pw, per the pw neighbor and fec-value (pw-id).

 - clear ldp label-allocation p2mp - restart the ldp p2mp lsp label per MC root-address and opaque-value.


**Parameter table:**

+---------------------+--------------------------------------------------------+---------------+-------------+
|                     |                                                        |               |             |
| Parameter           | Description                                            | Range         | Default     |
+=====================+========================================================+===============+=============+
|                     |                                                        |               |             |
| ipv4-prefix         | Restart ldp label of a given prefix                    | A.B.C.D/M     | \-          |
+---------------------+--------------------------------------------------------+---------------+-------------+
| neighbor-address    | Restart ldp label of a vpws pw per neighbor            | A.B.C.D       |             |
+---------------------+--------------------------------------------------------+---------------+-------------+
| fec-value           | Restart ldp label of a vpws pw per neighbor pw-id      | 1..4294967295 |             |
+---------------------+------------------------------------------------------------------------+-------------+
| root-address        | Restart ldp label of a root node IP address            | A.B.C.D       |             |
+---------------------+------------------------------------------------------------------------+-------------+
| opaque-value        | uniquely identifying the P2MP LSP in the               | string        |             |
|                     | context of the root node                               | no spaces     |             |
+---------------------+------------------------------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear ldp label-allocation
	dnRouter# clear ldp label-allocation ipv4 7.7.7.7/32
	dnRouter# clear ldp label-allocation pw-binding neighbor-address 1.1.1.1 fec-value 444
	dnRouter# clear ldp label-allocation p2mp root-address 20.20.20.20 opaque-value 07000B0000010000000100000000

.. **Help line:** Restart ldp label-allocation

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 18.3        | Command introduced    |
+-------------+-----------------------+
