# Virtual Miner MVP

## Features
- SQLite-backed task registry
- Async scheduler
- Android + web runners
- Agent-generated task flows
- Flow validation
- Runtime state persistence
- Retry + timeout support

## Setup

```bash
pip install -r requirements.txt
```

## Generate Tasks

```bash
python main.py generate "Create a daily rewards web workflow"
```

## Start Scheduler

```bash
python main.py start
```
