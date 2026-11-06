Aedrova — Complete Settings Structure
I would design Aedrova with two distinct settings environments:
1. Personal Settings: Controls belonging to an individual user, regardless of which workspace they are using.
2. Workspace Settings: Controls belonging to the entire team, including members, Spaces, AI configuration, Buds, integrations, credits, and security.
There should also be a third, more focused layer: Space Settings. Workspace settings govern the organization; Space settings govern a specific project environment within it.

This separation is important. A user shouldn't have to navigate through team administration to change their personal appearance preferences, and a workspace administrator shouldn't have to configure every Space individually to manage team-wide defaults.

1. Personal Settings
Location: User avatar in the bottom-left corner → Settings.

Personal Settings should be accessible from anywhere in Aedrova and should never change the configuration for other workspace members.
Recommended sidebar
Settings

ACCOUNT
 Profile

 Login & Security

 Connected Accounts


PREFERENCES
 Appearance

 Notifications

 Language & Region

 Accessibility & Shortcuts


AI PREFERENCES
 AI Preferences

 Personal Instructions


PRIVACY
 Privacy & Data


SUPPORT
 Help & Support

 About Aedrova


A. Account
1. Profile
Everything associated with the user's identity.
- Profile picture/avatar.
- Full name.
- Display name.
- Username.
- Email address.
- Job title or role.
- Short personal bio.
- Account creation date.
- Current workspace.
- Default workspace selection.
- Change email address.
- Change password, when applicable.
- Delete account.
Design consideration: Keep this minimal. Aedrova is a collaborative workspace, so the profile should primarily establish who someone is to their teammates.
2. Login & Security
- Login methods:
  - Google.
  - Email and password.
  - Other supported authentication providers.
- Change password.
- Enable two-factor authentication.
- View recovery codes.
- Manage verified email addresses.
- Active sessions and devices.
- Last login activity.
- Sign out of individual sessions.
- Sign out of all devices.
3. Connected Accounts
This section is for accounts tied to the individual user, rather than integrations shared with the workspace.
- Connected identity providers.
- Manage sign-in connections.
- Reauthorize an expired connection.
- Disconnect an account.
- View connection status.
Shared GitHub organizations, Notion workspaces, Slack environments, and other team tools should be configured under Workspace Settings → Integrations.

B. Preferences
4. Appearance
This deserves particular attention because Aedrova's visual experience is central to the product.

Theme
- Light.
- Dark.
- System default.
Interface
- Default interface density.
- Compact or comfortable spacing.
- Sidebar behavior.
- Default workspace landing page.
- Show or hide optional interface elements.
- Animation preferences.
- Reduced motion.
Chat appearance
- Message density.
- Message grouping.
- Timestamp visibility.
- Chat text size.
- Enter-to-send behavior.
- Code block display preferences.
Editor preferences
- Font size.
- Tab size.
- Word wrapping.
- Code editor theme.
- Default editor behavior.
5. Notifications
Allow users to control what they receive and where they receive it.
Notification	Options
Direct messages	On/off
Mentions	On/off
Team activity	On/off
Agent completed a task	On/off
Agent requires approval	On/off
Build failed	On/off
Integration disconnected	On/off
Space invitations	On/off
Credit balance running low	On/off
Billing updates	On/off

Delivery preferences
- In-app notifications.
- Email notifications.
- Browser notifications, if supported.
- Notification sound.
- Daily or weekly digest.
- Quiet hours.
Workspace administrators should configure organization-wide notification defaults separately.
6. Language & Region
- Interface language.
- Time zone.
- Date format.
- Time format (12-hour or 24-hour).
- Number formatting.
- Default region.
This matters when teams collaborate across different time zones.
7. Accessibility & Shortcuts
Accessibility
- Reduced motion.
- High contrast.
- Larger text.
- Keyboard navigation support.
- Screen reader preferences.
Keyboard shortcuts
- Open search.
- Open command menu.
- Navigate between Spaces.
- Open a new chat.
- Focus the message composer.
- Mention an agent.
- Open the Bud directory.
- Toggle the sidebar.
- Open settings.
Provide a searchable shortcut list and customization where supported.

