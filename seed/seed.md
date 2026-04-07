# Seeding Rules into the Database

This guide explains how to populate the rule-api database with test rules and how device IDs are generated in the IoT Hub Alpha system.

## Quick Start

Seed the database with default test rules:

```bash
docker compose run --rm rule-api python -m seed.seed_rules
```

### Expected Output

```
[seed_rules] Starting rule seeding...
[seed_rules] Database: db:5432/iot_hub_alpha_db
[seed_rules] Seeding 9 rules...
[seed_rules] ✓ Committed 0 rules to database
[seed_rules] Results: 0 inserted, 9 skipped, 0 errors
[seed_rules] ✓ Done.
```

> **Note:** Rules are skipped if they already exist in the database. To clear existing rules, use the `--clear` flag.

### Clear and Reseed

```bash
docker compose run --rm rule-api python -m seed.seed_rules --clear
```

### Dry Run (Preview Changes)

```bash
docker compose run --rm rule-api python -m seed.seed_rules --dry-run
```

## Device ID Generation

Device IDs in the IoT Hub Alpha system are generated using **UUID5 with DNS namespace** to create deterministic, repeatable identifiers from device serial numbers.

### Why UUID5?

- **Deterministic**: Same serial number always produces the same UUID
- **Unique**: Different serial numbers produce different UUIDs
- **RFC 4122 compliant**: Standard UUID format
- **No central authority needed**: Generated locally without requiring a registry

### How Device IDs Are Generated

#### 1. **From Serial Number (UUID5)**

When a device sends telemetry with a serial number, the system generates a device_id using:

```
UUID5(NAMESPACE_DNS, serial_number)
```

**Example:**
- Serial number: `"VIB-SN-001"`
- Device ID: `a716e2e7-df82-5640-ade5-624f11de0c7b` (deterministic)

#### 2. **Generation Process**

The UUID5 algorithm:

1. Takes the **DNS namespace UUID**: `6ba7b810-9dad-11d1-80b4-00c04fd430c8`
2. Takes the device **serial number** as input
3. Applies **SHA-1 hash** to the concatenation (per RFC 4122 section 4.3)
4. Produces a **deterministic UUID**

#### 3. **Where Device IDs Are Generated**

| Component | Location | Trigger |
|-----------|----------|---------|
| **mqtt-ingest** | `app/core/message_handler.py:build_raw_event()` | When MQTT message is received |
| **rule-engine** | `RuleConsumer.java:processMessage()` | When device_id missing from message |
| **seed script** | `seed/seed_rules.py:generate_device_uuid()` | When creating test data |

#### 4. **Code Examples**

**Python (mqtt-ingest):**
```python
from uuid import NAMESPACE_DNS, uuid5

device_id = str(uuid5(NAMESPACE_DNS, serial_number))
# Example: uuid5(NAMESPACE_DNS, "VIB-SN-001") → "a716e2e7-df82-5640-ade5-624f11de0c7b"
```

**Java (rule-engine):**
```java
private static UUID uuid5DnsNamespace(String name) throws NoSuchAlgorithmException {
    UUID NAMESPACE_DNS = UUID.fromString("6ba7b810-9dad-11d1-80b4-00c04fd430c8");
    byte[] ns = toBytes(NAMESPACE_DNS);
    byte[] nb = name.getBytes(StandardCharsets.UTF_8);
    byte[] buf = new byte[ns.length + nb.length];
    System.arraycopy(ns, 0, buf, 0, ns.length);
    System.arraycopy(nb, 0, buf, ns.length, nb.length);

    byte[] hash = MessageDigest.getInstance("SHA-1").digest(buf);
    hash[6] = (byte) ((hash[6] & 0x0f) | 0x50);  // version 5
    hash[8] = (byte) ((hash[8] & 0x3f) | 0x80);  // variant

    ByteBuffer bb = ByteBuffer.wrap(hash);
    return new UUID(bb.getLong(), bb.getLong());
}
```

## Seeding Test Rules

### Seed Data File

Rules are defined in `services/rule-api/seed/seed_rules_data.json`:

```json
[
  {
    "device_serial": "CNC-SN-002",
    "name": "Critical Temperature – CNC Mill #2",
    "description": "Stops the machine if temperature exceeds the critical threshold",
    "condition": {
      "type": "leaf",
      "operator": "gt",
      "threshold": 100.0
    },
    "is_enabled": true
  },
  ...
]
```

