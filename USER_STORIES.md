# DataWipe User Stories

## Epic 1: Account Discovery & Import

### US-1.1: Multi-Format CSV Import
**As a** user with passwords in various managers  
**I want to** upload CSV exports from any password manager (Bitwarden, LastPass, 1Password, Dashlane, KeePass, Chrome, Firefox)  
**So that** I can import all my accounts regardless of which manager I use

**Acceptance Criteria:**
- System auto-detects CSV format from structure/headers
- Supports all major password manager export formats
- Shows preview of detected accounts before import
- Handles parsing errors gracefully with clear error messages

### US-1.2: Duplicate Account Management
**As a** user with multiple accounts on the same service  
**I want to** see and manage duplicate accounts separately  
**So that** I can choose which specific accounts to delete

**Acceptance Criteria:**
- Duplicate accounts (same site, different username) shown separately
- Visual indication of duplicates in the account list
- Ability to select/deselect duplicates independently

### US-1.3: Manual Account Entry
**As a** user who wants to add specific accounts  
**I want to** manually add individual accounts  
**So that** I can include accounts not in my password manager

**Acceptance Criteria:**
- Form for manual account entry (site name, URL, username, password, email)
- Validation of required fields
- Ability to add multiple accounts sequentially

### US-1.4: Secure Password Storage
**As a** security-conscious user  
**I want** my passwords encrypted at rest  
**So that** my credentials are protected even if the database is compromised

**Acceptance Criteria:**
- AES-256 encryption for stored passwords
- Encryption keys properly managed and rotated
- Passwords only decrypted when needed for deletion process

## Epic 2: Account Categorization & Risk Assessment

### US-2.1: Automatic Account Categorization
**As a** user with many accounts  
**I want** accounts automatically categorized by type  
**So that** I can review and delete accounts by category

**Acceptance Criteria:**
- Auto-categorization into: Social Media, Financial, Shopping, Entertainment, Productivity, Other
- Category detection based on domain/service name
- Ability to manually change categories
- Filter/sort accounts by category

### US-2.2: Risk Assessment & Prioritization
**As a** user concerned about data privacy  
**I want** accounts prioritized by data sensitivity risk  
**So that** I can focus on deleting high-risk accounts first

**Acceptance Criteria:**
- Risk score (1-10) based on: data type collected, breach history, service reputation
- Visual risk indicators (colors/badges)
- Sort accounts by risk level
- Risk explanation tooltip

### US-2.3: Smart Deletion Suggestions
**As a** user overwhelmed by many accounts  
**I want** AI-powered suggestions on what to keep vs delete  
**So that** I can make informed decisions quickly

**Acceptance Criteria:**
- Suggestions based on: last usage, importance, alternatives available
- "Keep", "Delete", or "Review" recommendations
- Ability to accept/reject suggestions
- Bulk apply suggestions

### US-2.4: Account Whitelist
**As a** user with essential accounts  
**I want to** whitelist accounts from deletion suggestions  
**So that** critical accounts are never accidentally queued for deletion

**Acceptance Criteria:**
- Mark accounts as "Never Delete"
- Whitelisted accounts excluded from bulk selections
- Visual indicator for whitelisted accounts
- Manage whitelist from settings

## Epic 3: Automated Deletion Process

### US-3.1: Web Scraping Deletion
**As a** user wanting automated deletion  
**I want** the app to automatically log in and delete accounts  
**So that** I don't have to manually visit each website

**Acceptance Criteria:**
- Selenium/Playwright automation for supported sites
- Progress indicator during deletion
- Screenshot capture of deletion confirmation
- Fallback to email method if automation fails

### US-3.2: GDPR Email Templates
**As a** user in EU  
**I want** GDPR-compliant deletion request emails  
**So that** companies are legally obligated to delete my data

**Acceptance Criteria:**
- Language auto-detection based on service domain
- User can override language selection
- Templates include all GDPR required information
- Customizable templates per service

### US-3.3: Email Monitoring & Confirmation
**As a** user who sent deletion emails  
**I want** automatic monitoring of email responses  
**So that** I know when deletions are confirmed

**Acceptance Criteria:**
- IMAP monitoring for deletion confirmations
- Auto-detect confirmation links in emails
- Parse and extract deletion timelines
- Update account status based on email responses

### US-3.4: Deletion Difficulty Rating
**As a** user planning deletions  
**I want to** see how difficult each service makes deletion  
**So that** I can prioritize easy deletions or prepare for difficult ones