C. AI Preferences
8. AI Preferences
Personal-level AI defaults, without overriding workspace restrictions.

Default AI behavior
- Preferred response style: concise, balanced, detailed.
- Default task behavior.
- Preferred explanation depth.
- Default model preference, if permitted by workspace policy.
- Default routing preference:
  - Automatic.
  - Prioritize speed.
  - Balanced.
  - Prioritize quality.
Coding preferences
- Preferred programming languages.
- Code explanation preferences.
- Preferred coding style.
- Testing preferences.
- Code commenting preferences.
Agent behavior
- How much explanation should agents provide?
- Whether to show progress updates.
- Whether to ask before making certain changes.
9. Personal Instructions
A persistent instruction field that follows the user across their Aedrova conversations.

For example:
I prefer concise explanations. When working on code, prioritize maintainability, clear architecture, and production-ready implementations. Explain important changes before applying them.

Include:
- Personal instruction text area.
- Character limit.
- Enable/disable instructions.
- Preview of how instructions affect an agent.
- Reset to default.
This should be separate from workspace-wide AI instructions.

D. Privacy
10. Privacy & Data
- Data collection preferences.
- AI data usage information.
- Conversation and activity retention information.
- Personal data export.
- Download account information.
- Manage active sessions.
- Delete personal conversations, where supported.
- Delete account.
- View privacy policy.
- View terms of service.
Be transparent about what Aedrova stores, what connected services can access, and how data is processed by AI providers.

E. Support
11. Help & Support
- Help center.
- Getting started guide.
- Documentation.
- Contact support.
- Report a bug.
- Submit product feedback.
- Feature requests.
- Keyboard shortcuts reference.
- System status.
12. About Aedrova
- Aedrova version.
- Terms of service.
- Privacy policy.
- Licenses and acknowledgments.
- Company information.
- What's new / changelog.

2. Workspace Settings
Location: Workspace switcher → Workspace Settings.

This is where Aedrova becomes a genuinely collaborative product. Workspace settings should give founders, administrators, and team owners control over the environment their team works in.

Unlike Personal Settings, these options affect other people.
Recommended sidebar
I would divide the sidebar into five groups.

Aedrova Workspace

Workspace settings

Admin


WORKSPACE
 Overview

 General

 Members & Invitations

 Roles & Permissions

 Spaces & Subspaces


AI & BUILDING
 AI & Model Routing

 Agents

 Buds

 Knowledge & Context


CONNECTED TOOLS
 Integrations

 Developer & API


PLAN & GOVERNANCE
 Billing & Credits

 Usage & Activity

 Audit Log

 Security & Data

 Notifications


ADVANCED
 Danger Zone


The following is what each section should actually contain.

A. Workspace
1. Overview
This should be the landing page for Workspace Settings.

It should provide a quick snapshot of the entire workspace instead of making administrators open five different pages to understand its state.

Workspace information
- Workspace name.
- Workspace logo.
- Workspace owner.
- Number of members.
- Number of active Spaces.
- Number of active Buds.
- Number of connected integrations.
Plan overview
- Current team plan.
- Billing period.
- Number of seats used.
- Next renewal date.
- Workspace billing status.
Credits overview
- Credit usage across Spaces.
- Credits remaining per Space.
- Spaces approaching their limits.
- Recent credit consumption.
System status
- Connected integrations.
- Disconnected integrations.
- Active agent activity.
- Recent team activity.
- Outstanding approvals.
Quick actions
- Invite members.
- Create a Space.
- Configure an integration.
- Manage credits.
- Configure AI routing.
2. General
Basic workspace identity and organization-wide defaults.

