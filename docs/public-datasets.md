# Public dataset access and terms

MeshShield includes read-only CSV adapters for PaySim and IEEE-CIS. The downloads stay local. The repository contains neither dataset, prepared copies, nor fitted artifacts produced from them.

| Dataset | Character | Access and terms | Loader |
| --- | --- | --- | --- |
| [PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) | Synthetic mobile-money transactions with simulator-assigned fraud labels. It is not independent real-fraud evidence. | The Kaggle listing identifies CC BY-SA 4.0. Retain attribution and check the current dataset page and [license text](https://creativecommons.org/licenses/by-sa/4.0/) before sharing adapted data or results. Download requires a Kaggle account. | `load_paysim(data/raw/paysim/PS_20174392719_1491204439457_log.csv)` |
| [IEEE-CIS Fraud Detection](https://www.kaggle.com/competitions/ieee-fraud-detection/data) | Historical e-commerce transactions and identity data released for a Kaggle competition. `TransactionDT` is elapsed time from a hidden reference, not a calendar timestamp. | Competition access requires accepting Kaggle's [competition rules](https://www.kaggle.com/competitions/ieee-fraud-detection/rules). The data is not licensed by this code repository. Do not redistribute it; check current terms for any intended use. | `load_ieee_cis(train_transaction.csv, train_identity.csv)` |

The PaySim loader maps `step` to a synthetic UTC timeline anchored at 2020-01-01. The IEEE-CIS adapter maps `TransactionDT` to a synthetic UTC anchor at 2017-01-01. These anchors preserve event ordering for experiments and must not be interpreted as the source event's real calendar time. Missing device identity is represented as `unknown-device`; it is not imputed from future rows.

## Download

Install the optional Kaggle CLI and configure its credentials outside this repository, then run:

```text
python scripts/download_datasets.py paysim
python scripts/download_datasets.py ieee-cis
```

The IEEE-CIS command only works after the account accepts the competition rules. No credential file or token belongs in this project. Raw files are ignored by Git under `data/raw/`.

## Current boundary

These adapters are input utilities, not proof of an end-to-end external-data experiment. The app's existing model report remains the generated synthetic benchmark unless a separate experiment explicitly names the external dataset, version, split, and measured results. IEEE-CIS should not be labeled real UPI or offline-payment data.
