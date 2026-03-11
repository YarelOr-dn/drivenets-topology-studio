show policy 
------------

**Minimum user role:** viewer

To display a policy:



**Command syntax: show policy** [policy-name]

**Command mode:** operational




**Parameter table**

+-------------+----------------------------------------------------------------------------------------------------+-------------------+
| Parameter   | Description                                                                                        | Range             |
+=============+====================================================================================================+===================+
| policy-name | The name of the policy to display. If you do not specify a policy, all policies will be displayed. | 1..255 characters |
+-------------+----------------------------------------------------------------------------------------------------+-------------------+

**Example**
::

	dnRouter# show policy 
	policy SET6_VPN_RCDE_OUT
	  rule 10 allow
	    match extcommunity CL_RT_13979:100497
	    set ipv6 next-hop ::ffff:10:40:193:113
	  !
	  rule 20 allow
	    match extcommunity CL_RT_13979:100499
	    set ipv6 next-hop ::ffff:10:40:193:113
	  !
	!
	
	
	policy SET_AGGSET
	  rule 10 allow
	    call SET_DDOS
	    set community "no-export, 65060:2010"
	  !
	!
	
	
	dnRouter# show policy SET6_VPN_RCDE_OUT
	
	policy SET6_VPN_RCDE_OUT
	  rule 10 allow
	    match extcommunity CL_RT_13979:100497
	    set ipv6 next-hop ::ffff:10:40:193:113
	  !
	  rule 20 allow
	    match extcommunity CL_RT_13979:100499
	    set ipv6 next-hop ::ffff:10:40:193:113
	  !
	!
	
	

.. **Help line:** Displays a prefix-list

**Command History**

+---------+----------------------------------+
| Release | Modification                     |
+=========+==================================+
| 6.0     | Command introduced               |
+---------+----------------------------------+
| 7.0     | Added AIGP information to output |
+---------+----------------------------------+
| 10.0    | Removed protocol filter          |
+---------+----------------------------------+


