protocols segment-routing mpls path pcep-delegation
---------------------------------------------------

**Minimum user role:** operator

A path defined with 'pcep delegation' will hold no local ERO definition and is expected to be controlled by PCE. 
Only when there is a valid PCE ERO, can the path be used to forward traffic
To define the path to be delegated and controlled by PCE in active stateful mode:


**Command syntax: pcep-delegation**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls path

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# path PATH_1
    dnRouter(cfg-sr-mpls-path)# pcep-delegation
    dnRouter(cfg-mpls-path-pcep)#


**Removing Configuration**

To remove path definition of delegated path:
::

    dnRouter(cfg-sr-mpls-path)# no pcep-delegation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
