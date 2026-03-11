protocols segment-routing mpls policy seamless-bfd failure-action
-----------------------------------------------------------------

**Minimum user role:** operator

Configure the failure-action to be performed when the S-BFD session fails. If 'down' - then the SR-TE policy state is set to down if the S-BFD session fails. If it is 'none' then the SR-TE state is not affected by the S-BFD state.

**Command syntax: failure-action [failure-action]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls policy seamless-bfd

**Parameter table**

+----------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter      | Description                                                                      | Range    | Default |
+================+==================================================================================+==========+=========+
| failure-action | Define whether failure of the S-BFD session will bring the SR-TE state 'down' or | | down   | down    |
|                | not affect it                                                                    | | none   |         |
+----------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# mpls
    dnRouter(cfg-protocols-sr-mpls)# policy SR_POLICY_1
    dnRouter(cfg-sr-mpls-policy)# seamless-bfd
    dnRouter(cfg-mpls-policy-sbfd)# failure-action none
    dnRouter(cfg-mpls-policy-sbfd)#


**Removing Configuration**

To return the failure-action to its default value:
::

    dnRouter(cfg-mpls-policy-sbfd) no failure-action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
