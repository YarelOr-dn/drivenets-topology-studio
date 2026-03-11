protocols ospf graceful-restart ietf-helper-strict-lsa-checking admin-state
---------------------------------------------------------------------------

**Minimum user role:** operator

Indicates whether or not an OSPF restart helper (for IETF mode) should terminate the graceful restart when there is a change to an LSA that could be flooded
to the restarting router or when there is a changed LSA on the restarting router's retransmission list when the graceful restart is initiated.  
Default admin-state is enabled.
To configure ietf-helper-strict-lsa-checking admin-state:

**Command syntax: ietf-helper-strict-lsa-checking admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols ospf graceful-restart

**Note**

- To reduce the risk of data loss for a stand-alone system hot-patch upgrade of the routing service, the operator is advised to disable the LSA strict checking on neighbors.

**Parameter table**

+-------------+--------------------------------------------------------------------+--------------+---------+
| Parameter   | Description                                                        | Range        | Default |
+=============+====================================================================+==============+=========+
| admin-state | Configure Strict LSA checking of IETF NSF per RFC 3623 Section B.2 | | enabled    | enabled |
|             |                                                                    | | disabled   |         |
+-------------+--------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)# ietf-helper-strict-lsa-checking admin-state disabled


**Removing Configuration**

To revert ietf-helper-strict-lsa-checking admin-state to the default value
::

    dnRouter(cfg-protocols-ospf-gr)# no ietf-helper-strict-lsa-checking admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
