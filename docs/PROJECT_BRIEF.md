# E Block Lounge Bot — Project Brief

## Problem

The lounge is currently booked through chat messages. Requests are difficult to track, availability is unclear, and overlapping or forgotten bookings are possible.

## First release

Residents should be able to:

1. Start the bot and understand how to use it.
2. View available lounge slots for a date.
3. Book one available slot with an optional purpose.
4. Receive a confirmation.
5. View and cancel their own future bookings.

Admins should be able to view all bookings and manage exceptional cases.

## Deliberate MVP choices

- Begin with fixed two-hour slots rather than arbitrary time ranges.
- Use the configured E Block timezone consistently.
- Keep the booking resource as a single lounge.
- Use a database as the source of truth.
- Start with polling locally; use a webhook in production.

## Future direction

Add a separate events capability for planned E Block activities: upcoming events, monthly calendar views, event administration, reminders, and possible calendar export.

## Non-goals for the MVP

- Payments
- Multiple lounges
- Public web dashboard
- External calendar synchronization
- AI-generated booking decisions
