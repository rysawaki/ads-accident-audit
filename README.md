# ads-accident-audit

A domain-agnostic post-incident audit framework
for determining responsibility when complex automated systems fail.


Applied to:

Automated Driving Systems (ADS/ADAS)

Large Language Models (LLMs)

Critical Infrastructure Control Systems (e.g., power grids)


| SIA最小監査ログ      | 欧米事例で実際に出たもの                        | 具体事例           |
| -------------- | ----------------------------------- | -------------- |
| 物体検出イベント（時系列）  | 検出の有無・距離・相対速度                       | Uber ATG（NTSB） |
| クラス分類履歴        | unknown / pedestrian / bicycle 等の遷移 | Uber ATG       |
| トラッキングIDの生成・消失 | IDの付与・消滅ログ                          | Uber ATG       |
| 認識確信度（明示/暗示）   | classification が揺れた事実               | Uber ATG       |
| 接触後の再認識        | fallen object 等への再分類                | Cruise         |





This repository provides a neutral audit framework.
It does not assert fault or assign liability.

This audit framework is derived from the broader SIA (Self-Imprint Attribution) research.
