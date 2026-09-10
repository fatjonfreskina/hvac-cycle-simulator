# HVAC Learning Lab - Product Roadmap

## Vision

Build an interactive learning environment that helps students develop HVAC
engineering intuition by predicting, simulating and explaining the behavior of
vapor-compression systems. The product should teach cause and effect, not merely
calculate properties.

## Target users

1. Mechanical, energy and automation engineering students
2. Graduate HVAC engineers and new hires
3. University lecturers and corporate trainers
4. Firmware and control engineers entering the HVAC domain

## Learning loop

Every guided experiment should follow the same pattern:

1. Present a physical scenario and a question.
2. Ask the learner to predict the outcome.
3. Let the learner change one or more parameters.
4. Show synchronized circuit, state-table and P-h diagram results.
5. Explain the physical cause of each important change.
6. Check understanding with a short question.

## Milestone 0 - Reliable foundation

**Goal:** make the repository installable, testable and physically coherent.

- [x] Replace the original project template packaging
- [x] Provide a working command-line example
- [x] Implement a complete idealized steady-state cycle
- [x] Add typed states and cycle results
- [x] Add input validation and first-law balance tests
- [ ] Add continuous integration for supported Python versions
- [ ] Define engineering conventions and a glossary
- [ ] Add reference cases validated against independent calculations
- [ ] Clean and align the exploratory notebooks with the package API

**Exit criteria:** a new contributor can clone, install, run and test the model
using only the README.

## Milestone 1 - Thermodynamic learning engine

**Goal:** expose enough information to explain the cycle, not just solve it.

- [x] Return saturation levels, superheat, subcooling and pressure ratio
- [x] Add heating COP and component-specific energy balances
- Generate P-h and T-s cycle coordinates
- Add warnings for unsafe or non-physical operating points
- Support a small, documented refrigerant set
- Add parameter sweeps for comparative experiments
- Document model assumptions and limitations beside every result

**Exit criteria:** the engine supports three independently validated teaching
examples and produces all data needed by the web interface.

## Milestone 2 - Learning Lab MVP

**Goal:** publish a memorable browser-based learning experience without login.

- Interactive cycle schematic
- Synchronized P-h diagram and state table
- Controls for refrigerant, temperatures, superheat, subcooling, efficiency and flow
- Immediate explanations of parameter effects
- Friendly validation messages instead of raw CoolProp errors
- Shareable experiment configuration
- Responsive, accessible interface

Initial guided labs:

1. Build and identify the four stages of the ideal cycle
2. Explore superheat and liquid-return risk
3. Explore subcooling, refrigeration effect and COP

**Exit criteria:** a student can complete all three labs independently and a
lecturer can run them from a public URL.

## Milestone 3 - Academic pilot

**Goal:** validate learning value with real students and lecturers.

- Expand to 8-10 guided laboratories
- Add prediction-before-simulation questions
- Create instructor notes, worksheets and solution keys
- Export results to CSV and a printable report
- Add anonymous feedback and learning checks
- Pilot with at least one class or structured student group

Candidate advanced labs include ambient-temperature effects, compressor
efficiency, flash gas, refrigerant comparison, dirty condensers and diagnosis
from incomplete measurements.

**Exit criteria:** documented feedback and learning evidence from a real pilot,
followed by a prioritized iteration plan.

## Milestone 4 - Instructor tools

**Goal:** make the lab easy to adopt in repeatable courses.

- Assignment authoring and parameter constraints
- Randomized problem variants
- Instructor-only solutions and grading rubrics
- Class progress and misconception analytics
- LMS-friendly links and exports
- Optional self-hosted deployment

This milestone should be shaped by pilot feedback rather than built speculatively.

## Milestone 5 - Controls and firmware track

**Goal:** connect thermodynamics education to embedded HVAC control.

- Discrete-time plant and sensor models
- Electronic expansion valve and variable-speed compressor models
- Superheat PID with saturation and anti-windup
- Startup, shutdown and protection state machines
- Noise, delay, quantization and sensor-fault injection
- Software-in-the-Loop interface for C/C++ controller code

This becomes an advanced learning path and the project's main professional
differentiator.

## Validation principles

- Every model states its assumptions and validity range.
- Every component has conservation-law tests.
- Reference scenarios are checked against independent sources or measurements.
- Educational explanations distinguish ideal behavior from field behavior.
- User interfaces display engineering units explicitly.

## Sustainable product path

Keep the simulation core and introductory labs open source. Validate demand
before adding paid infrastructure. Potential paid offerings include instructor
workflows, premium lab packs, hosted class management, corporate training,
custom scenarios and SIL/HIL engineering integrations.

## Near-term backlog

1. Configure CI and verify Python 3.11-3.13.
2. Add state-table and diagram-ready output to `CycleResult`.
3. Create and validate three reference cycles.
4. Choose the web stack after the learning-engine API stabilizes.
5. Build the first guided lab before building accounts or instructor analytics.
