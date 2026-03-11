protocols isis instance interface address-family adjacency-sid protection-eligible
----------------------------------------------------------------------------------

**Minimum user role:** operator

* For adjacency-sid configured without protection-eligible (default behavior), SID is always advertised with B flag unset, regardless of protection status in ISIS. Such adjacency-sid will not be protected and will not hold alternate path.
* For adjacency-sid configured with protected flag, sid is always advertised with B flag set. Regardless of protection status in ISIS (i.e if LFA/TI-LFA is enabled - same behavior in Cisco).

To set the adjacency-sid as protection-eligible:

**Command syntax: protection-eligible**

**Command mode:** config

**Hierarchies**

- protocols isis instance interface address-family adjacency-sid

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# interface bundle-1
    dnRouter(cfg-isis-inst-if)# address-family ipv4-unicast
    dnRouter(cfg-inst-if-afi)# adjacency-sid index 10
    dnRouter(cfg-if-afi-adj-sid)# protection-eligible


**Removing Configuration**

To return to default behavior:
::

    dnRouter(cfg-if-afi-adj-sid)# no protection-eligible

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
