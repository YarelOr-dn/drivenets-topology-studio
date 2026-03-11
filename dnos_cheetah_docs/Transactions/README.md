# DNOS Transactions Reference

*Configuration transaction management commands*

---

## Overview

DNOS uses a transactional configuration model where changes are staged, validated, and then committed atomically. This ensures configuration consistency and provides rollback capabilities.

---

## Transaction Workflow

```
1. Enter configuration mode: configure
2. Make changes: set, delete, edit
3. Review changes: show | compare
4. Validate: commit check
5. Apply: commit
```

---

## Configuration Mode Commands

### configure

Enter configuration mode to begin making changes.

**Syntax:**
```
configure
configure exclusive
configure private
```

**Options:**
| Mode | Description |
|------|-------------|
| `configure` | Shared configuration mode |
| `configure exclusive` | Exclusive lock on configuration |
| `configure private` | Private copy of configuration |

**Example:**
```
dn> configure
Entering configuration mode
dn#
```

---

### exit

Exit configuration mode.

**Syntax:**
```
exit
exit discard
```

**Options:**
| Option | Description |
|--------|-------------|
| `exit` | Exit with uncommitted changes warning |
| `exit discard` | Discard changes and exit |

**Example:**
```
dn# exit
warning: uncommitted changes
dn# exit discard
Discarding uncommitted changes
dn>
```

---

## Commit Commands

### commit

Apply pending configuration changes.

**Syntax:**
```
commit
commit check
commit confirmed <minutes>
commit comment "<message>"
commit at <time>
commit synchronize
```

**Options:**
| Option | Description |
|--------|-------------|
| `commit` | Apply changes immediately |
| `check` | Validate without applying |
| `confirmed <min>` | Auto-rollback after minutes if not confirmed |
| `comment` | Add commit message for audit trail |
| `at <time>` | Schedule commit for later |
| `synchronize` | Sync config to standby (HA) |

---

### commit check

Validate configuration without applying.

**Syntax:**
```
commit check
```

**Example:**
```
dn# commit check
configuration check succeeds

dn# commit check
error: configuration check-out failed
   protocols bgp: local-as is required
```

---

### commit confirmed

Apply changes with automatic rollback if not confirmed.

**Syntax:**
```
commit confirmed <minutes>
```

**Parameters:**
| Parameter | Description | Range |
|-----------|-------------|-------|
| `minutes` | Rollback timer in minutes | 1-60 |

**Example:**
```
dn# commit confirmed 5
commit confirmed will be automatically rolled back in 5 minutes unless confirmed

# After verifying connectivity:
dn# commit
commit complete, rollback timer cancelled
```

**Use case:** Safe remote configuration changes. If you lose connectivity, the system automatically reverts.

---

### commit comment

Add a message to the commit for audit purposes.

**Syntax:**
```
commit comment "<message>"
```

**Example:**
```
dn# commit comment "Added BGP neighbor 10.0.0.2 for customer ACME - ticket #12345"
commit complete
```

---

### commit at

Schedule a commit for a specific time.

**Syntax:**
```
commit at <time>
```

**Example:**
```
dn# commit at 02:00
commit scheduled for 02:00
```

---

### commit synchronize

Synchronize configuration to standby NCPs (High Availability).

**Syntax:**
```
commit synchronize
```

**Example:**
```
dn# commit synchronize
commit synchronize complete
```

---

## Rollback Commands

### rollback

Revert to a previous configuration state.

**Syntax:**
```
rollback <number>
```

**Parameters:**
| Number | Description |
|--------|-------------|
| 0 | Current active configuration |
| 1 | Previous configuration (before last commit) |
| 2-49 | Older configurations |

**Example:**
```
dn# rollback 1
load complete

dn# show | compare
[edit protocols bgp]
-    neighbor 10.0.0.2 {
-        remote-as 65002;
-    }

dn# commit
commit complete
```

---

### show system commit

View commit history.

**Syntax:**
```
show system commit
```

**Example Output:**
```
Commit ID  User     Time                 Comment
0          admin    2024-12-24 10:30:15  Added BGP neighbor
1          admin    2024-12-24 09:15:00  Updated interface MTU
2          admin    2024-12-23 14:45:30  Initial configuration
```

---

### compare rollback

Compare current/candidate config with rollback point.

**Syntax:**
```
compare rollback <number>
```

