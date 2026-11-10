# Identity working slice

This slice reads the eight CSV files in `data/` and gives every customer record a `person_key`.
Records with the same key are treated as one real person.
It uses only the Python 3 standard library.

## Run it

From this folder:

    python3 -m identity --data ../data --out .

It writes `identities.csv` and `review_queue.csv` here and prints a short summary.
Add `--label-sample analysis/pairs_to_label.csv` to also regenerate the hand-labelling sample.
Run the tests with `python3 -m unittest discover -s tests`.

Latest run on the shipped data: 1,994 records, 610 persons, 26 review items covering 132 record pairs, largest cluster 9 records.
331 persons span all four systems, 3 span three and 191 span two.

## Outputs

`identities.csv` has one row per customer record: 533 e-commerce customers, 689 CRM accounts, 433 portal registrations and 339 EHR charts.
The columns are `system`, `record_id`, `person_key` and `confidence`.
The key is a hash of the smallest member record, so it is the same on every run for the same data.
This is a prototype shortcut.
The key can be guessed from a record ID and it changes if a lower-sorting record joins the cluster.
The target design mints a random key once, stores it and never derives it from source data.

Confidence is a match score, not a calibrated probability.
It comes from a logistic of hand-set weights, so it ranks links but 0.95 does not mean a 95 percent chance.
It is the weakest link on the record's path to the cluster anchor, which is the member the key comes from.
92 records sit at exactly 1.0: the 82 singletons and records joined only by a deterministic link.
The anchor itself takes its strongest link.
A record that is alone in its cluster gets 1.0, which means only that nothing else was linked to it.
It does not mean the record is certain to have no duplicate.
Check `review_queue.csv` for singletons that have open candidates.

`review_queue.csv` lists candidate links that were not made, one row per pair of persons.
A reviewer answers one question per row: are these two persons one person.
The columns are `person_key_a`, `person_key_b`, the strongest record pair (`system_a`, `record_id_a`, `system_b`, `record_id_b`), its `score`, the `reason` codes, `supporting_pairs` and `supporting_records`.
The last two give the count and the list of every record pair that raised the same question.
It holds only IDs, scores and reason codes because the data is treated as protected health information.
Reason codes name the evidence that agreed or disagreed, for example `first_name_agree;surname_agree;birthdate_missing;phone_shared`.
Codes starting with `cluster_conflict_` mean the pair scored high enough to link but a cluster rule blocked it.
`two_ehr_charts_never_auto_merged` marks two charts that look like one person.

## How matching works

1. Normalise. Emails are trimmed and lowercased with a dot-insensitive variant key. A plus tag is kept, so tagged addresses stay distinct. US phones reduce to 10 digits and a number with another country code keeps every digit. Names are case-folded and mapped through a nickname table. A blank birthdate or 1920-01-01 means unknown. Addresses reduce to street number plus zip.
2. Deterministic links. A portal registration and an EHR chart that share a kit barcode through `lab_results` are linked at score 1.0 when name and birthdate also agree. In all 406 results they do.
3. Candidate pairs. Two records become a pair when they share a normalised email, a dot-variant email, a phone, surname plus zip or surname plus birthdate.
4. Scoring. Each pair gets a score from a logistic of a bias plus additive weights, written out in `identity/scoring.py`. Agreeing birthdate, first name, surname and email push it up. A different first name after nickname mapping pushes it down hard, so relatives who share surname, phone, zip and email stay apart. Phone and address are household evidence and carry small weights. CRM emails and the `ecom_customer_id` stamp count for less because the legacy sync wrote them onto relatives' accounts. The kit-to-order buyer link only adds weight when the full name also agrees. Two known birthdates that differ veto the pair outright, transpositions included.
5. Thresholds. A score of 0.90 or more links automatically. That figure is provisional until the false-match rate has been measured. Two addresses that match only after a plus tag is removed go to review whatever they score, because that rule has not been validated. From 0.60 to 0.90 the pair goes to the review queue. Below 0.60 nothing happens.
6. Constrained clustering. Auto links are applied from the highest score down with union-find. A union is skipped and the pair goes to review if the cluster would hold two known birthdates or two canonical first names or two EHR charts.

## Assumptions

- A false merge exposes one person's health data to another. A missed link costs a review. The thresholds favour precision.
- Consecutive record IDs say nothing about identity and are not used.
- A registration's buyer may be a gift giver or a relative, so the buyer link is supporting evidence only.
- A different surname alone is a penalty, not a veto, because names change.
- Weights were set by reasoning about the data and checked by eye. They were not fitted to labels because there is no ground truth file.

## Known limitations

- Precision and recall are not measured. `analysis/pairs_to_label.csv` holds a simple random sample of 100 of the 2,902 auto links, drawn with a fixed seed, plus random samples of the review queue and of pairs just under the threshold. `python3 analysis/evaluate.py analysis/pairs_to_label.csv` reports the false-match rate of auto links with a 95 percent interval once a person has labelled them. With no false match in 100 the upper bound is about 3.7 percent, which is a spot check. `--label-auto 600` draws the 600 the rollout gate asks for.
- E-commerce has no birthdate. Two e-commerce records with the same name and no differing evidence cannot be told apart from a father and son with the same name. These pairs fall below the auto threshold unless other records tie them together.
- A person who shares one email, one phone and one address with a same-named relative who has no birthdate on file could still be merged if the other evidence lines up. The cluster birthdate rule only helps when a birthdate exists somewhere in the cluster.
- Two EHR charts for one person are never merged, so duplicate charts stay in the review queue until a person decides.
- Weights are hand-set and the nickname table is short. A rare nickname missing from the table makes two records of one person look like different people, which costs a review and not a false merge.
- Large blocks above 60 records are skipped. None occur in this data.
- The data holds US phone numbers only, so the handling of other country codes is tested with made-up values and not seen in the data.