**Acceptance Criteria:**
- Difficulty score (1-5 stars) per service
- Based on: method required, steps involved, time to complete
- Community-sourced difficulty updates
- Filter accounts by difficulty

## Epic 4: Email Integration

### US-4.1: User Email Configuration
**As a** user with email  
**I want to** configure my email for sending deletion requests  
**So that** requests come from my own email address

**Acceptance Criteria:**
- SMTP configuration (server, port, username, password)
- Support for Gmail App Passwords (no 2FA)
- Test email functionality
- Encrypted storage of email credentials

### US-4.2: Multiple Email Support
**As a** user with multiple email accounts  
**I want to** use different emails for different deletion requests  
**So that** I can organize my deletion communications

**Acceptance Criteria:**
- Add multiple email configurations
- Select which email to use per deletion batch
- Default email selection
- Email account management interface

### US-4.3: Customizable Email Templates
**As a** power user  
**I want to** customize deletion email templates  
**So that** I can adjust tone and content as needed

**Acceptance Criteria:**
- Edit templates per service
- Variable substitution (name, account, date)
- Preview before sending
- Reset to default template option

### US-4.4: Automatic Link Detection
**As a** user receiving deletion confirmations  
**I want** the app to detect and highlight confirmation links  
**So that** I can quickly complete the deletion process

**Acceptance Criteria:**
- Parse incoming emails for confirmation links
- Extract and display links in UI
- One-click to open confirmation links
- Mark as confirmed after clicking

## Epic 5: Batch Processing & Workflow

### US-5.1: Configurable Batch Processing
**As a** user with hundreds of accounts  
**I want to** process deletions in parallel batches  
**So that** I can delete many accounts efficiently

**Acceptance Criteria:**
- User-configurable parallelism (1-10 simultaneous)
- Queue management with priorities
- Progress tracking per batch
- Pause/resume batch processing

### US-5.2: Review & Confirm Workflow
**As a** cautious user  
**I want to** review and confirm before each deletion  
**So that** I don't accidentally delete important accounts

**Acceptance Criteria:**
- Optional review step before processing
- Show account details and deletion method
- Batch approval or individual approval
- Skip review option for trusted deletions

### US-5.3: Dry Run Mode
**As a** user wanting to test  
**I want** a dry run mode  
**So that** I can see what would happen without actually deleting

**Acceptance Criteria:**
- Toggle dry run mode in settings
- Simulates entire process without executing
- Shows predicted outcomes
- Generates dry run report

### US-5.4: Undo Period
**As a** user who might change my mind  
**I want** an undo period after deletion  
**So that** I can reverse deletions if needed

**Acceptance Criteria:**
- 24-hour undo window for email-based deletions
- "Undo" button for recent deletions
- Warning before undo period expires
- Permanent deletion after undo period

## Epic 6: Tracking & Reporting

### US-6.1: GDPR Compliance Reports
**As a** user needing proof of deletion requests  
**I want** compliance reports  
**So that** I have documentation for legal purposes

**Acceptance Criteria:**
- Generate GDPR compliance reports
- Include: request date, method, response status
- Export as PDF or CSV
- Digital signatures/timestamps

### US-6.2: Response Time Tracking
**As a** user monitoring GDPR compliance  
**I want** to track company response times  
**So that** I can identify non-compliant services

**Acceptance Criteria:**
- Track time from request to confirmation
- Flag services exceeding 30-day GDPR limit
- Response time analytics dashboard
- Export non-compliance report

### US-6.3: Success Rate Analytics
**As a** user wanting insights  
**I want** analytics on deletion success rates  
**So that** I can see which services honor deletion requests

**Acceptance Criteria:**
- Success/failure rates per service
- Trending success rates over time
- Compare services within categories
- Community-aggregated success rates

### US-6.4: Audit Trail Export
**As a** user needing records  
**I want to** export complete audit trails  
**So that** I have permanent records of all deletion activities

**Acceptance Criteria:**
- Export formats: PDF, CSV, JSON
- Include all actions and timestamps
- Filter by date range or status
- Scheduled automatic exports

## Epic 7: Security & Breach Monitoring

### US-7.1: Breach Detection Integration
**As a** security-conscious user  
**I want** integration with Have I Been Pwned  
**So that** I can prioritize deleting breached accounts

