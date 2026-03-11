clear rsvp statistics packets
-----------------------------

**Minimum user role:** operator

To clear RSVP packet statistics:

**Command syntax: clear rsvp statistics packets** interface [interface-name]

**Command mode:** operation

.. **Hierarchies**

.. **Note**

**Parameter table:**

+---------------+---------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+
|               |                                                                                                         |                                                    |             |
| Parameter     | Description                                                                                             | Range                                              | Default     |
+===============+=========================================================================================================+====================================================+=============+
| interface-name| Clear packet statistics from the specified interface only. Applicable to configured MPLS-TE interfaces. | configured mpls-te interface name.                 | \-          |
|               |                                                                                                         |                                                    |             |
|               |                                                                                                         | ge{/10/25/40/100}-X/Y/Z                            |             |
|               |                                                                                                         |                                                    |             |
|               |                                                                                                         | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |             |
|               |                                                                                                         |                                                    |             |
|               |                                                                                                         | bundle-<bundle-id>                                 |             |
|               |                                                                                                         |                                                    |             |
|               |                                                                                                         | bundle-<bundle-id.sub-bundle-id>                   |             |
+---------------+---------------------------------------------------------------------------------------------------------+----------------------------------------------------+-------------+


**Example**
::

	dnRouter# clear rsvp statistics packets
	dnRouter# clear rsvp statistics packets bundle-2


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 11.0        | Command introduced    |
+-------------+-----------------------+