policy set med
--------------

**Minimum user role:** operator

To set the BGP attribute MED:

**Command syntax: set med {igp-cost \|** [relative] **[med-value]** }

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                                                                               | Range         | Default |
+===========+===========================================================================================================================================+===============+=========+
| igp-cost  | Set the MED value to be the metric towards the route bgp next-hop. Usage of igp-cost is only applicable for policy out.                   | \-            | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| relative  | Increases or decreases the route's existing MED value by the configured med-value. The resulting MED value must be between 0..4294967295. | \+/\-         | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| med-value | Sets a new multi-exit discriminator for best path selection.                                                                              | 0..4294967295 | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set med 500


	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy PL_OUT
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set med igp-cost


	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy PL_IN
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set med + 30
	dnRouter(cfg-rpl-policy-rule-20)#set med - 5


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set med

.. **Help line:** Set the BGP attribute MED

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 6.0     | Command introduced                           |
+---------+----------------------------------------------+
| 15.2    | 'igp-cost' and 'relative' options were added |
+---------+----------------------------------------------+