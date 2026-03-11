routing-policy policy rule match rib-has-route
----------------------------------------------

**Minimum user role:** operator

To match if a route exist in Routing Information Base (RIB):

**Command syntax: match rib-has-route [match-rib-has-route]** protocol [protocol]

**Command mode:** config

**Hierarchies**

- routing-policy policy rule

**Note**

- Match is exact prefix match

- Match is for selected routes only

**Parameter table**

+---------------------+----------------------------------------------------------------------------------+----------------+---------+
| Parameter           | Description                                                                      | Range          | Default |
+=====================+==================================================================================+================+=========+
| match-rib-has-route | Match if a requested route exists in the Routing Information Base (RIB) as       | | A.B.C.D/x    | \-      |
|                     | selected route for FIB installation.                                             | | X:X::X:X/x   |         |
+---------------------+----------------------------------------------------------------------------------+----------------+---------+
| protocol            | Match that route required by rib-has-route was installed to Routing Information  | | bgp          | \-      |
|                     | Base (RIB) by specific protocol                                                  | | connected    |         |
|                     |                                                                                  | | ebgp         |         |
|                     |                                                                                  | | ibgp         |         |
+---------------------+----------------------------------------------------------------------------------+----------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# match rib-has-route 1.12.18.4/31
    dnRouter(cfg-rpl-policy-rule-10)# exit
    dnRouter(cfg-rpl-policy)# rule 20 allow
    dnRouter(cfg-rpl-policy-rule-20)# match rib-has-route 2005:100:0:d::/128

    dnRouter# configure
    dnRouter(cfg)# routing-policy
    dnRouter(cfg-rpl)# policy MY_POLICY
    dnRouter(cfg-rpl-policy)# rule 10 allow
    dnRouter(cfg-rpl-policy-rule-10)# match rib-has-route 223.16.16.6/32 protocol connected


**Removing Configuration**

To remove match rib-has-route criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no match rib-has-route

To remove match rib-has-route protocol criteria:
::

    dnRouter(cfg-rpl-policy-rule-10)# no match rib-has-route 223.16.16.6/32 protocol

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