Workspace profile
- Workspace name.
- Workspace logo/icon.
- Workspace description.
- Workspace URL/slug.
- Workspace ID.
- Creation date.
Workspace defaults
- Default language.
- Default time zone.
- Default Space template.
- Default permissions for newly created Spaces.
- Default AI configuration.
- Default notification settings.
Workspace access
- Public or private workspace, depending on supported sharing.
- Allowed email domains.
- Who can invite members.
- Who can create Spaces.
- Who can create Subspaces.
- Guest access settings.
Administrative actions
- Transfer ownership.
- Archive workspace.
- Delete workspace.
3. Members & Invitations
A full directory of everyone who belongs to the workspace.

Member directory
Field	Content
Member	Name and avatar
Email	Account email
Role	Owner, Admin, Member, Guest
Spaces	Assigned Spaces
Status	Active, Pending, Suspended
Joined	Date joined

Actions
- Invite a member by email.
- Copy invitation link.
- Resend invitation.
- Cancel invitation.
- Remove member.
- Suspend access.
- Change workspace role.
- Assign or remove Space access.
- Transfer ownership.
Invitation management
- Pending invitations.
- Expiration information.
- Invitation history.
- Default invitation role.
- Domain-based invitations, if enabled.
4. Roles & Permissions
This is important once Aedrova has teams with more than a few members.

I recommend four built-in roles initially.
Role	Intended permissions
Owner	Full workspace control
Admin	Manage workspace and team
Member	Work within assigned Spaces
Guest	Limited access to explicitly shared content

Permission categories
- Workspace management.
- Member invitations.
- Member removal.
- Role management.
- Space creation.
- Space deletion.
- Space access.
- Integration management.
- AI configuration.
- Agent management.
- Bud management.
- Credit management.
- Billing access.
- Usage reporting.
- Security configuration.
- API key management.
Eventually, allow custom roles with individual permissions.

Important: Space permissions should be independently configurable. A workspace member doesn't necessarily need access to every Space.
5. Spaces & Subspaces
One of the most important Aedrova settings sections.

This is where administrators manage the actual project environments inside a workspace.

Space directory
- All Spaces.
- Active Spaces.
- Archived Spaces.
- Private Spaces.
- Recently created Spaces.
- Space owner.
- Number of members.
- Number of Subspaces.
- Credit plan and usage.
Create a Space
- Name.
- Icon.
- Description.
- Owner.
- Initial members.
- Visibility.
- Default agents.
- Default Buds.
- Starting credit configuration.
Subspaces
- Create Subspace.
- Assign parent Space.
- Configure independent permissions.
- Configure context inheritance.
- View parent Space.
- Archive Subspace.
Space management
- Rename.
- Change icon.
- Change description.
- Manage members.
- Manage integrations.
- Configure AI behavior.
- Configure credit settings.
- Archive.
- Delete.
Important credit rule: A Space may have its own credit plan. A Subspace should use the shared credit allocation of its parent Space rather than silently creating another independent billing arrangement. Make this inheritance visible in the interface.

B. AI & Building
This is where Aedrova should differentiate itself from ordinary collaboration platforms.
6. AI & Model Routing
I would give this its own major section because optimal model routing is one of Aedrova's defining features.

Provider management
- OpenAI.
- Anthropic.
- Google Gemini.
- Other supported AI providers.
Provider configuration
- Enable/disable provider.
- Connect provider.
- Manage API credentials.
- Test connection.
- Connection status.
- Default provider.
- Provider availability.
Model routing configuration

Allow the administrator to select the workspace's routing strategy.
Routing mode	Behavior
Automatic	Aedrova selects the appropriate model
Quality-first	Prioritizes output quality
Speed-first	Prioritizes response time
Cost-efficient	Prioritizes lower operating cost
Manual	Uses administrator-defined preferences

Task-specific routing