**Acceptance Criteria:**
- Check accounts against HIBP database
- Visual indicators for breached accounts
- Breach details (date, data exposed)
- Auto-prioritize breached accounts
- Support for other breach detection services

### US-7.2: Account Activity Check
**As a** user with old accounts  
**I want** to check if accounts are still active  
**So that** I don't waste time on already-deleted accounts

**Acceptance Criteria:**
- Verify account existence before deletion
- Check last activity if available
- Mark inactive/deleted accounts
- Skip already-deleted accounts

### US-7.3: LLM-Assisted Navigation
**As a** user facing complex deletion processes  
**I want** AI assistance navigating difficult deletions  
**So that** I can complete deletions that require multiple steps

**Acceptance Criteria:**
- LLM analyzes deletion process
- Step-by-step guidance generation
- Handle dynamic page changes
- Fallback to manual if LLM fails

## Epic 8: Job Management & Monitoring

### US-8.1: Real-time Status Updates
**As a** user running deletions  
**I want** real-time status updates  
**So that** I know exactly what's happening

**Acceptance Criteria:**
- Live status per account/job
- Detailed logs per deletion attempt
- WebSocket/SSE for real-time updates
- Color-coded status indicators

### US-8.2: Automatic Retry Logic
**As a** user experiencing failures  
**I want** automatic retries for failed deletions  
**So that** temporary issues don't require manual intervention

**Acceptance Criteria:**
- User-configurable retry count (1-5)
- Exponential backoff between retries
- Different strategies for different failure types
- Manual retry option after auto-retries exhausted

### US-8.3: CAPTCHA Handling
**As a** user facing CAPTCHAs  
**I want** the app to handle CAPTCHAs  
**So that** automated deletion can continue

**Acceptance Criteria:**
- Detect CAPTCHA presence
- Integration with CAPTCHA solving service
- Manual CAPTCHA solving fallback
- Skip if CAPTCHA unsolvable

## Epic 9: Data Retention & Privacy

### US-9.1: Credential Retention Policy
**As a** user concerned about security  
**I want** deleted credentials retained for only 30 days  
**So that** I can recover if needed but minimize exposure

**Acceptance Criteria:**
- Soft delete with 30-day retention
- Automatic purge after 30 days
- Manual purge option
- Recovery within retention period

### US-9.2: Permanent Audit Logs
**As a** user needing long-term records  
**I want** audit logs retained forever  
**So that** I always have proof of deletion requests

**Acceptance Criteria:**
- Audit logs never deleted
- Efficient storage for long-term retention
- Search and filter historical logs
- Archive old logs to reduce database size

## Epic 10: User Authentication

### US-10.1: Single User Authentication
**As a** user of DataWipe  
**I want** simple login with username and password  
**So that** my deletion data is protected

**Acceptance Criteria:**
- Secure login/logout functionality
- Password reset via email
- Session management
- Account lockout after failed attempts

---

## Priority Matrix

### P0 - Critical (MVP)
- US-1.1: Multi-Format CSV Import
- US-1.4: Secure Password Storage
- US-3.1: Web Scraping Deletion
- US-3.2: GDPR Email Templates
- US-4.1: User Email Configuration
- US-5.1: Configurable Batch Processing
- US-8.1: Real-time Status Updates
- US-10.1: Single User Authentication

### P1 - High Priority
- US-1.2: Duplicate Account Management
- US-1.3: Manual Account Entry
- US-2.1: Automatic Account Categorization
- US-3.3: Email Monitoring & Confirmation
- US-5.2: Review & Confirm Workflow
- US-6.1: GDPR Compliance Reports
- US-8.2: Automatic Retry Logic

### P2 - Medium Priority
- US-2.2: Risk Assessment & Prioritization
- US-2.3: Smart Deletion Suggestions
- US-2.4: Account Whitelist
- US-3.4: Deletion Difficulty Rating
- US-4.2: Multiple Email Support
- US-4.3: Customizable Email Templates
- US-4.4: Automatic Link Detection
- US-5.3: Dry Run Mode
- US-5.4: Undo Period
- US-6.2: Response Time Tracking
- US-6.3: Success Rate Analytics
- US-6.4: Audit Trail Export
- US-7.1: Breach Detection Integration
- US-7.2: Account Activity Check

### P3 - Low Priority
- US-7.3: LLM-Assisted Navigation
- US-8.3: CAPTCHA Handling
- US-9.1: Credential Retention Policy
- US-9.2: Permanent Audit Logs