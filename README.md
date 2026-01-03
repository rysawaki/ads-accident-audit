# ads-accident-audit

A domain-agnostic post-incident audit framework
for determining responsibility when complex automated systems fail.


Applied to:

Automated Driving Systems (ADS/ADAS)

Large Language Models (LLMs)

Critical Infrastructure Control Systems (e.g., power grids)

---

## Mapping Between **Minimal Post-Incident Audit Logs** and Logs Actually Disclosed or Contested in Western Court / Regulatory Cases

---

### 1️⃣ Perception Layer

| Minimal Post-Incident Audit Log              | What Was Actually Disclosed in Western Cases            | Concrete Case   |
| -------------------------------------------- | ------------------------------------------------------- | --------------- |
| Object detection events (timeline)           | Presence/absence of detection, distance, relative speed | Uber ATG (NTSB) |
| Classification history                       | Transitions such as unknown / pedestrian / bicycle      | Uber ATG        |
| Tracking ID creation / deletion              | Assignment and loss of tracking IDs                     | Uber ATG        |
| Recognition confidence (explicit / implicit) | Evidence of unstable classification                     | Uber ATG        |
| Post-impact re-recognition                   | Reclassification as fallen object, etc.                 | Cruise          |

**Implications**

* 👉 The *perception existence logs* fully match what has been disclosed
* 👉 Raw sensor data is **not required** to determine whether an object was recognized or not

---

### 2️⃣ Prediction Layer

| Minimal Post-Incident Audit Log     | What Was Actually Disclosed                       | Concrete Case |
| ----------------------------------- | ------------------------------------------------- | ------------- |
| Predicted trajectory update history | Frequency of path re-computation                  | Uber ATG      |
| TTC (time to collision)             | Records of TTC shortening / re-evaluation         | Uber ATG      |
| Prediction instability indicator    | Instability caused by classification fluctuations | Uber ATG      |

**Implications**

* 👉 The issue was not that *prediction was wrong*
* 👉 **It was that prediction never stabilized**

---

### 3️⃣ Planning Layer

| Minimal Post-Incident Audit Log               | What Was Actually Disclosed                | Concrete Case               |
| --------------------------------------------- | ------------------------------------------ | --------------------------- |
| Existence of avoidance / stop plan candidates | Design that suppressed avoidance plans     | Uber ATG                    |
| Safety constraint enable / disable            | Design decision to disable AEB             | Uber ATG                    |
| Risk handling policy                          | Prioritization of false-positive avoidance | Uber ATG / Tesla litigation |

**Implications**

* 👉 The question was not *“why it did not stop”*
* 👉 **But that it was designed not to stop**

---

### 4️⃣ Control Layer

| Minimal Post-Incident Audit Log | What Was Actually Disclosed             | Concrete Case |
| ------------------------------- | --------------------------------------- | ------------- |
| Brake command issuance          | No brake command issued                 | Uber ATG      |
| Actual deceleration             | Speed change immediately before impact  | Tesla         |
| Intervention latency            | Delay from stop decision to actual stop | Cruise        |

**Implications**

* 👉 It is possible to distinguish between
* 👉 **“control failure”** and **“no control request issued”**

---

### 5️⃣ Authority / Mode (Responsibility Boundary)

| Minimal Post-Incident Audit Log | What Was Actually Disclosed        | Concrete Case    |
| ------------------------------- | ---------------------------------- | ---------------- |
| Automated driving mode state    | Autopilot ON / OFF                 | Tesla litigation |
| Handover request logs           | Warning timing and content         | Tesla / Mercedes |
| Driver inputs                   | Steering torque, pedal inputs      | Tesla            |
| Responsibility attribution logs | Responsibility during L3 operation | Mercedes-Benz    |

**Implications**

* 👉 *Responsibility boundary logs*
* 👉 Are **already legal requirements in Europe**

---

### 6️⃣ Disclosure / Integrity (The Audit Itself)

| Minimal Post-Incident Audit Log      | What Was Actually Disclosed                     | Concrete Case       |
| ------------------------------------ | ----------------------------------------------- | ------------------- |
| Log completeness                     | Incomplete submission identified as a violation | Cruise (CPUC / DMV) |
| Post-hoc log modification prevention | Re-submission orders and sanctions              | Cruise              |
| Version identification               | Disclosure of design intent and limitations     | Tesla litigation    |

**Implications**

* 👉 In some cases, the sanction was not based on the accident itself
* 👉 **But on how logs were disclosed**

---

## Summary (README-ready)

> This table shows that **minimal post-incident audit logs** align with
> logs that have already been disclosed or contested
> in Western courts and regulatory investigations.
>
> Raw sensor data or model weights are not required.
> These logs are sufficient to determine **whether responsibility attribution is possible or not**.

---









This repository provides a neutral audit framework.
It does not assert fault or assign liability.

```md
*Note:* This minimal audit log specification is derived from a broader internal research framework.
```


