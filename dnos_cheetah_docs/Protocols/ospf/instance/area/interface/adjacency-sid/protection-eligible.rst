protocols ospf instance area interface adjacency-sid protection-eligible
------------------------------------------------------------------------

**Minimum user role:** operator

* For adjacency-sid configured without protection-eligible (default behavior), SID is always advertised with B flag unset, regardless of protection status in OSPF. Such adjacency-sid will not be protected and will not hold alternate path.
* For adjacency-sid configured with protected flag, sid is always advertised with B flag set. Regardless of protection status in OSPF (i.e if LFA/TI-LFA is enabled - same behavior in Cisco).

To set the adjacency-sid as protection-eligible:

**Command syntax: protection-eligible**

**Command mode:** config

**Hierarchies**

- protocols ospf instance area interface adjacency-sid

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# instance ospf1
    dnRouter(cfg-protocols-ospf-inst)# area 0
    dnRouter(cfg-ospf-inst-area)# interface bundle-1
    dnRouter(cfg-inst-area-if)# adjacency-sid index 10
    dnRouter(cfg-area-if-adj-sid)# protection-eligible


**Removing Configuration**

To return to default behavior:
::

    dnRouter(cfg-area-if-adj-sid)# no protection-eligible

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.2    | Command introduced |
+---------+--------------------+
