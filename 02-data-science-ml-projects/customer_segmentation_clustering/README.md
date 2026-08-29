# Customer Segmentation via RFM + K-Means

Rebuilds the CRM behavioral-clustering work referenced on the resume
("analyzed customer spending patterns and purchase frequency to build
CRM clusters for customer segmentation" — Kellogg's and retail analytics
work) as a full, runnable pipeline, since the original production SAS
work and retail data can't be shared.

## Data

Synthetic transaction data for 1,500 customers across five underlying
purchase-behavior archetypes (champion, loyal, at-risk, new, lapsed) —
the archetype label is used only to validate that clustering recovers a
sensible structure, never as a model input.

## What it does

1. Aggregates raw transactions into **RFM** features (Recency, Frequency,
   Monetary) per customer.
2. Scales features and fits K-Means, using an elbow plot to support the
   choice of *k*.
3. Names each resulting cluster using a composite RFM ranking (Champions,
   Loyal/Growing, At Risk, Lapsed/Low Value) — the same segment vocabulary
   used in real CRM targeting work.
4. Visualizes segments and saves a profile summary.

## Running

```bash
pip install pandas numpy scikit-learn matplotlib
python segmentation.py
```

## Outputs

- `segment_profiles.csv` — mean recency/frequency/monetary and size per segment
- `elbow_plot.png` — inertia vs. k
- `segment_scatter.png` — recency vs. monetary, colored by segment

## Results (synthetic data)

| Segment | Customers | Avg. Recency (days) | Avg. Frequency | Avg. Monetary |
|---|---|---|---|---|
| Champions | ~165 | ~26 | ~25 | ~$3,050 |
| Loyal / Growing | ~355 | ~49 | ~13 | ~$1,100 |
| At Risk (was active) | ~510 | ~134 | ~5 | ~$440 |
| Lapsed / Low Value | ~470 | ~299 | ~3 | ~$205 |

The four recovered clusters line up cleanly with the underlying customer
archetypes used to generate the data, confirming the pipeline recovers
real structure rather than arbitrary groupings.
