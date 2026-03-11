protocols segment-routing mpls policy seamless-bfd remote-reflector-discriminator
---------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the discriminator value of the SR-TE path endpoint.

**Command syntax: remote-reflector-discriminator [remote-reflector-discriminator]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy seamless-bfd

**Parameter table**

+--------------------------------+----------------------------------------------------------------------------------+------------------+---------+
| Parameter                      | Description                                                                      | Range            | Default |
+================================+==================================================================================+==================+=========+
| remote-reflector-discriminator | User can optionally supply the remote discriminator value that will be used by   | | 1-4294967295   | \-      |
|                                | the S-BFD                                                                        | | A.B.C.D        |         |
+--------------------------------+----------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# remote-reflector-discriminator 14267
    dnRouter(cfg-mpls-policy-sbfd)#


    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# remote-reflector-discriminator 187.23.45.9
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To remove the remote-reflector-discriminator value:
::

    dnRouter(cfg-mpls-policy-sbfd) no remote-reflector-discriminator

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
