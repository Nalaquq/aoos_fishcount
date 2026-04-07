# Validation Protocol

CV counts must be validated against concurrent human observer counts before
the data can be used for fisheries management decisions.

## Minimum Validation Requirement

Run concurrent observer counts for a minimum of **3 days** (72 hours) during
active salmon passage before leaving the system unattended.

## Metrics to Calculate

| Metric | Formula | Target |
|---|---|---|
| Detection efficiency | CV count ÷ observer count | > 0.80 |
| Species classification accuracy | Correct species ÷ total classified | > 0.85 |
| False positive rate | False detections ÷ total detections | < 0.05 |

## Reporting Format

Do not report CV counts as absolute numbers. Report as:

> "CV-estimated count: 847 ± 11% (based on 0.83 detection efficiency
> measured against 45 hours of concurrent observer counts, 95% CI)"

## Adjusting conf_threshold

If detection efficiency is low (missing fish):
- Lower `conf_threshold` toward 0.35 in `config/my_site.yaml`
- Check water clarity — turbidity > 12 inch visibility degrades detection

If false positive rate is high (counting debris or waves):
- Raise `conf_threshold` toward 0.55
- Check polarizer orientation — poor glare reduction produces false detections