Let Aedrova intelligently select models for different types of work:
- Brainstorming.
- Planning.
- Research.
- Coding.
- Debugging.
- Code review.
- Data analysis.
- Writing.
- Design-related tasks.
- Long-context analysis.
Fallback configuration
- Primary provider.
- Secondary provider.
- Provider failure behavior.
- Retry behavior.
- Fallback notifications.
Workspace AI policies
- Allowed models.
- Restricted models.
- Maximum task budgets.
- Usage limits.
- Data handling requirements.
- Whether members can override workspace defaults.
Routing transparency
- View which model handled a task.
- View routing reason.
- View provider failures.
- View fallback events.
- Review approximate credit consumption.
This helps users understand that Aedrova isn't simply sending every request to one model.
7. Agents
This section manages the core Aedrova AI agents, particularly the main Aedrova builder agent and coding-agent behavior.

Agent directory
- Aedrova.
- Coding agents.
- Research agents.
- Other workspace-enabled agents.
Default agent configuration
- Default agent for new Spaces.
- Default agent behavior.
- Allowed capabilities.
- Connected tools.
- Workspace instructions.
- Execution permissions.
Coding agent preferences
- Preferred execution environment.
- GitHub access.
- Repository permissions.
- Branch behavior.
- Code review settings.
- Test execution permissions.
- Commit and push permissions.
- Deployment approval requirements.
Autonomy & approval
- Which operations can run automatically?
- Which operations require approval?
- Who can approve actions?
- How agents report completed work.
- How failed tasks are handled.
Agent activity
- Running tasks.
- Completed tasks.
- Failed tasks.
- Pending approvals.
- Execution history.
The main Aedrova agent should be clearly distinguished from the Builder Bud. The main agent is the primary workspace/building assistant, while Buds are specialized AI teammates.
8. Buds
Buds need their own settings because they're a core part of Aedrova's product identity.

Bud directory

Show all available and active Buds, including:
- Builder.
- Designer.
- Marketing.
- Finance.
- Research.
- Product.
Bud configuration

For each Bud:

Identity
- Name.
- Avatar.
- Role.
- Description.
- Personality.
- Custom instructions.
Capabilities
- Available tools.
- Connected integrations.
- Permitted actions.
- Knowledge sources.
- Supported tasks.
Access
- Allowed Spaces.
- Allowed Subspaces.
- Available chat rooms.
- Access to workspace context.
- Repository or document permissions.
AI behavior
- Default model routing.
- Available models.
- Response style.
- Task limitations.
- Approval requirements.
- Autonomy level.
Budget
- Credit allocation or usage limit.
- Maximum task consumption.
- Usage alerts.
Management
- Enable/disable Bud.
- Duplicate Bud.
- Reset configuration.
- Test Bud.
- Preview behavior.
- View Bud activity.
Custom Bud creation

Eventually, provide the ability to create custom Buds with a role, description, instructions, tools, integrations, permissions, and budget.
9. Knowledge & Context
This section controls what Aedrova and its agents know about the workspace and its projects.

This is especially important because shared context is a major part of the product's value.

Context sources
- Chats.
- Meeting transcripts.
- Project documents.
- Decisions.
- Project plans.
- GitHub repositories.
- Notion pages.
- Figma files.
- Linear issues.
- Other connected sources.
Source management
- View all indexed sources.
- Add source.
- Remove source.
- Enable/disable synchronization.
- View last sync.
- View indexing status.
- Reconnect unavailable sources.
Context permissions
- Which Spaces can access a source?
- Which Buds can access it?
- Which agents can access it?
- Which members can view it?
- Should Subspaces inherit parent context?
Workspace knowledge
- Workspace description.
- Company background.
- Product information.
- Technical architecture.
- Team conventions.
- Persistent instructions.
- Important decisions.
Context maintenance
- Excluded documents.
- Archived information.
- Duplicate detection.
- Source freshness.
- Sync failures.
- Context indexing status.
Aedrova should make it clear what information an agent can access before it performs a task.

C. Connected Tools
10. Integrations
This is the central management area for all external services connected to Aedrova.

I would use a visual integration directory with categories and connection statuses.

