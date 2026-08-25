# exp10 night addendum (advisor gpt-5.6-sol-high)

Advisor: [VRAM stall](aafda373-56e3-4e26-a20d-d2fcff5bbe18)

1. Stay queued. No earlier launch without an actually empty card. No sharing, killing, reset, or offload.
2. Keep n=64. Sub-64 is only terminal pre-wipe salvage labeled INSUFFICIENT_POWER, never claim-bearing.
3. Keep claim gate memory.used <1500 MiB.
4. Next 2 hours: keep waiter polling; launch n=64 only when concurrency <4 and a card crosses that gate.
