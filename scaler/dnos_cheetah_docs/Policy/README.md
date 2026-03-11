# DNOS Policy Configuration Reference

This document contains the complete DNOS CLI Policy configuration syntax from the official DriveNets documentation.

---

## policy set aigp
```rst
policy set aigp
---------------

**Minimum user role:** operator

Within an autonomous system (AS), the distance between two nodes in the interior gateway protocol (IGP) domain is calculated as a sum of all the metric values of links along the path. The IGP selects the shortest path between two nodes based on the calculated distance.

BGP is designed to provide routing over independent ASs with limited or no coordination among respective administrations. BGP does not use metrics in the path selection decisions.

The accumulated interior gateway protocol (AIGP) is an attribute that enables the BGP speakers in a network that is managed by a single administrative domain, but is sub-divided into multiple autonomous systems (AS), to perform best-path selection based on IGP metric, even if the nodes are in different ASs.

In the following image, the network of a single service provider is divided into three contiguous ASs (AS 6660, AS 6661, and AS 6662). The end-to-end service between CE1 and CE2 is MPLS VPN, resulting in the BGP speakers (i.e. PE1 and PE2, and the four border routers (BR P1, BR P2, BR P3, and BR P4) running BGP-LU (labeled unicast). Without AIGP, the PEs and BRs will perform best-path decisions without the IGP metrics inside the different ASs, by basing the interior cost of a route on the calculation of the metric to the next hop for the route. When AIGP is enabled on the PEs and BRs, the IGP metrics in the different ASs are accumulated and the AIGP distance is compared to break a tie, allowing these routers to make better best-path decisions.

<INSERT 04_protocols_bgp>

The set AIGP action depends on the policy attachment point:

+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| Set AIGP Policy Attachment Point                                 | Set AIGP IGP-metric                                                                                                              | Set AIGP [relative] [aigp-value]                                                                                                                                                                                    | Set AIGP [aigp-value]                                                                                                                                                                         |
+==================================================================+==================================================================================================================================+=====================================================================================================================================================================================================================+===============================================================================================================================================================================================+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp neighbor address-family policy in                            | Set 0 in the AIGP metric                                                                                                         | Add the given [aigp-value] to or deduct it from the AIGP metric attribute before best path selection.                                                                                                               | Set the given [aigp-value] to the AIGP metric attribute before best path selection.                                                                                                           |
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
|                                                                  | **This is not the proper usage.**                                                                                                |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp neighbor address-family policy out                           | Set 0 in the AIGP metric                                                                                                         | Add the given [aigp-value] to or deduct it from the AIGP metric attribute after best path selection.                                                                                                                | Overwrite the AIGP metric value with the specified [aigp-value].                                                                                                                              |
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
|                                                                  | **This is not the proper usage.**                                                                                                |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp address-family unicast redistribute ospf|static|connected    | Set the IGP metric of the redistributed route to BGP AIGP. This will cause the system to be the AIGP originator for the route.   | Add the value to or deduct the value from the AIGP metric attribute of the BGP path. If the attribute does not exist, it will be created. This will cause the system to be the AIGP originator for the route.       | Set a specific value for the BGP AIGP attribute of the BGP path. If the attribute does not exist, it will be created. This will cause the system to be the AIGP originator for the route.     |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
|                                                                  |                                                                                                                                  |                                                                                                                                                                                                                     |                                                                                                                                                                                               |
| bgp network                                                      | Set the IGP metric of the redistributed route to BGP AIGP. This will cause the system to be the AIGP originator for the route.   | Add the value to or deduct the value from the AIGP metric attribute of the BGP path. If the attribute does not exist, it will be created. This will cause the system to be the AIGP originator for the route.       | Set a specific value for the BGP AIGP attribute of the BGP path. If the attribute does not exist, it will be created. This will cause the system to be the AIGP originator for the route.     |
+------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

To configure AIGP:
1. Create a policy to set the AIGP metric attribute. This command.
2. Enable the AIGP metric with a BGP neighbor. See bgp neighbor address-family aigp.
3. Optional. Set the router to ignore the AIGP metric in best-path calculation. See bgp bestpath aigp-ignore.

To set the AIGP metric attribute:

**Command syntax: set aigp {igp-metric \| [aigp-value] \| [relative] [aigp-value]}**

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
| 25.2        | Command syntax changed|
+-------------+-----------------------+```

