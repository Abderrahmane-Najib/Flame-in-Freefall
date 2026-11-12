# P11: Fabric (SIBAL) ignition and quench limits (chart only)

**Investigations:** BASS and BASS-II, T'ien experiments. Flat **SIBAL** fabric (cotton / fiberglass blend) in concurrent flow, ISS, microgravity.

## What we show

Too few tests for a model, so this is a **chart**: O₂ (%) vs airflow (cm/s), each test coloured by result.

| Result | Tests |
|---|---|
| Burned / spread | ~15 |
| **Quenched** (flow turned down until it went out) | 6 |
| **No ignition** | 3 fresh + reused samples |
| **Blow-off** | 1 (plus 2 "no blowoff" at up to 53 cm/s) |

**Key reading:** **no ignition at 16.4 to 16.8% O₂**, so the approximate **fabric ignition limit in microgravity** is around 17% O₂. Quenching happens at ~2.2 to 3 cm/s flow.

## Data

| Source | Use |
|---|---|
| **BASS-II Summary Report, Table 7.1** (p. 104) | **Main data:** 31 tests (27 BASS-II + 4 BASS) with sample width (1.2 / 2.2 cm), flow start → end (cm/s), O₂ % and result. Type it into a small CSV with the page as source. |
| `Data/psi/PSI-25/docs/PSI-25_Science Documents_BASS-II_Test.Matrices.xlsx`, sheet `T'ien` | Same tests with sensor readings |
| `Data/psi/PSI-26/docs/PSI-26_Science Documents_As Run_Test Matrix.xlsx` | Extra BASS SIBAL rows (21% O₂) with observation text |

## Documents to use

| Document | Where | What for |
|---|---|---|
| **BASS-II Summary Report §7** (T'ien) | `Data/psi/PSI-25/docs/PSI-25_Reports_BASS-II Summary Report.pdf` | Table 7.1 (p. 104). Text on flame growth, steady spread (~40 s burn at 10 cm/s, > 60 s at 5 cm/s), *"flames spread more slowly across narrower samples, at lower flow velocities and at lower O₂."* Table A.6 (p. ~120): full log. |
| BASS fabric presentations | `Data/psi/PSI-26/docs/PSI-26_Presentations_Flammability Aspects of Fabric_USNationalCombustion2013.pdf`, `…CottonFiberglassFabric_ASGSR2012.pdf` | Images and summary for the app |
| BASS fabric paper | `Data/psi/PSI-26/docs/PSI-26_Science Documents_FlammabilityAspectsofFabric_USNationalCombustion.2013.docx` | Text for the AI assistant |

## Caveats

- **Reused samples** (partly burned) are marked "Reused". Show them faded or exclude them.
- Two O₂ readings are flagged as possibly inaccurate in Table 7.1 (tests GMT45-T1, T2).
- Flow changed during most tests. Plot the **final** flow for quench / blow-off.
- One fabric type only.
