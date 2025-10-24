# Rollout Plan – Channels & Ops

MVP (WhatsApp-only, worldwide routes)
- Deliver end-to-end WhatsApp booking, hardened webhooks, basic agent console
- KPIs: quote→paid, time-to-3-offers, ticket issuance success

Next Channels (low-lift → impact, still worldwide)
1) Web app (self-serve) – reuse API; embed Paystack
2) Instagram/Facebook DMs – Meta Graph adapter; shared templates
3) Email/SMS – links/receipts; local SMS aggregator
4) Web chat widget – routes to same orchestrator
5) Phone/IVR – agent-assisted; send links via SMS/WhatsApp
6) GBM/Telegram – optional, segment-specific

Operational Readiness
- Playbooks: payment failure, schedule change, involuntary reroute, refund/void
- Alerts: webhook failures, pricing mismatch, deadlines (<2h)
- Access: RBAC for agents/supervisors/finance; least privilege