## policy set as-path prepend
```rst
policy set as-path prepend
---------------------------

**Minimum user role:** operator

To prepend the given string of AS number(s) or last AS to the AS-path:

**Command syntax: set as-path prepend** { **as-number [as-number]**, [as-number], ... \| **last-as [number]** }

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- This action is only relevant as a BGP policy.

- Within the same route policy rule, "set as-path exclude" will be processed and imposed before "set as-path prepend" action

**Parameter table**

+---------------+-------------------------------------------------------------------------------------+------------------+---------+
|               |                                                                                     |                  | Default |
| Parameter     | Description                                                                         | Range            |         |
+===============+=====================================================================================+==================+=========+
|               |                                                                                     |                  | \-      |
| as-number     | The AS number to prepend to the AS-path. You can   specify multiple AS numbers.     | 1..4294967295    |         |
+---------------+-------------------------------------------------------------------------------------+------------------+---------+
|               |                                                                                     |                  | \-      |
| number        | The number of times the last as-number will be added.                               | 1..9             |         |
+---------------+-------------------------------------------------------------------------------------+------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set as-path prepend as-number 23456
	dnRouter(cfg-rpl-policy-rule-10)# exit

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set as-path prepend as-number 12956, 23456
	dnRouter(cfg-rpl-policy-rule-20)# exit

	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# set as-path prepend last-as 1
	dnRouter(cfg-rpl-policy-rule-30)# exit

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set as-path prepend last-as 7
	dnRouter(cfg-rpl-policy-rule-40)# exit


**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# no set as-path prepend as-number 12956
	dnRouter(cfg-rpl-policy-rule-20)# exit

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# no set as-path prepend


.. **Help line:** Prepend the given string of AS number(s)

**Command History**

+-------------+----------------------------------------------+
|             |                                              |
| Release     | Modification                                 |
+=============+==============================================+
|             |                                              |
| 6.0         | Command introduced                           |
+-------------+----------------------------------------------+
|             |                                              |
| 9.0         | Changed parameter's range from minimum 1     |
+-------------+----------------------------------------------+
|             |                                              |
| 18.2        | Impose action order within route policy rule |
+-------------+----------------------------------------------+
| 25.2        | Command syntax changed                       |
+-------------+----------------------------------------------+```

