# Research: DynamoDB Session State Persistence

## R1: boto3 vs aiobotocore for Async DynamoDB

**Decision**: Use `aiobotocore` for async DynamoDB operations in write-through adapters. Use `boto3` synchronous client for shutdown drain (where we must block until writes complete).

**Rationale**: The voice server is fully async (asyncio + FastAPI). Blocking boto3 calls on the hot path would stall the event loop and add latency to audio streaming. `aiobotocore` provides native async/await DynamoDB operations. During graceful shutdown, synchronous boto3 is acceptable since we're draining (no new requests).

**Alternatives considered**:
- boto3 only (run in thread pool): Works but adds complexity — `asyncio.to_thread()` for every write. Less ergonomic.
- aioboto3: Thin wrapper around aiobotocore. Adds a dependency for minimal benefit.
- AWS SDK for Python (smithy-based): Not yet stable for DynamoDB.

## R2: Single-Table Design Pattern

**Decision**: Single table with composite key. PK = `session_id`, SK = `SESSION` | `HISTORY` | `ELICITATION`. GSI on `status` attribute for listing active sessions.

**Rationale**: Co-locates all session data for efficient batch reads on reconnection (single `Query` by PK returns all 3 records). Avoids cross-table coordination. GSI enables the "list active sessions" access pattern without scanning the whole table.

**Table Schema**:
```
Table: intent-capture-sessions
  PK: session_id (String)
  SK: record_type (String) — "SESSION", "HISTORY", "ELICITATION"
  GSI1: status-index
    GSI1PK: status (String) — "active", "closed"
    GSI1SK: last_activity (Number) — epoch seconds
  TTL attribute: expires_at (Number) — epoch seconds
```

**Alternatives considered**:
- Three separate tables: Simpler per-table but requires 3 operations on reconnection and coordinated TTL.
- Single table with SK as timestamp (event sourcing): Over-engineered for this use case — we only need latest state, not event history.

## R3: Write-Through Adapter Pattern

**Decision**: Adapters wrap existing modules via composition. Each adapter holds a reference to the in-memory module AND the DynamoDB client. On mutation, it updates in-memory first (fast path), then fires an async DynamoDB write (background task). On load, it reads from DynamoDB with strong consistency.

**Rationale**: This preserves the existing module interfaces exactly — consumers don't know persistence exists. The hot path (in-memory) stays fast. DynamoDB writes are fire-and-forget with error logging. On reconnection, DynamoDB is the source of truth.

**Pattern**:
```python
class PersistentSessionRegistry:
    def __init__(self, registry: SessionRegistry, dynamo_client):
        self._registry = registry
        self._dynamo = dynamo_client
    
    def create(self, session):
        self._registry.create(session)  # fast path
        asyncio.create_task(self._dynamo.put_session(session))  # async backup
    
    async def load(self, session_id):
        item = await self._dynamo.get_session(session_id)  # strong read
        session = deserialize(item)
        self._registry.create(session)  # hydrate in-memory
        return session
```

**Alternatives considered**:
- Subclassing: Tight coupling, fragile if base class changes.
- Middleware/hooks: More generic but harder to test and debug.
- Replace internals: Adds DynamoDB latency to every read, even hot-path.

## R4: Graceful Shutdown Persistence Strategy

**Decision**: On SIGTERM, iterate all active sessions and batch-write to DynamoDB using `batch_write_item` (up to 25 items per batch). Retry with exponential backoff for the full 30-second drain window. Log any sessions that could not be persisted.

**Rationale**: ECS sends SIGTERM then waits `stopTimeout` (30s default) before SIGKILL. We have 30 seconds to persist everything. `batch_write_item` is the most efficient bulk write. With 50 sessions × 3 records = 150 items = 6 batches — easily fits in 30 seconds even with retries.

**Implementation**:
1. Signal handler sets `draining = True`
2. Stop accepting new connections
3. For each active session: serialize state → add to batch
4. Submit batches with retry loop (max 30s total)
5. Log unprocessed items as warnings
6. Exit

**Alternatives considered**:
- Write-ahead log (local file): Adds complexity, still needs DynamoDB write on next start.
- Don't persist on shutdown (rely on write-through): Risks losing the most recent state change if it hasn't been flushed yet.

## R5: TTL and Session Expiry

**Decision**: Store `expires_at` as epoch seconds on every item. Set to `last_activity + 24 hours` (configurable). DynamoDB's native TTL feature deletes expired items automatically within ~48 hours of expiry (eventual deletion, not exact).

**Rationale**: Zero-cost cleanup with no application-side cron or Lambda. Items are eventually removed without any action. For correctness, the application also checks `expires_at` on load — if expired, treat as not found (don't wait for DynamoDB TTL to physically delete).

**Alternatives considered**:
- Application-side cleanup (scheduled task): Adds a moving part that can fail.
- Lambda trigger on stream: Over-engineered for simple expiry.
- Short TTL (1 hour): Too aggressive — users may pause for lunch and return.
