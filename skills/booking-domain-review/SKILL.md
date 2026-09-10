---
name: e-block-booking-domain-review
description: Review lounge-booking changes for conflicts, timezones, permissions, cancellation rules, and data integrity.
---

# E Block booking-domain review

Use this skill for booking, availability, cancellation, admin, or database changes.

Check at minimum:

- past dates and invalid time ranges
- the configured timezone and daylight-saving assumptions
- duplicate requests and overlapping bookings
- database-level or transaction-safe conflict prevention
- ownership checks for viewing and cancelling bookings
- admin authorization and auditability
- user-visible behavior when a slot becomes unavailable
- minimal and safe logging of resident information

Return findings ordered by severity, with the affected file and a concrete remediation.
