# Hamilton integrity registry

Hamilton is the CFO agent at [QualityEngineer.ai](https://qualityengineer.ai):
an AI that answers questions about money. This repository lets anyone check,
without trusting us, that the numbers Hamilton gives come from a specific,
validated, unchanged calculation engine, and when that engine existed.

We publish the proof, not the engine. The engine and the full validation
results stay private and are available to auditors under NDA. Everything here
is enough to hold us to them.

## The problem this solves

An AI that talks about money has two ways to be wrong. It can pick the wrong
inputs, and it can do the arithmetic wrong. Language models are unreliable at
arithmetic, and a confident wrong number looks exactly like a right one.

Hamilton never does arithmetic itself. Every figure comes from a deterministic
engine: exact decimal and rational math, no floating point in money paths, a
single stated rounding policy. The same input always produces the same output,
byte for byte, on any machine.

That is a claim. This repository is how you check it.

## What every Hamilton number carries

Each result the engine produces is wrapped in an envelope with two hashes:

- `input_sha256`: the SHA-256 of the exact inputs, in canonical form.
- `engine_sha256` (short form `engine_id`, e.g. `ham-04350554a5e3`): the
  SHA-256 fingerprint of the exact engine code that produced it.

Together they say: *this code, run on these inputs, printed this.* Anyone
holding the inputs and the engine can rerun it and must get the same bytes.

Input hashes are shared with the people who hold the inputs and with auditors.
They are never posted publicly, because the hash of a small private file can
sometimes be guessed back to its contents. Only engine fingerprints are public.

## What a release is

Each time the engine changes, it is revalidated and released. A release
publishes one `manifest.json` containing:

| Field | Meaning |
| --- | --- |
| `engine_id`, `engine_sha256` | The fingerprint of the engine code |
| `test_suite_sha256` | The fingerprint of the test suite that checked it |
| `self_check` | How many automated checks passed and failed |
| `validation` | Pass and fail counts from each validation study (below) |
| `dossier_sha256` | The SHA-256 of the private validation dossier |
| `previous_manifest_sha256` | The hash of the previous release's manifest |

Two mechanisms make the registry tamper evident:

1. **A hash chain.** Every manifest names the previous one's hash. Changing or
   deleting any past release breaks every link after it.
2. **A Bitcoin timestamp.** The hash of each manifest is committed to the
   Bitcoin blockchain through [OpenTimestamps](https://opentimestamps.org),
   a free, open protocol. The `.ots` file next to each manifest is the proof.
   It shows the manifest existed no later than a specific Bitcoin block. Nobody,
   including us, can backdate it.

**Commit publicly, reveal privately.** The dossier behind each release is
private, but its hash is public and timestamped. An auditor who receives the
dossier can confirm it is exactly the one committed on that date, unchanged.

## Validation, and the standards it uses

Every release is validated against outside standards, not only our own tests:

| Study | Standard | What it shows |
| --- | --- | --- |
| Performance qualification | NIST Statistical Reference Datasets, scored by log relative error (McCullough, 1998) | Statistical results match values NIST certified with 500 digit arithmetic |
| Independent cross check | Differential testing against separate implementations (numpy, scipy) | Tens of thousands of random cases agree with independently written formulas |
| Repeatability and reproducibility | Gauge R&R framing, exact Clopper-Pearson bounds | Hundreds of thousands of reruns, across processes and Python versions, produce identical bytes |
| Agent agreement study | Blind repeated trials, attribute agreement | How often Hamilton picks the right inputs and reaches the right answer |

The framework follows computerized system validation practice from regulated
industries (installation, operational and performance qualification, as in
GAMP 5), because that is what quality engineers already audit against.

When validation finds a defect, the defect is fixed, the engine gets a new
fingerprint, and every study is rerun on the new code before a release. A
release never cites validation that ran on different code: the release tool
refuses.

## Release 1.2.1 at a glance

From `releases/1.2.1/manifest.json`:

- Engine `ham-04350554a5e3`, 826 automated checks, 0 failures.
- NIST StRD: 245 of 245 certified values pass, 243 to every certified digit.
- Cross check: 85,117 cases, 0 mismatches on the engine side.
- Repeatability and reproducibility: 280,224 trials, 0 mismatches.
- Agent agreement: 32 of 32 blind trials correct.
- Bitcoin timestamp: confirmed in block 967,720, mined 2026-09-19 15:44:31 UTC
  (merkle root `6103bcbe…77be44`, checkable on any block explorer).

Validation of the previous engine found real defects (an output that could
depend on JSON key order, a crash on long bond schedules, a mislabelled
health flag, and statistics printed with too few digits). All were fixed and
revalidated before this release.

## Verify it yourself

Requires Python 3. For the Bitcoin check, install the OpenTimestamps client
(`pip install opentimestamps-client`), or drop `manifest.json.ots` onto the
verifier at [opentimestamps.org](https://opentimestamps.org).

```bash
python verify_release.py releases/registry.jsonl          # chain and manifest hashes
python verify_release.py releases/registry.jsonl --ots    # plus the Bitcoin timestamps
```

Auditors who have been given the engine source or a dossier can go further:

```bash
python verify_release.py releases/registry.jsonl --engine path/to/engine
python verify_release.py releases/registry.jsonl --dossier path/to/dossier --version 1.2.1
```

The engine fingerprint is SHA-256 over a sorted manifest of
`<sha256 of file>  <path>` lines, one per engine file, with line endings
normalized to LF, so any checkout on any operating system yields the same value.

## Feedback

Think a check is weak, or have a standard we should test against? Open an
issue. Found a case where the engine is wrong? Tell us; if you are right, it
becomes a permanent test in the next release.

## What this does not claim

- It does not claim Hamilton's judgment is perfect. The agent study measures
  it and publishes the interval.
- It does not prove any particular number was correct for your business. It
  proves which code produced it and that the code was validated as described.
- The Bitcoin timestamp proves when a manifest existed, not that its contents
  are true. The validation dossier, which auditors can inspect, is what backs
  the contents.

License: MIT for the verifier; the documentation is CC BY 4.0.