Suggested categories
Category	Integrations
Communication	Slack, Discord
Development	GitHub
Design	Figma
Documentation	Notion
Project management	Linear
Backend	Supabase
Payments	Stripe
Analytics	PostHog
Meetings	Supported meeting/calendar providers
Marketing	Supported social and marketing platforms

Integration directory
- All integrations.
- Connected integrations.
- Available integrations.
- Disconnected integrations.
- Recently used integrations.
Each integration's settings page should include:
- Connect/disconnect.
- Authentication status.
- Account or organization connected.
- Permissions granted.
- Available workspaces, repositories, channels, or projects.
- Spaces that can access the integration.
- Buds that can use the integration.
- Sync frequency.
- Last successful sync.
- Last error.
- Reauthorize connection.
- Remove connection.
Permission management

For example, connecting GitHub shouldn't automatically grant every Bud access to every repository.

Administrators should be able to determine exactly which repositories the Builder Bud or main Aedrova agent can access.
11. Developer & API
This is useful for advanced users and future extensibility.

API keys
- Create API key.
- Name key.
- Assign permissions/scopes.
- View creation date.
- View last-used date.
- Revoke key.
Developer configuration
- API documentation.
- Webhook management.
- Webhook event subscriptions.
- Webhook delivery history.
- OAuth applications, if supported.
- Integration development documentation.
Security
- Key permissions.
- Expiration settings.
- Secret rotation.
- Usage limits.
Never display a complete secret again after its initial creation.

D. Plan & Governance
12. Billing & Credits
Because Aedrova's pricing is team-oriented, billing should make it unmistakably clear that the plan belongs to the team or the relevant Space, not an individual member.

I recommend two clearly separated areas.

A. Workspace subscription
- Current team plan.
- Monthly or annual billing.
- Subscription price.
- Billing interval.
- Number of seats.
- Seats used.
- Payment method.
- Billing contact.
- Tax information.
- Renewal date.
- Invoices.
- Upgrade/downgrade.
- Cancel subscription.
- Billing history.
B. Space credit plans

Display every Space in a table.
Space	Credit plan	Usage	Remaining
Main Project	Plan A	65%	35%
Marketing	Plan B	40%	60%
Research	Inherits parent	Shared	Shared

Each Space should allow administrators to:
- View its credit plan.
- Change its plan.
- View credit consumption.
- Set usage alerts.
- Set spending limits, if supported.
- Review recent credit activity.
For Subspaces, display the parent Space and make it clear that they share its credits.

Billing clarity is essential: Every purchase, upgrade, or credit change should identify which workspace or Space it affects before the user confirms.
13. Usage & Activity
This section should give administrators insight into how the team actually uses Aedrova.

Usage dashboard
- Total credit consumption.
- Usage by Space.
- Usage by member.
- Usage by agent.
- Usage by Bud.
- Usage by AI provider.
- Usage by model.
- Usage over time.
Task analytics
- Total tasks.
- Successful tasks.
- Failed tasks.
- Average completion time.
- Agent execution activity.
- Most-used tools.
- Integration activity.
Filters
- Date range.
- Member.
- Space.
- Agent.
- Bud.
- Model.
- Provider.
Reports
- Export usage data.
- Monthly summaries.
- Credit consumption reports.
- Provider breakdown.
- Failed task reports.
14. Audit Log
This is different from the general usage dashboard.

Usage tells you what is being used. The audit log tells you what people changed.

