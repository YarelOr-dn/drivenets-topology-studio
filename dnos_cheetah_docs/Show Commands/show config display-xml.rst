show config | display-xml
-------------------------

**Minimum user role:** viewer

Displays the show config output in XML format.


**Command syntax: show config [level-1] [level-2] | display-xml** {format}

**Command mode:** operational



**Note**

- The output of this command displays commands in an XML format, with all the hierarchy.

- When using the option 'edit-config', the configuration output is wrapped with **start** and **end** clauses as follows:

::

    <rpc message-id="urn:uuid:{uid}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <edit-config>
            <target>
                <candidate/>
            </target>

    ...

        </edit-config>
    </rpc>]]>]]>

..

**Parameter table**

+-----------+--------------------------------------------------------------+
| Parameter | Description                                                  |
+===========+==============================================================+
| format    | edit-config                                                  |
+-----------+--------------------------------------------------------------+
| level     | Level 1 - The main menu hierarchy level (e.g. interfaces)    |
|           | Level 2 - main menu sub-menu hierarchy (e.g. protocols ospf) |
+-----------+--------------------------------------------------------------+

**Example**
::

    dev-dnRouter(cfg)# sh con system ssh server | display-xml

    <config xmlns:dn-sys-ssh="http://drivenets.com/ns/yang/dn-sys-ssh" xmlns:dn-top="http://drivenets.com/ns/yang/dn-top" xmlns:dn-system="http://drivenets.com/ns/yang/dn-system">
            <dn-top:drivenets-top>
                    <dn-system:system>
                            <dn-sys-ssh:ssh>
                                    <ssh-server>
                                            <config-items>
                                                    <max-sessions>10</max-sessions>
                                                    <admin-state>enabled</admin-state>
                                            </config-items>
                                    </ssh-server>
                            </dn-sys-ssh:ssh>
                    </dn-system:system>
            </dn-top:drivenets-top>
    </config>

    dev-dnRouter(cfg)# sh con system ssh server | display-xml edit-config


    <rpc message-id="urn:uuid:8f4f002a-6f9d-40b3-aba9-2b4413593848" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <edit-config>
            <target>
                <candidate/>
            </target>
            <config xmlns:dn-sys-ssh="http://drivenets.com/ns/yang/dn-sys-ssh" xmlns:dn-top="http://drivenets.com/ns/yang/dn-top" xmlns:dn-system="http://drivenets.com/ns/yang/dn-system">
                    <dn-top:drivenets-top>
                            <dn-system:system>
                                    <dn-sys-ssh:ssh>
                                            <ssh-server>
                                                    <config-items>
                                                            <max-sessions>10</max-sessions>
                                                            <admin-state>enabled</admin-state>
                                                    </config-items>
                                            </ssh-server>
                                    </dn-sys-ssh:ssh>
                            </dn-system:system>
                    </dn-top:drivenets-top>
                    </config>
        </edit-config>
    </rpc>]]>]]>


**Command History**

+---------+----------------------------------------------------------+
| Release | Modification                                             |
+=========+==========================================================+
| 18.2    | Command introduced                                       |
+---------+----------------------------------------------------------+