## policy set community
```rst
policy set community
--------------------

**Minimum user role:** operator

Use this command to add or remove communities for BGP updates. When you enter multiple entries, they are collected as a list. You can add or remove values to/from the list, and you can do this in separate commits.

To set the specified communities value to BGP updates:

**Command syntax: set community** {**[community]**, [community], ... }
**Command syntax: set community additive {**[community]**, [community], ...} **
**Command syntax: set community none**

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- You can set up to 25 different communities or 'none'.

- Within the same route policy rule, "set community-list" will be processed and imposed before "set community" action.

- Running one of these commands will replace whatever was previously configured.


**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| Parameter     | Description                                                                                     | Range                                                    | Comment             |
+===============+=================================================================================================+==========================================================+=====================+
|               |                                                                                                 |                                                          |                     |
| community     | The community value to set to BGP updates.                                                      | The community number (e.g. aa:nn), range (e.g. aa-bb:nn) | AS_number: 1..65535 |
|               |                                                                                                 |                                                          |                     |
|               | The set community [community] command will replace any existing community configuration.        | <AS_number:NN>                                           | ID: 0..65535        |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | <lower_AS_number- upper_AS_number:lower_id-upper-id>     |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | internet                                                 |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | accept-own                                               |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | local-AS                                                 |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-export                                                |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-advertise                                             |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | no-LLGR                                                  |                     |
|               |                                                                                                 |                                                          |                     |
|               |                                                                                                 | LLGR-stale                                               |                     |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| additive      | Appends the new communities to the existing communities.                                        |  \-                                                      | \-                  |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+
|               |                                                                                                 |                                                          |                     |
| none          | Removes the entire communities attribute from BGP updates.                                      |  \-                                                      | \-                  |
|               |                                                                                                 |                                                          |                     |
|               | The set community none will overwrite any existing community with "none".                       |                                                          |                     |
+---------------+-------------------------------------------------------------------------------------------------+----------------------------------------------------------+---------------------+

**Example**

To overwrite the existing route communities with new communities:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set community 65000:1918

	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set community 65000:86, 65000:2010
	dnRouter(cfg-rpl-policy)# rule 30 allow
	dnRouter(cfg-rpl-policy-rule-30)# set community local-AS, 65000:2010, internet

To add new route communities to the existing communities:
::

	dnRouter(cfg-rpl-policy)# rule 50 allow
	dnRouter(cfg-rpl-policy-rule-50)# set community additive 65000:86, 65000:2010

To delete the existing route communities (by overwriting them with "none")
::

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set community none

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set community


.. **Help line:** The specified communities value is set to BGP updates.


**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 6.0         | Command introduced    |
+-------------+-----------------------+
| 18.2        | Added note for command|
|             | restriction           |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+
| 25.2        | Command syntax changed|
+-------------+-----------------------+```

## policy set large-community
```rst
policy set large-community
---------------------------

**Minimum user role:** operator

Use this command to add or remove large communities for BGP updates. When you enter multiple entries, they are collected as a list. You can add or remove values to/from the list, and you can do this in separate commits.

To set the specified communities' values to BGP updates:

**Command syntax: set large-community** {**[large-community]**, [large-community], ... }
**Command syntax: set large-community additive {**[large-community]**, [large-community], ... }
**Command syntax: set large-community none**


**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- You can set up to 25 large-communities or none.

- Within the same route policy rule, "set large-community-list" will be processed and imposed before "set large-community" action.

**Parameter table**

+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
|    Parameter    | Description                                                         |                    Range                    | Default |
+=================+=====================================================================+=============================================+=========+
| large-community | The large-community values to set for BGP updates                   | <AS_number:id-1:id-2> :                     | \-      |
|                 |                                                                     | AS_number: 0..4294967295id-1: 0..4294967295 |         |
|                 |                                                                     | id-2: 0..4294967295                         |         |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
| additive        | Appends the new large-communities to the existing large-communities |                                             | \-      |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+
| none            | Removes the entire large-communities attribute from BGP updates     |                                             | \-      |
+-----------------+---------------------------------------------------------------------+---------------------------------------------+---------+

**Example**

To overwrite the existing route large-communities with new large-communities:
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)# set large-community 15562:45:29
	dnRouter(cfg-rpl-policy)# rule 20 allow
	dnRouter(cfg-rpl-policy-rule-20)# set large-community 15562:45:29, 15562:45:50

To add new route large-communities to the existing large-communities:
::

	dnRouter(cfg-rpl-policy)# rule 50 allow
	dnRouter(cfg-rpl-policy-rule-50)# set large-community additive 15562:45:29, 15562:45:50

To delete the existing route large-communities (by overwriting them with "none")
::

	dnRouter(cfg-rpl-policy)# rule 40 allow
	dnRouter(cfg-rpl-policy-rule-40)# set large-community none

**Removing Configuration**

To remove all set large-communities:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set large-community

.. **Help line:** The specified large communities value is set to BGP updates.

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 15.1        | Command introduced    |
+-------------+-----------------------+
| 18.1        | Added note for command|
|             | restriction           |
+-------------+-----------------------+
| 18.2        | Impose action order   |
|             | within route policy   |
|             | rule                  |
+-------------+-----------------------+
| 25.2        | Command syntax changed|
+-------------+-----------------------+
```

