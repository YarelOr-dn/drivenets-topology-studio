protocols segment-routing mpls auto-policy template color seamless-bfd failure-action
-------------------------------------------------------------------------------------

**Minimum user role:** operator

Configure the failure-action to be performed when the S-BFD session fails. If 'down' - then the state of all auto-policies created with this template will be set to down if the S-BFD session fails. If it is 'none' then the SR-TE state of all auto-policies created with this template will not be affected by the S-BFD state.

**Command syntax: failure-action [failure-action]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing mpls auto-policy template color seamless-bfd

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
    dnRouter(cfg-protocols-sr-mpls)# auto-policy
    dnRouter(cfg-sr-mpls-auto-policy)# template color 3
    dnRouter(cfg-mpls-auto-policy-color-3)# seamless-bfd
    dnRouter(cfg-auto-policy-color-3-sbfd)# failure-action none


**Removing Configuration**

To return the failure-action to its default value:
::

    dnRouter(cfg-auto-policy-color-3-sbfd) no failure-action

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.0    | Command introduced |
+---------+--------------------+
