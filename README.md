# airesearch

AI research on feedback-driven self-correction, ethical AI, and adversarial testing in autonomous agent systems.

## Papers

- **paper.md** — *Failure Is the Teacher: A Survey of Feedback-Driven Self-Correction in Autonomous AI Agent Systems* — surveys 4 primary systems + 20 landscape papers on reliability, 10 Ethical AI dimensions, and adversarial testing (91 references)
- **paper_seed.md** — *Confirmation Bias in Self-Improving AI: Measuring the Gap Between Self-Reported and Actual Capability Growth* — introduces the Infinite Seed framework and dual-scoring methodology for detecting metric inflation

## The Infinite Seed Experiment

A self-evolving Python program that rewrites its own source code using an LLM, with dual-scoring to detect confirmation bias. See [seed/README.md](seed/README.md).

```bash
cd seed
./setup_experiment.sh 01
./run.sh 01
```

## Supporting Data

- **knowledge_graph.json** — 180 nodes, 512 edges mapping papers, concepts, and relationships
- **latest_papers_2025_2026.md** — 48 curated papers across 13 categories (agents, safety, fairness, adversarial testing, etc.)

## Tests

```bash
cd seed
source .venv/bin/activate
python -m pytest tests/ -v   # 127 tests
```