## policy set local-preference aigp relative
```rst
set local-preference aigp relative
----------------------------------

**Minimum user role:** operator

AIGP (Accumulated IGP Metric) is a BGP attribute designed to enhance path selection in networks that span over multiple ASs. It allows BGP to propagate and consider IGP metric across multiple autonomous system, ensuring routing decisions are consistent with the internal network's shortest-path metrics.
In some cases, legacy devices do not support AIGP, or in some cases (like the case at hand) an operator would like to avoid introducing new configuration on legacy networks, in such case, the operator may decide to copy the AIGP value into the Local-Preference value when routes are advertised in a legacy AS, this way the legacy AS devices will select per route the ASBR that can provide the shortest path.
Updating Local-Preference by inbound policy may influence local best-path selection
If no aigp value known , no update to local-preference.

To update Local-Preference value according to offset from known AIGP value by route policy set action:

**Command syntax: set local-preference aigp [relative] [value]** }

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                                                                               | Range         | Default |
+===========+===========================================================================================================================================+===============+=========+
| relative  | Sets the desired relative modification (add/substract) for the aigp value. The resulting value must be between 0..4294967295.             | \+/\-         | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| value     | Sets an offset for the aigp metric value to be set into local-preference.                                                                 | 0..4294967295 | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set local-preference aigp + 10
	dnRouter(cfg-rpl-policy-rule-10)#set local-preference aigp - 5

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set local-preference

	dnRouter(cfg-rpl-policy-rule-10)# no set local-preference aigp

	dnRouter(cfg-rpl-policy-rule-10)# no set local-preference aigp + 10

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 25.2    | Command introduced                           |
+---------+----------------------------------------------+
```

## policy set med aigp relative
```rst
policy set med aigp relative
----------------------------

**Minimum user role:** operator

AIGP (Accumulated IGP Metric) is a BGP attribute designed to enhance path selection in networks that span over multiple ASs. It allows BGP to propagate and consider IGP metric across multiple autonomous system, ensuring routing decisions are consistent with the internal network's shortest-path metrics.
in some cases, legacy devices do not support AIGP, or in some cases  (like the case at hand) an operator would like to avoid introducing new configuration on legacy networks, in such case, the operator may decide to copy the AIGP value into the MED value when routes are advertised to a legacy AS, this way the legacy AS devices will select per route the ASBR that can provide the shortest path.
the downside of such solution, is that the path to the ASBR is not taken into consideration when selecting the best path

To update MED value according to offset from known AIGP value by route policy set action:

**Command syntax: set med aigp [relative] [value]** }

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Parameter table**

+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| Parameter | Description                                                                                                                               | Range         | Default |
+===========+===========================================================================================================================================+===============+=========+
| relative  | Sets the desired relative modification (add/substract) for the aigp value. The resulting MED value must be between 0..4294967295.         | \+/\-         | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+
| value     | Sets an offset for the aigp metric value to be set into MED.                                                                              | 0..4294967295 | \-      |
+-----------+-------------------------------------------------------------------------------------------------------------------------------------------+---------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-policy
	dnRouter(cfg-rpl)# policy SET_FULL_ROUTES
	dnRouter(cfg-rpl-policy)# rule 10 allow
	dnRouter(cfg-rpl-policy-rule-10)#set med aigp + 10
	dnRouter(cfg-rpl-policy-rule-10)#set med aigp - 5

**Removing Configuration**

To remove the set entry:
::

	dnRouter(cfg-rpl-policy-rule-10)# no set med

	dnRouter(cfg-rpl-policy-rule-10)# no set med aigp

	dnRouter(cfg-rpl-policy-rule-10)# no set med aigp + 10

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 25.2    | Command introduced                           |
+---------+----------------------------------------------+
```

## policy set med
```rst
policy set med
--------------

**Minimum user role:** operator

To set the BGP attribute MED:

**Command syntax: set med {igp-cost \| [med-value] \| [relative] [med-value]}**

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
| 25.2    | Command syntax changed                       |
+---------+----------------------------------------------+```

