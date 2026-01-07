## Professional Enterprise Few-Shot (Tone + Structure)

### 1
Goal: Reduce latency risk in a new rollout.  
Voice: Formal, quantified, ownership-driven.  
Output:  
Objective: Cut P95 latency by 20% before launch.  
Assumptions: traffic doubles; no CDN changes.  
Actions (Owner/When/Metric):  
1) Profile top 3 endpoints (Owner: Backend, This week, Metric: P95 < 400ms).  
2) Add circuit breakers for upstreams (Owner: SRE, This week, Metric: <1% error budget).  
3) Run canary at 10% traffic (Owner: Release, Next week, Metric: rollback < 5 min).  
Controls: rollback plan, alerting tuned to new SLOs.  
Outcome: Go/no-go based on P95 + error budget.

### 2
Goal: Harden data provenance for customer-facing content.  
Voice: Formal, risk-aware.  
Output:  
Objective: Ensure every published claim has a traceable source.  
Assumptions: mixed internal/external references.  
Actions:  
1) Tag sources by domain risk (Owner: Content Ops, Today, Metric: 100% tagged).  
2) Enforce citations per section (Owner: Editor, This week, Metric: 0 uncited claims).  
3) Spot-check 5% of posts weekly (Owner: QA, Ongoing, Metric: <1% citation gaps).  
Controls: allowlist/denylist domains; block publish on missing citations.  
Outcome: Audit-ready references with owner + timestamp.

### 3
Goal: Improve incident response clarity.  
Voice: Directive, measurable.  
Output:  
Objective: Cut MTTR by 15% this quarter.  
Assumptions: on-call rotates weekly; runbooks partially stale.  
Actions:  
1) Update top 10 runbooks with current owners (Owner: SRE, This week, Metric: 100% ownership).  
2) Add decision trees for rollback/feature-flag paths (Owner: Eng Lead, Next week, Metric: trees in runbooks).  
3) Simulate 2 priority-1 drills per month (Owner: Incident Commander, Ongoing, Metric: MTTR trend).  
Controls: postmortems must include what-to-automate.  
Outcome: Faster, repeatable response with audited changes.

### 4
Goal: Align AI-generated outputs with compliance.  
Voice: Precise, control-heavy.  
Output:  
Objective: Zero PII in generated content.  
Assumptions: mixed sources; new model rollout.  
Actions:  
1) Enable PII scrubber pre/post generation (Owner: Platform, This sprint, Metric: 0 PII leaks in samples).  
2) Restrict references to allowlist domains (Owner: Content Ops, Today, Metric: 100% allowlist compliance).  
3) Add QA check for high-risk topics (Owner: Compliance, Ongoing, Metric: pass/fail tracked).  
Controls: block publish on PII hit; log model + prompt for each artifact.  
Outcome: Compliant drafts with traceability.

### 5
Goal: Improve handoff between research and delivery.  
Voice: Concise, owner-focused.  
Output:  
Objective: Reduce spec rework by 25%.  
Assumptions: specs often lack acceptance criteria.  
Actions:  
1) Add “definition of ready” checklist to every spec (Owner: PM, This week, Metric: 100% coverage).  
2) Require examples + non-goals per feature (Owner: Author, This week, Metric: present in PRD).  
3) Pilot 2 spec reviews with QA + Eng before commit (Owner: PM, This sprint, Metric: rework rate).  
Controls: block dev start without checklist.  
Outcome: Fewer revisions; clearer ownership.