Record important administrative events:
- Member invited.
- Member removed.
- Role changed.
- Space created.
- Space deleted.
- Integration connected.
- Integration disconnected.
- API key created or revoked.
- AI routing configuration changed.
- Bud permissions changed.
- Credit plan changed.
- Billing changes.
- Security configuration changed.
- Data exported or deleted.
Each event should include:
- Actor.
- Action.
- Affected resource.
- Timestamp.
- Relevant details.
Only show technical metadata such as IP addresses when it is actually collected and appropriate under Aedrova's privacy practices.
15. Security & Data
Authentication
- Workspace authentication requirements.
- Two-factor authentication requirements.
- Session policies.
- Supported SSO options, when available.
Access control
- Allowed email domains.
- Guest access restrictions.
- External sharing controls.
- Integration permissions.
- API access controls.
Data management
- Data retention settings.
- Workspace export.
- Workspace deletion.
- Source removal.
- Conversation retention information.
- AI provider data-handling information.
Security information
- Encryption information.
- Security documentation.
- Data processing disclosures.
- Security incident contact.
Some of these controls, such as SSO enforcement, should be introduced when the product supports them rather than displayed as nonfunctional settings.
16. Notifications
Workspace-wide notification defaults.

Workspace events
- New members.
- Member invitations.
- New Spaces.
- Space changes.
- Integration failures.
- Agent failures.
- Pending approvals.
- Credit thresholds.
- Subscription and billing events.
Administrator notifications
- Failed payments.
- Expiring integrations.
- Low credit balances.
- Unusual usage.
- Security-related events.
Notification recipients
- Workspace owner.
- Administrators.
- Relevant Space owners.
These settings establish default notification behavior. Individual members should retain control over their own personal notification preferences.

E. Advanced
17. Danger Zone
Keep destructive operations isolated from everyday settings.

Workspace actions
- Transfer workspace ownership.
- Archive workspace.
- Delete workspace permanently.
Before deletion
- Explain what will be deleted.
- Explain what happens to Spaces and Subspaces.
- Explain what happens to members and integrations.
- Provide an export option.
- Require explicit confirmation.
- Require appropriate owner authorization.

3. Space Settings — A Separate Layer
I strongly recommend giving every Space its own settings environment rather than placing all project settings directly inside Workspace Settings.

For example, a workspace called Aedrova might contain:
Aedrova Workspace

Aedrova Main Project

Space

 Development

 Marketing

 Research


Other Project

Space



When a user opens settings for a particular Space, they should see only settings related to that project.
Recommended Space Settings sidebar
Aedrova Main Project


 Overview

 General

 Members & Access

 Agents & Buds

 Integrations

 Context & Knowledge

 AI Configuration

 Credits & Usage

 Notifications


 Archive Space

 Delete Space


1. Overview
- Space name and description.
- Space owner.
- Number of members.
- Active agents and Buds.
- Connected integrations.
- Credit balance and usage.
- Recent activity.
2. General
- Name.
- Icon.
- Description.
- Visibility.
- Parent Space, if applicable.
- Space owner.
- Default project instructions.
- Archive settings.
3. Members & Access
- Space members.
- Invite members.
- Remove members.
- Assign permissions.
- Manage guest access.
- Configure Subspace access.
- Control who can view conversations and project information.
4. Agents & Buds
- Enable/disable agents.
- Select available Buds.
- Configure Bud instructions.
- Customize agent behavior.
- Manage permissions.
- Set approval requirements.
- Restrict specific capabilities.
5. Integrations
- Enable workspace-connected integrations for this Space.
- Connect additional supported integrations.
- Select accessible repositories.
- Select relevant Slack channels.
- Select Notion pages or databases.
- Configure Linear projects.
- Manage integration permissions.
6. Context & Knowledge
- Space-specific instructions.
- Project overview.
- Technical architecture.
- Key documents.
- Meeting transcripts.
- Important decisions.
- Project chats.
- Context source access.
- Parent context inheritance.
- Excluded sources.
- Sync status.
7. AI Configuration
- Default model routing.
- Task-specific model preferences.
- Available AI providers.
- Model restrictions.
- Space-specific AI instructions.
- Task limits.
- Approval policies.
Workspace-wide restrictions should always take precedence over Space-level overrides.
8. Credits & Usage
- Current credit plan.
- Credits consumed.
- Credits remaining.
- Historical usage.
- Usage by member.
- Usage by agent.
- Usage by Bud.
- Credit alerts.
- Spending limits, if supported.
For a Subspace, show:
Credit allocation
Inherited

