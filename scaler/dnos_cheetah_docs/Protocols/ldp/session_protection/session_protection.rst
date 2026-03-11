protocols ldp session protection
--------------------------------

**Minimum user role:** operator

Enables the LDP session protection, and enters it’s configuration hierarchy.
Once enabled, LDP will initiate targeted hellos to any discovered neighbor to protect LDP sessions even if a direct link goes down.
By default the feature is disabled.
To enable LDP session protection:

**Command syntax: session protection**

**Command mode:** config

**Hierarchies**

- protocols ldp

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# session protection
    dnRouter(cfg-protocols-ldp-session-prot)#


**Removing Configuration**

To remove session protection:
::

    dnRouter(cfg-protocols-ldp)# no session protection

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
