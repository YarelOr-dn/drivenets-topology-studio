protocols ospf instance area summarization-policy
-------------------------------------------------

**Minimum user role:** operator

Apply policy to control route summarization as ABR and to modify certain summarized (LSA type 3) routes metric, or filter specific prefixes from being advertised as inter-area routes.

**Command syntax: summarization-policy [summarization-policy]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area

**Note**
- By default, assuming a no totally stub/NSSA area, all the intra-area routes will be summarized and advertised as inter-area routes.

- Supported actions in the policy:

--  match ipv4 prefix.

--  set ospf-metric.

-  all other actions are ignored, and continue policy processing.

**Parameter table**

+----------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter            | Description                                                                      | Range            | Default |
+======================+==================================================================================+==================+=========+
| summarization-policy | When acting as ABR, impose route policy to filter or modify summary routes (lsa  | | string         | \-      |
|                      | type 3)                                                                          | | length 1-255   |         |
+----------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# instance INSTANCE_1
    dnRouter(cfg-protocols-ospf-inst)# area 0
    dnRouter(cfg-ospf-inst-area)# summarization-policy MY_POLICY_1


**Removing Configuration**

To return the attribute to the default state:
::

    dnRouter(cfg-ospf-inst-area)# no summarization-policy

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
