policy set aigp
---------------

**Minimum user role:** operator

The set AIGP action depends on the policy attachment point:

+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| Set AIGP Policy Attachment Point                                 | Set AIGP IGP-metric                                                                                                              | Set AIGP [relative] [aigp-value]                                                                                                                                                                                    | Set AIGP [aigp-value]                                                                                                                                                                         |
+==================================================================+==================================================================================================================================+=====================================================================================================================================================================================================================+===============================================================================================================================================================================================+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp neighbor address-family policy in                            | Set 0 in the AIGP metric                                                                                                         | Add the given [aigp-value] to or deduct it from   the AIGP metric attribute before best path selection.                                                                                                             | Set the given [aigp-value] to the AIGP metric   attribute before best path selection.                                                                                                         |
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
|                                                                  | **This is not the proper usage.**                                                                                                |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp neighbor address-family policy out                           | Set 0 in the AIGP metric                                                                                                         | Add the given [aigp-value] to or deduct it from   the AIGP metric attribute after best path selection.                                                                                                              | Overwrite the AIGP metric value with the   specified [aigp-value].                                                                                                                            |
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
|                                                                  | **This is not the proper usage.**                                                                                                |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp address-family unicast redistribute ospf|static|connected    | Set the IGP metric of the redistributed route to   BGP AIGP. This will cause the NCR to be the AIGP originator for the route.    | Add the value to or deduct the value from the   AIGP metric attribute of the BGP path. If the attribute does not exist, it   will be created. This will cause the NCR to be the AIGP originator for the   route.    | Set a specific value for the BGP AIGP attribute   of the BGP path. If the attribute does not exist, it will be created. This   will cause the NCR to be the AIGP originator for the route.    |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp network                                                      | Set the IGP metric of the redistributed route to   BGP AIGP. This will cause the NCR to be the AIGP originator for the route.    | Add the value to or deduct the value from the   AIGP metric attribute of the BGP path. If the attribute does not exist, it   will be created. This will cause the NCR to be the AIGP originator for the   route.    | Set a specific value for the BGP AIGP attribute   of the BGP path. If the attribute does not exist, it will be created. This   will cause the NCR to be the AIGP originator for the route.    |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

To set the AIGP metric attribute:

**Command syntax: set aigp {igp-metric \|** [relative] **[aigp-value]** }

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- BGP neighbor afi must be set with 'aigp enabled', otherwise no aigp attribute is sent or received regardless of the policy set action.


**Parameter table**

+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+
|                |                                                                                                                                                       |                  | Default |
| Parameter      | Description                                                                                                                                           | Range            |         |
+================+=======================================================================================================================================================+==================+=========+
|                |                                                                                                                                                       |                  | \-      |
| igp-metric     | Sets the metric value as the IGP metric for the   route                                                                                               | \-               |         |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+
|                |                                                                                                                                                       |                  | \-      |
| relative       | Increase/decrease the current value of the AIGP   metric by [aigp-value]. The resulting value cannot go below 0 or above the   maximum aigp-value.    | \+ /\-           |         |
|                |                                                                                                                                                       |                  |         |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+
|                |                                                                                                                                                       |                  | \-      |
| aigp-value     | The new value of the AIGP metric that will be   set.                                                                                                  | 0..4294967294    |         |
+----------------+-------------------------------------------------------------------------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set aigp igp-metric

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)#set aigp 300

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)#set aigp + 10

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)#set aigp - 10


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)#no set aigp


.. **Help line:**

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
|             |                       |
| 7.0         | Command introduced    |
+-------------+-----------------------+