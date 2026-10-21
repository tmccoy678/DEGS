# Exact numeric task input

The engineering gate applies both exact numerical preservation and representation
limits when loading task JSON. The same input policy applies to `validate`,
`evaluate`, and `explain`, with either JSON or text output.

## Supported representations

- Integer tokens are converted directly to Python integers without a floating-point
  intermediary.
- Tokens containing a decimal point or exponent are converted directly from their
  source spelling to `decimal.Decimal`. Construction preserves every supplied
  coefficient digit independently of the arithmetic context's precision.
- Each numeric token may contain at most **4,300 decimal digits in total**, counting
  coefficient and exponent digits, including leading and trailing zeros. Signs,
  the decimal point, and the exponent marker do not count as digits.
- An explicitly written exponent must have an absolute value no greater than
  **10,000**. Leading zeros in an exponent are accepted within the total digit
  budget; for example, `1e000001` has the same value as `10`.
- Any tighter active Python integer-conversion limit remains in force for integer
  tokens. The gate does not disable or raise that interpreter limit.

The digit and exponent bounds are explicit resource limits for this input format.
They retain a broad finite-decimal range, including the reported `1e-4000`
counterexample, while bounding conversion work and exponent representations.
They are not claims that numbers outside those limits are mathematically invalid.

## Rejected representations

The gate rejects a number exceeding either representation limit before constructing
its numeric value. `NaN`, `Infinity`, and `-Infinity` are rejected. Invalid JSON
number syntax is rejected by the JSON decoder. Input rejection returns a structured
`FAIL` with exit code `4`; conversion never substitutes a rounded, zero, or infinite
value for an unsupported token.

Accepted numbers still must satisfy the task schema and readiness rules. For
example:

| Raw token and field | Exact interpretation | Gate consequence |
| --- | --- | --- |
| `schema_version: 1.0` | Exactly one | Satisfies the version constant |
| `schema_version: 1.0000000000000001` | Greater than one | `FAIL`, exit `4` |
| `orphan_count: 1e-4000` | Positive and nonzero | Fails the required zero constraint; cannot pass readiness |
| `orphan_count: 0e10000` | Exactly zero | Satisfies the zero constant |
| Any numeric field: `1e10001` | Exceeds the supported exponent bound | Input `FAIL`, exit `4` |

JSON numerical equality remains value-based: `1`, `1.0`, and `1e0` are equal.
Booleans remain distinct from numbers, including inside arrays and objects. Exact
parsing preserves numerical value, not the original lexical spelling of a token.

The output's risk-tier and authority-lane fields contain only a supplied string or
`null`. Invalid non-string identifiers receive field diagnostics rather than being
echoed as arbitrary input objects. This keeps malformed numerical identifiers from
causing a serialization failure.

## Verification scope

`tests/test_numeric_input.py` tests raw JSON at the loader and CLI boundaries. It
covers the precision and underflow counterexamples, supported equivalent constants,
representation-limit boundaries, nonfinite rejection, Boolean distinction, active
interpreter limits where available, and malformed identifiers in both output modes.

The separate public schema benchmark loads its own source cases. Its existing
results measure the selected schema helper behavior and do not independently
establish this task-input numeric policy.