### Rules Created

The seeding process creates **9 test rules** for different devices:

| Device | Rule | Condition | Purpose |
|--------|------|-----------|---------|
| CNC Mill #2 | Critical Temperature | value > 100.0 | Stop machine if overheating |
| CNC Mill #2 | Safe Zone | value ≤ 100.0 | Allow normal operation |
| Lathe #1 | High Vibration | value > 50.0 | Detect machinery issues |
| Lathe #1 | Normal Vibration | value ≤ 50.0 | Normal operation |
| Power Monitoring | High Consumption | value > 5000.0 | Alert on excessive usage |
| Power Monitoring | Normal Consumption | value ≤ 5000.0 | Normal operation |
| ... | ... | ... | ... |

## Message Flow with Device IDs

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. MQTT Simulator publishes telemetry with serial_number        │
│    {"serial_number": "VIB-SN-001", "value": 45.2, ...}         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. mqtt-ingest receives and generates device_id                 │
│    device_id = uuid5(NAMESPACE_DNS, "VIB-SN-001")              │
│    device_id = "a716e2e7-df82-5640-ade5-624f11de0c7b"          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Publishes to telemetry.clean with device_id in envelope     │
│    {                                                             │
│      "device_id": "a716e2e7-df82-5640-ade5-624f11de0c7b",      │
│      "serial_number": "VIB-SN-001",                             │
│      "payload": {"value": 45.2, ...}                            │
│    }                                                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. rule-engine consumes from telemetry.clean                    │
│    - Extracts device_id from message                            │
│    - Fetches rules for device from rule-api                     │
│    - Evaluates rules against telemetry value                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. If rule triggered, produces event to event.topic             │
│    {                                                             │
│      "type": "internal",                                         │
│      "rule_id": "84f10a3c-b57d-4d31-abe4-67d1eabfed96",       │
│      "device_id": "a716e2e7-df82-5640-ade5-624f11de0c7b",     │
│      "triggered": true,                                         │
│      "message": "Rule triggered"                                │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Verify Seeded Rules

### List all rules in database:

```bash
docker compose exec db psql -U postgres -d iot_hub_alpha_db \
  -c "SELECT id, device_id, name, is_enabled FROM rules ORDER BY created_at;"
```

### Count rules by device:

```bash
docker compose exec db psql -U postgres -d iot_hub_alpha_db \
  -c "SELECT device_id, COUNT(*) as rule_count FROM rules GROUP BY device_id;"
```

### Check specific device rules:

```bash
docker compose exec db psql -U postgres -d iot_hub_alpha_db \
  -c "SELECT id, name, condition FROM rules WHERE device_id = 'a716e2e7-df82-5640-ade5-624f11de0c7b';"
```

## Testing the Full Flow

After seeding, test the end-to-end system:

```bash
# Run simulator (publishes telemetry)
docker compose run --rm simulator -f demo2.json -c 5 -r 0.5 -v -m mqtt
```

**Expected behavior:**
1. Simulator publishes 20 telemetry messages (5 devices × 4 messages each)
2. mqtt-ingest receives and adds device_id using UUID5
3. rule-engine fetches rules from rule-api for each device
4. rule-engine evaluates rules and triggers events
5. Events appear in event.topic

**Verify in logs:**
```bash
docker compose logs rule-engine | grep -i "fetched\|cached\|event produced"
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'app'"

**Solution:** Use the correct command:
```bash
docker compose run --rm rule-api python -m seed.seed_rules
```

### Error: "Database connection refused"

**Solution:** Ensure the database is healthy:
```bash
docker compose up -d db
docker compose exec db pg_isready
```

### Rules not appearing after seeding

**Solution:** Check if they were skipped (already exist):
```bash
docker compose exec db psql -U postgres -d iot_hub_alpha_db -c "SELECT COUNT(*) FROM rules;"
```

To force re-seed:
```bash
docker compose run --rm rule-api python -m seed.seed_rules --clear
```

## Related Files

- **Seed Data**: `services/rule-api/seed/seed_rules_data.json`
- **Seed Script**: `services/rule-api/seed/seed_rules.py`
- **Rule Model**: `services/rule-api/app/models/models.py`
- **mqtt-ingest Handler**: `mqtt-ingest/app/core/message_handler.py`
- **rule-engine Consumer**: `services/rule-engine/src/main/java/com/iothubalpha/ruleengine/consumer/RuleConsumer.java`
