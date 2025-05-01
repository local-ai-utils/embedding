#!/usr/bin/env bash
#
# generate_embeddings.sh
# ----------------------
# Bulk-create and store example embeddings that mimic the kinds of
# quick voice notes a busy manager might dictate during the day.
#
# Usage: ./generate_embeddings.sh
#
# The script loops over a here-document containing one note per line
# and calls `embedding get "<note>" --save` for each.

set -euo pipefail

while IFS= read -r note; do
  # Escape any embedded double quotes so they survive the CLI call
  safe_note=${note//\"/\\\"}
  echo "embedding get \"${safe_note}\" --save"
  embedding get "${safe_note}" --save
done <<'NOTES_EOF'
Email Sarah about the Q2 timeline
Schedule one-on-one with DevOps lead
Draft agenda for Friday stand-up
Update the sprint board before lunch
Ping finance for latest budget numbers
Review pull request #482
Book conference room for roadmap review
Prepare slides for customer demo
Follow up on the security audit action items
Ask design team for new icon set
Call vendor about support renewal
Finish performance review feedback
Send onboarding checklist to new hire
Log bug report from yesterday’s demo
Share weekly OKR update with team
Organize folders in shared drive
Submit travel request for DevCon
Check backup status on production cluster
Brainstorm team-building ideas
Set up interview loop for backend candidate
Move Jira ticket DEV-921 to in-progress
Review analytics dashboard for adoption trends
Confirm lunch order for client visit
Clean up old feature flags in codebase
File expense report for Seattle trip
Draft outage post-mortem outline
Double-check license counts for SaaS tools
Sync with legal on NDA revisions
Test patched build on staging
Collect feedback on new hiring rubric
Send birthday card to Emma
Archive obsolete documentation pages
Follow up with IT about laptop replacement
Write thank-you note to partner team
Add “culture” topic to next retro
Schedule dental appointment reminder
Re-run load tests after caching fix
Check status of GDPR ticket
Order business cards for interns
Review Q3 headcount forecast
Ask HR about wellness stipend balance
Turn on OOO message for Monday
Update Trello board labels
Merge feature toggle cleanup branch
Draft quarterly newsletter intro
Refresh AWS credentials in CI
Set calendar hold for brainstorming session
Ping recruiter for candidate pipeline stats
Revisit OKR wording for clarity
Finalize survey questions for beta users
Kick off usability testing task
Touch base with product marketing
Clean inbox to zero before 5 pm
Re-label Slack channels per naming guide
Ask support for top pain points this week
Plan brown-bag lunch topic
Publish API deprecation notice
Request design review on new mockups
Prepare summary slide for exec meeting
Log hardware asset tag for new monitor
Pay outstanding invoice #7731
Verify rollout config in LaunchDarkly
Update Confluence homepage banner
Invite data team to sprint review
Reconcile credit-card charges
File PTO request for July 5th
Confirm venue for off-site
Share customer quote on Slack
Set recurring reminder to stretch
Record quick win for weekly highlights
Document API error codes
Check on pending SOC 2 evidence
Assign mentor to new grad hire
Trim backlog tickets older than six months
Follow up on accessibility audit notes
Post fun poll in team channel
Update favicon in staging site
Schedule code freeze for release
Review staging logs for 500 errors
Add myself as reviewer on PR#512
Whitelist new IP for partner API
Reply to engineering blog comments
Sync escalation roster with pager duty
Draft job description for SRE intern
Tag analytics events in checkout flow
Close loop on legal redlines
Share reading list on leadership channel
Add glossary terms to onboarding doc
Start draft for annual report
Confirm keynote speaker travel
Export metrics for QBR deck
Update unit test coverage badge
Create T-shirt sizes for roadmap items
Add security checklist to repo README
Send reminder for hackathon sign-ups
Reschedule UX critique to Thursday
Merge updated CONTRIBUTING guide
Contact recruiter about offer letter ETA
Do quick pulse-check with remote team
Migrate Jira filters to new naming
Upload logo assets to Brandfolder
Enable MFA enforcement reminder
Block time for deep-work session
Flag flaky test to fix later
Publish docker image to registry
Refactor helper utils for readability
Collect screenshots for app store
Rotate secrets in Kubernetes cluster
Log meeting minutes in Notion
Ask PM for priority clarification
Review open RFC documents
Send weekend read suggestion
Update onboarding Trello template
Sync roadmap slide with updated metrics
Book AMAs for next month
Verify SSL cert expiry dates
Create notion page for OKR ideas
Add escalations channel to Slack
Ping customer success for NPS comments
Copy checklist into shared template
Push feedback to performance portal
Check remaining budget for swag
Add dark-mode toggle ticket
Document monitoring playbook
Confirm hostname change rollout
Share data privacy update
Request AWS cost report
Draft welcome email for new beta users
Test fallback flow on slow network
Add changelog entry for hotfix
Prepare talking points for investor call
Review design tokens PR
Request update from analytics vendor
File ticket to remove dead code
Run linter on legacy folder
Test multi-language support
Add example snippets to API docs
Arrange coffee chat with mentee
Update PTO calendar invite
Sync billing settings with new plan
Review error-budget policy
Post weekly gratitude shout-outs
Tag marketing on feature flag change
Clean up unused S3 buckets
Review quarterly capacity plan
Set up retrospective MURAL board
Send Zoom link for office hours
Check error spike alert thresholds
Refine interview questions for culture fit
Renew domain names expiring soon
Audit IAM roles for least privilege
Update git hooks for commit lint
Share slides from internal demo
Build prototype for dark-mode nav
Collect RSVPs for holiday party
Write snippet for release blog
Schedule server patch window
Publish incident timeline internally
Ask ops to resize DB volume
Move keynote slides to shared folder
Review PR for license compliance
Send follow-up survey after training
Draft guidance on meeting best practices
Reset demo environment database
Ping content team for copy edits
Mark done items in Planner board
Confirm T-shirts order size mix
List blockers for next sprint
Run cross-browser tests
Clean stale branches in git
Help intern file first PR
Add new policy link to footer
Turn on feature flag for 10 % users
Touch up header animation timing
Update pair-programming rota
Finalize launch checklist sign-offs
Ask vendor rep about roadmap
Upload signed MSA to contract vault
Suggest topic for all-hands lightning talk
Send Zoom recording to absent attendee
Close feedback loop on pricing page
Generate KPIs for monthly report
Update privacy policy version
Verify staging cache headers
Backup notes from whiteboard session
Review roadmap assumptions
Prepare budget line items for 2026
Document escalation matrix contacts
Merge hotfix for billing webhook
Check translation quality in Spanish
Request NDA signature from partner
Post daily stand-up summary
Update Dockerfile base image
Audit public S3 buckets
Draft retention policy update
Invite sales to tech deep-dive
Fix broken link checker config
Send highlight reel to execs
Confirm lead-capture form tracking
Clear completed tasks in Planner
Set baseline metrics for new feature
Research competitor pricing tiers
Schedule skip-level meetings
Ask designer for icon variations
Update K8s ingress annotations
Order HDMI adapters for conference room
Post gif to celebrate bug fix
Check contracts for auto-renew clauses
Create Slack alias for support rotation
Review metrics for DAU slump
Write unit test for edge case
Ask finance for forecast assumptions
Sync repo labels across projects
Publish internal FAQ draft
Create Airtable base for user interviews
Run penetration test scans
Capture screenshots for handbook
Send “thanks” kudos in recognition app
Check TLS min-version policy
Update elevator pitch doc
Coordinate lunch-and-learn session
Pair with junior dev on review
Confirm agenda for leadership off-site
Ping QA about edge-case regression
Refine nomenclature in schema
Merge config-as-code PR
Review story mapping board
Send reminder for quarterly objectives
Export CSV for partner integration
Book recruiter screen follow-ups
Publish shared calendar for PTO
Enable cost-savings recommendation
Verify HSTS headers in prod
Update zoom background guidelines
Investigate slow query alert
Compile list of API rate-limit errors
Sync with data team on ETL pipeline
Check status of bug bounty report
Submit talk proposal to meetup
Create demo script for trade show
Ask ops to audit firewall rules
Post link to new brand guidelines
Update footer links on marketing site
Review open security findings
Order webcam for new remote hire
Add codeowners file to repo
Draft announcement for feature sunset
Migrate legacy cron jobs to airflow
Enable session-replay tool in staging
File accessibility VPAT draft
Ask finance to set PO for renewal
Track P90 response times
Verify alert mute schedule
Publish service catalogue page
Delete old Terraform state files
Share KPI graph in Slack
Move checklist items to “done”
Re-enable autoscaling policy
Schedule database vacuum run
Document local dev setup steps
Send out meeting recording link
Compile dev-env bootstrap script
Add friction-log entry
Update dashboard color palette
Check failover replication lag
Invite interns to hackathon kickoff
Post gif to celebrate milestone
Align log levels across microservices
Request capacity increase for cache
Gather customer testimonials
Submit bug to open-source project
Check CRON expression for report
Update email footer to new address
Push schema migration to staging
Review new color-contrast ratios
Synchronize HR system profile pics
Pin critical dependencies in pip
Close stale GitHub issues
Tag release v1.7.3
Ask analytics for retention cohort
Refresh preview links in CMS
Confirm default timeout in nginx
Attach spec doc to Jira ticket
Review CLA agreement status
Create diagram for service mesh
Set up buddy system for on-call
Ask mentor for feedback on plan
Double-check error messages grammar
Post link to mental-health resources
Enable click-stream logging flag
Rotate personal access tokens
Tweet about product demo video
Add risk assessment section
Request design tokens export
Ping lawyer about contract clause
Label experiment groups in db
Attach trace-id to logs
Update readme quick-start
NOTES_EOF

for note in "${NOTES[@]}"; do
  # Escape any embedded double-quotes so they survive the CLI call.
  safe_note=${note//\"/\\\"}
  echo "embedding get \"${safe_note}\" --save"
  embedding get "${safe_note}" --save
done