# ads-accident-audit

A domain-agnostic post-incident audit framework
for determining responsibility when complex automated systems fail.


Applied to:

Automated Driving Systems (ADS/ADAS)

Large Language Models (LLMs)

Critical Infrastructure Control Systems (e.g., power grids)



---

## Mapping Between **SIA Minimal Audit Logs** and **Logs Actually Disclosed or Contested in Western Court / Regulatory Cases**

---

### 1️⃣ Perception Layer

| SIA Minimal Audit Log                        | What Was Actually Disclosed in Western Cases            | Concrete Case   |
| -------------------------------------------- | ------------------------------------------------------- | --------------- |
| Object detection events (timeline)           | Presence/absence of detection, distance, relative speed | Uber ATG (NTSB) |
| Classification history                       | Transitions such as unknown / pedestrian / bicycle      | Uber ATG        |
| Tracking ID creation / deletion              | Assignment and loss of tracking IDs                     | Uber ATG        |
| Recognition confidence (explicit / implicit) | Evidence of unstable classification                     | Uber ATG        |
| Post-impact re-recognition                   | Reclassification as fallen object, etc.                 | Cruise          |

---

### 2️⃣ Prediction Layer

| SIA Minimal Audit Log               | What Was Actually Disclosed                       | Concrete Case |
| ----------------------------------- | ------------------------------------------------- | ------------- |
| Predicted trajectory update history | Frequency of path re-computation                  | Uber ATG      |
| TTC (time to collision)             | Records of TTC shortening / re-evaluation         | Uber ATG      |
| Prediction instability flag         | Instability caused by classification fluctuations | Uber ATG      |

---

### 3️⃣ Planning Layer

| SIA Minimal Audit Log                         | What Was Actually Disclosed                | Concrete Case               |
| --------------------------------------------- | ------------------------------------------ | --------------------------- |
| Existence of avoidance / stop plan candidates | Design that suppressed avoidance plans     | Uber ATG                    |
| Safety constraint enable/disable              | Design decision to disable AEB             | Uber ATG                    |
| Risk handling policy                          | Prioritization of false-positive avoidance | Uber ATG / Tesla litigation |

---

### 4️⃣ Control Layer

| SIA Minimal Audit Log  | What Was Actually Disclosed             | Concrete Case |
| ---------------------- | --------------------------------------- | ------------- |
| Brake command issuance | No brake command issued                 | Uber ATG      |
| Actual deceleration    | Speed change immediately before impact  | Tesla         |
| Intervention latency   | Delay from stop decision to actual stop | Cruise        |

---

### 5️⃣ Authority / Mode (Responsibility Boundary)

| SIA Minimal Audit Log           | What Was Actually Disclosed        | Concrete Case    |
| ------------------------------- | ---------------------------------- | ---------------- |
| Automated driving mode state    | Autopilot ON / OFF                 | Tesla litigation |
| Handover request logs           | Warning timing and content         | Tesla / Mercedes |
| Driver inputs                   | Steering torque, pedal inputs      | Tesla            |
| Responsibility attribution logs | Responsibility during L3 operation | Mercedes-Benz    |

---

### 6️⃣ Disclosure / Integrity (The Audit Itself)

| SIA Minimal Audit Log                | What Was Actually Disclosed                     | Concrete Case       |
| ------------------------------------ | ----------------------------------------------- | ------------------- |
| Log completeness                     | Incomplete submission identified as a violation | Cruise (CPUC / DMV) |
| Post-hoc log modification prevention | Re-submission orders and sanctions              | Cruise              |
| Version identification               | Disclosure of design intent and limitations     | Tesla litigation    |



---







This repository provides a neutral audit framework.
It does not assert fault or assign liability.

This audit framework is derived from the broader SIA (Self-Imprint Attribution) research.