This Subspace shares the credit allocation of its parent Space.

Parent: Aedrova Main Project

Credit plan

Managed by parent

Usage

Included in parent usage


9. Notifications
- New Space members.
- Agent completion.
- Agent failures.
- Pending approvals.
- Credit thresholds.
- Integration failures.
- Project activity notifications.
10. Archive / Delete
- Archive Space.
- Restore archived Space.
- Delete Space.
- Handle associated Subspaces.
- Export project information.

4. How the Three Settings Layers Should Interact
This is the most important architectural distinction.
Setting	Personal	Workspace	Space
Profile	Yes	—	—
Appearance	Yes	—	—
Personal notifications	Yes	—	—
Team members	—	Yes	Access assignments
Roles	—	Yes	Space permissions
AI provider configuration	—	Yes	Restricted overrides
Model routing	Personal preference	Workspace defaults	Space overrides
Agents	—	Workspace defaults	Enabled agents
Buds	—	Bud directory and defaults	Available Buds
Integrations	Personal sign-in only	Shared connections	Integration access
Context	Personal instructions	Shared knowledge	Project knowledge
Billing	—	Team subscription	Space credit plan
Usage	Personal activity view, if offered	All workspace usage	Project usage
Security	Account security	Organization policies	Project access

The inheritance hierarchy should work like this:
1. Workspace settings establish the organization's rules.
2. Space settings customize those rules for a particular project, within the workspace's restrictions.
3. Personal settings customize the user's individual experience without overriding workspace security or access policies.
This keeps the product predictable and makes it easier to expand Aedrova without turning settings into a collection of disconnected controls.

5. Recommended Implementation Priority
Aedrova should eventually have the complete structure above, but I would not build every setting before launch. Some enterprise-level functionality can wait.
Priority	Settings to implement
P0 — Essential	Profile, Appearance, Notifications, General, Members, Roles, Spaces, Integrations, AI Routing, Buds, Context, Billing & Credits
P1 — Important	Agents, Space-level permissions, Usage, Audit Log, Personal Instructions, Developer & API, Security & Data
P2 — Later	Custom roles, advanced SSO, advanced retention policies, custom Bud marketplace, advanced analytics, enterprise controls

The first priority is making the core settings genuinely functional. A beautifully designed settings page with controls that don't actually affect the product will hurt trust.

6. My Recommended Final Sidebar Architecture
For the cleanest production-ready Aedrova experience, this is the structure I would commit to:
Personal Settings
Available to every user

Account
- Profile
- Login & Security
- Connected Accounts
Preferences
- Appearance
- Notifications
- Language & Region
- Accessibility & Shortcuts
AI
- AI Preferences
- Personal Instructions
Privacy

- Privacy & Data

Support
- Help & Support
- About Aedrova


Workspace Settings
Available to authorized workspace members

Workspace
- Overview
- General
- Members & Invitations
- Roles & Permissions
- Spaces & Subspaces
AI & Building
- AI & Model Routing
- Agents
- Buds
- Knowledge & Context
Connected Tools
- Integrations
- Developer & API
Plan & Governance
- Billing & Credits
- Usage & Activity
- Audit Log
- Security & Data
- Notifications
Advanced

- Danger Zone


Space Settings
Available to authorized Space members
- Overview
- General
- Members & Access
- Agents & Buds
- Integrations
- Context & Knowledge
- AI Configuration
- Credits & Usage
- Notifications
- Archive / Delete


My strongest recommendation: Keep these three layers separate, but make navigating between them effortless. A user should always know whether they're changing something for themselves, the entire workspace, or just one project.

For Aedrova specifically, the settings experience should revolve around four product pillars: team collaboration, shared context, intelligent agents, and workspace-level resource management. Every setting should serve one of those pillars or a necessary account/security function.