**Example:**
```
dn# compare rollback 1
[edit protocols bgp]
+    neighbor 10.0.0.2 {
+        remote-as 65002;
+    }
```

---

## Load Commands

### load

Load configuration from a file or input.

**Syntax:**
```
load <mode> <source>
```

**Modes:**
| Mode | Description |
|------|-------------|
| `merge` | Merge with existing configuration |
| `override` | Replace entire configuration |
| `replace` | Replace matching sections only |
| `set` | Load set-style commands |
| `patch` | Load a configuration patch |

**Sources:**
| Source | Description |
|--------|-------------|
| `/path/to/file` | Load from local file |
| `terminal` | Paste configuration interactively |
| `http://url` | Load from URL |
| `ftp://url` | Load from FTP |
| `scp://url` | Load from SCP |

**Example - Load merge from file:**
```
dn# load merge /var/tmp/bgp-config.txt
load complete
dn# show | compare
dn# commit
```

**Example - Load override:**
```
dn# load override /var/tmp/full-config.txt
load complete
dn# commit check
dn# commit
```

**Example - Load from terminal:**
```
dn# load merge terminal
[Type or paste configuration, end with Ctrl+D]
interfaces ge0/0/1 {
    description "New description"
}
^D
load complete
```

**Example - Load set commands:**
```
dn# load set terminal
set interfaces ge0/0/1 description "WAN Link"
set protocols bgp local-as 65001
^D
load complete
```

---

## Save Commands

### save

Save configuration to a file.

**Syntax:**
```
save <destination>
```

**Example:**
```
dn# save /var/tmp/backup.txt
Saved 1234 lines to /var/tmp/backup.txt

dn> show config | save /var/tmp/running.txt
```

---

## Clear Commit Commands

### clear system commit

Clear commit history.

**Syntax:**
```
clear system commit
clear system commit <id>
```

**Example:**
```
dn> clear system commit 5
Cleared commit 5 from history
```

---

## Configuration Locking

### show system configuration lock

View configuration locks.

**Syntax:**
```
show system configuration lock
```

**Example Output:**
```
Lock held by: admin
Lock type: exclusive
Locked since: 2024-12-24 10:30:00
```

---

### request system configuration lock

Request a configuration lock.

**Syntax:**
```
request system configuration lock
request system configuration unlock
```

---

## Transaction Best Practices

### 1. Always Validate Before Committing

```
dn# commit check
configuration check succeeds
dn# commit
```

### 2. Use commit confirmed for Remote Changes

Especially when modifying management interfaces or routing:

```
dn# commit confirmed 5
# Test connectivity
dn# commit
```

### 3. Review Changes Before Committing

```
dn# show | compare
[edit]
+    interfaces ge0/0/1 {
+        description "WAN Link";
+    }
```

### 4. Use Meaningful Commit Comments

```
dn# commit comment "CHANGE-12345: Added customer ACME BGP peering"
```

### 5. Maintain Rollback History

Keep sufficient rollback points for recovery:

```
dn# rollback 1    # Quick fix
dn# rollback 5    # Recover from bad maintenance window
```

### 6. Use Configuration Groups for Reusability

```
groups {
    STANDARD-MTU {
        interfaces <*> {
            mtu 9216
        }
    }
}
apply-groups STANDARD-MTU
```

---

## Error Handling

### Commit Failures

```
dn# commit
error: commit failed
   interfaces ge0/0/1: interface does not exist
   
# Fix the error
dn# delete interfaces ge0/0/1
dn# commit
```

### Concurrent Modification

```
dn# commit
error: configuration modified by another user
Reload configuration and retry

dn# exit discard
dn> configure
dn# show | compare
```

### Rollback Failures

```
dn# rollback 10
error: rollback 10 not available (only 5 rollbacks stored)

dn# rollback 4
load complete
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Enter config mode | `configure` |
| Exclusive config | `configure exclusive` |
| Exit config mode | `exit` |
| Discard and exit | `exit discard` |
| Validate config | `commit check` |
| Apply config | `commit` |
| Safe remote commit | `commit confirmed <min>` |
| Add commit message | `commit comment "<msg>"` |
| Revert to previous | `rollback 1` |
| Load from file | `load merge <file>` |
| Replace config | `load override <file>` |
| View changes | `show | compare` |
| Compare rollbacks | `compare rollback <n>` |
| View commit history | `show system commit` |
| Save config | `save <file>` |

