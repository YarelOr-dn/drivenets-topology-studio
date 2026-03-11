show system ssh
--------------------

**Minimum user role:** viewer

Secure Shell (SSH) is a cryptographic network protocol that client applications use to securely access and manage devices over an unsecured network. It provides a secure channel for remote communication, enabling users to execute commands, transfer files, and perform administrative tasks, all while maintaining confidentiality and integrity through robust encryption methods.

To display the SSH configuration in the system:

**Command syntax: show system ssh**

**Command mode:** operational



**Parameter table**

The following information is displayed:

+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| Parameter           | Description                                                                                                                                     | Reference                                    |
+=====================+=================================================================================================================================================+==============================================+
| admin-state         | The administrative state of the SSH server per vrf                                                                                              | system ssh server mgmt0 admin-state          |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| Global admin-state  | The administrative state of the SSH server for all vrfs                                                                                         | system ssh server admin-state                |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| max-sessions        | The maximum number of allowed concurrent sessions                                                                                               | system ssh server max-sessions               |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| session-timeout     | The configured value for timeout when the session is idle                                                                                       | The TCP timeout                              |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| class-of-service    | CoS for all outgoing SSH Server sessions                                                                                                        | system ssh server class-of-service           |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| VRF                 | The SSH Server session management type (in-band, out-of-band or non-default-vrf)                                                                | default (in-band)                            |
|                     |                                                                                                                                                 | non-default-vrf (in-band)                    |
|                     |                                                                                                                                                 | mgmt0 (out-of-band)                          |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| client list         | The IP addresses that depending on the client-list type will or will not be permitted access to SSH sessions                                    | system ssh server vrf default client-list    |
|                     |                                                                                                                                                 | system ssh server vrf mgmt0 client-list type |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| ciphers             | Ciphers used by SSH Server                                                                                                                      | system ssh security ciphers                  |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| macs                | MACs used by SSH Server                                                                                                                         | system ssh security macs                     |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+
| hostkey algorithms  | Hostkey algorithms used by SSH Server                                                                                                           | system ssh security host-key-algorithms      |
+---------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------+

**Example**
::

    dnRouter# show system ssh

    Max-sessions: 6
    Session-timeout: 30 minutes
    Class-of-service: 16 (dscp)
    Ciphers: chacha20-poly1305-openssh.com,aes256-gcm-openssh.com,aes128-gcm-openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
    MACs: umac-64-etm-openssh.com,umac-128-etm-openssh.com,hmac-sha2-256-etm-openssh.com,hmac-sha2-512-etm-openssh.com,umac-64-openssh.com,umac-128-openssh.com,hmac-sha2-256,hmac-sha2-512
    Hostkey Algorithms: ssh-ed25519,ssh-ed25519-cert-v01-openssh.com,sk-ssh-ed25519-openssh.com,sk-ssh-ed25519-cert-v01-openssh.com,rsa-sha2-512,rsa-sha2-512-cert-v01-openssh.com,rsa-sha2-256,rsa-sha2-256-cert-v01-openssh.com

    VRF default
    admin-state: enabled
        Client List
          Client list type: allow
          Client list networks:
            1.2.3.0/24
            1.2.4.0/24
                2001:db8:2222::/48

    VRF my_vrf
    admin-state: disabled
        Client List
          Client list type: allow
          Client list networks:
            3.6.1.0/24
            3.2.4.0/24
                2001:db8:1111::/48

    VRF mgmt0
    admin-state: enabled
        Client List
          Client list type: allow
          Client list networks:
            1.1.1.0/24
            2.2.4.0/24
                2001:db8:1122::/48

.. **Help line:** show active ssh sessions in system.

**Command History**

+---------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                                                                                                  |
+=========+===============================================================================================================================================================================================+
| TBD     | Command introduced                                                                                                                                                                            |
+---------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
