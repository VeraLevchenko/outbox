# CLAUDE.md - AI Assistant Guide for Outbox Repository

**Last Updated:** 2026-01-18
**Repository:** VeraLevchenko/outbox
**Purpose:** Outgoing correspondence management system

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Current State](#current-state)
3. [Codebase Structure](#codebase-structure)
4. [Development Workflows](#development-workflows)
5. [Key Conventions](#key-conventions)
6. [AI Assistant Guidelines](#ai-assistant-guidelines)
7. [Git Workflows](#git-workflows)
8. [Future Development](#future-development)

---

## Repository Overview

### Project Name
**Outbox** (Исходящая корреспонденция - "Outgoing Correspondence" in Russian)

### Purpose
This repository is designed to manage outgoing correspondence, messages, or work items. The exact implementation is still being defined, but the name suggests it follows patterns related to:
- Outbox pattern for message/event processing
- Correspondence/document management
- Asynchronous communication systems
- Work item tracking and dispatch

### Owner
VeraLevchenko

---

## Current State

### Repository Status
- **Created:** Recently initialized
- **Commits:** 1 (Initial commit)
- **Files:** 1 (README.md)
- **Size:** Minimal - just starting out
- **Language:** Not yet determined
- **Framework:** Not yet determined

### Existing Files
```
outbox/
├── README.md          # Project description (Russian + English)
└── CLAUDE.md         # This file - AI assistant documentation
```

### Git Information
- **Main Branch:** Not yet established
- **Current Branch:** claude/claude-md-mkj4014ur9ehovkd-PgtLr
- **Remote:** http://127.0.0.1:56858/git/VeraLevchenko/outbox
- **Branch Naming Convention:** `claude/claude-md-<session-id>`

---

## Codebase Structure

### Current Structure
The repository is in its initial state with minimal structure.

### Recommended Future Structure

Based on the "outbox" concept, here are potential structures depending on the implementation:

#### Option 1: Microservice/Backend Service
```
outbox/
├── src/
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   ├── repositories/   # Data access layer
│   ├── controllers/    # API controllers
│   └── utils/          # Utility functions
├── tests/
│   ├── unit/
│   └── integration/
├── config/             # Configuration files
├── docs/               # Documentation
├── package.json        # Dependencies (if Node.js)
├── requirements.txt    # Dependencies (if Python)
└── README.md
```

#### Option 2: Library/Package
```
outbox/
├── lib/                # Core library code
├── examples/           # Usage examples
├── tests/              # Test suite
├── docs/               # Documentation
└── README.md
```

#### Option 3: Application
```
outbox/
├── frontend/           # UI layer
├── backend/            # API/server
├── shared/             # Shared types/utilities
├── docs/               # Documentation
└── README.md
```

---

## Development Workflows

### Setting Up Development Environment

1. **Clone the repository**
   ```bash
   git clone http://127.0.0.1:56858/git/VeraLevchenko/outbox
   cd outbox
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b claude/claude-md-<session-id>
   ```

3. **Install dependencies** (when applicable)
   - Node.js: `npm install` or `yarn install`
   - Python: `pip install -r requirements.txt`
   - Other: Follow language-specific conventions

### Making Changes

1. **Always read before modifying**
   - Use Read tool to understand existing code
   - Never propose changes without reading the file first

2. **Keep changes focused**
   - Address the specific request
   - Avoid over-engineering
   - Don't add unrequested features

3. **Test your changes**
   - Run existing tests
   - Add tests for new functionality
   - Verify nothing breaks

### Code Quality Standards

1. **Security First**
   - Avoid OWASP Top 10 vulnerabilities
   - No command injection, XSS, SQL injection
   - Validate all external inputs
   - Sanitize user data

2. **Simplicity**
   - Minimum viable complexity
   - Clear, readable code over clever solutions
   - No premature abstractions
   - Delete unused code completely

3. **Documentation**
   - Code should be self-documenting
   - Add comments only when logic is non-obvious
   - Keep README.md updated
   - Document public APIs

---

## Key Conventions

### File Naming
- **To be established** based on chosen language/framework
- Generally prefer:
  - Lowercase with hyphens: `user-service.js`
  - Or camelCase: `userService.js`
  - Or snake_case: `user_service.py`
- Be consistent within the codebase

### Code Style
- **To be established** based on chosen language
- Common guidelines:
  - Use language standard formatters (Prettier, Black, gofmt, etc.)
  - Follow community style guides
  - Configure linters early
  - Add .editorconfig for consistency

### Error Handling
- Fail fast with clear error messages
- Only catch errors you can handle
- Don't swallow exceptions
- Log appropriately for debugging
- Validate at system boundaries

### Testing
- Write tests for new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Test edge cases and error conditions

---

## AI Assistant Guidelines

### General Principles

1. **Read First, Modify Second**
   - Always read files before suggesting changes
   - Understand context before acting
   - Don't make assumptions about code structure

2. **Communicate Clearly**
   - Use direct text output to communicate
   - Don't use bash echo or comments to talk to users
   - Reference code with `file_path:line_number` format
   - Be concise but complete

3. **Use Tools Efficiently**
   - Prefer specialized tools over bash commands
   - Use Read/Edit/Write for file operations
   - Use Grep/Glob for searching
   - Run independent operations in parallel
   - Use Task tool for complex multi-step operations

4. **Track Progress**
   - Use TodoWrite for multi-step tasks
   - Mark todos as in_progress when starting
   - Mark todos as completed immediately when done
   - Keep only one todo in_progress at a time

### Specific Guidelines for This Repository

1. **Understand the Domain**
   - This is an "outbox" system for outgoing correspondence
   - May involve message queuing, event sourcing, or document management
   - Clarify requirements before implementing features

2. **Maintain Simplicity**
   - Start with minimal viable implementation
   - Add complexity only when needed
   - Avoid over-engineering early on

3. **Security Considerations**
   - If handling messages/correspondence, consider:
     - Data privacy and encryption
     - Access control and authentication
     - Audit logging
     - Data retention policies

4. **Performance Considerations**
   - If building a queue/outbox system, consider:
     - Scalability requirements
     - Message ordering guarantees
     - Retry mechanisms
     - Dead letter handling

### Common Tasks

#### Adding a New Feature
```
1. Read and understand existing code
2. Use TodoWrite to plan implementation steps
3. Ask clarifying questions if needed
4. Implement changes incrementally
5. Test functionality
6. Update documentation
7. Commit with clear message
8. Push to feature branch
```

#### Fixing a Bug
```
1. Reproduce the issue
2. Read relevant code sections
3. Identify root cause
4. Implement minimal fix
5. Test the fix
6. Verify no regressions
7. Commit and push
```

#### Answering Questions
```
1. Use Explore agent for codebase investigation
2. Read relevant files
3. Provide specific references (file:line)
4. Give clear, accurate answers
5. Avoid speculation
```

---

## Git Workflows

### Branch Naming Convention

All Claude Code branches must follow this pattern:
```
claude/claude-md-<session-id>
```

**Critical:** The branch must start with `claude/` and end with the session ID, otherwise push will fail with 403 error.

### Creating a Feature Branch

```bash
# Branch should already exist from session setup
git checkout claude/claude-md-<session-id>
```

### Committing Changes

1. **Stage relevant files only**
   ```bash
   git add <specific-files>
   ```

2. **Write clear commit messages**
   ```bash
   git commit -m "$(cat <<'EOF'
   Brief summary of changes (50 chars or less)

   More detailed explanation if needed:
   - What changed and why
   - Any important context
   - Related issues or tickets
   EOF
   )"
   ```

3. **Follow commit message best practices**
   - Use imperative mood: "Add feature" not "Added feature"
   - Focus on the "why" not the "what"
   - Keep first line under 50 characters
   - Reference issues/tickets when applicable

### Pushing Changes

**Always use the -u flag with branch name:**
```bash
git push -u origin claude/claude-md-<session-id>
```

**Retry Logic for Network Issues:**
- If push fails due to network errors, retry up to 4 times
- Use exponential backoff: 2s, 4s, 8s, 16s
- Only retry on network errors, not auth failures

### Git Safety Protocols

**NEVER do these without explicit permission:**
- Update git config
- Force push (--force, --force-with-lease)
- Amend pushed commits
- Hard reset
- Push to main/master
- Skip hooks (--no-verify, --no-gpg-sign)

**ONLY amend commits when ALL conditions are met:**
1. User explicitly requested amend, OR pre-commit hook auto-modified files
2. HEAD commit was created by you in this conversation
3. Commit has NOT been pushed to remote

### Creating Pull Requests

1. **Ensure all changes are committed and pushed**
2. **Analyze full commit history**
   ```bash
   git log main..HEAD  # or appropriate base branch
   git diff main...HEAD
   ```
3. **Create PR with gh CLI**
   ```bash
   gh pr create --title "Descriptive title" --body "$(cat <<'EOF'
   ## Summary
   - Bullet point 1
   - Bullet point 2

   ## Test plan
   - [ ] Test item 1
   - [ ] Test item 2
   EOF
   )"
   ```

---

## Future Development

### Potential Features to Implement

Based on the "outbox" concept, consider:

1. **Core Outbox Functionality**
   - Message/event storage
   - Retry mechanisms
   - Status tracking (pending, sent, failed)
   - Delivery confirmation

2. **API Layer**
   - RESTful or GraphQL API
   - Webhook support
   - Batch operations
   - Query/filter capabilities

3. **Persistence**
   - Database integration
   - Message serialization
   - Transaction support
   - Data migration tools

4. **Monitoring & Observability**
   - Logging
   - Metrics collection
   - Health checks
   - Alerting

5. **Integration**
   - Email providers
   - Message queues (RabbitMQ, Kafka, etc.)
   - Notification services
   - Third-party APIs

### Technology Stack Decisions

When choosing technologies, consider:

**Language Options:**
- **Node.js/TypeScript**: Great for async I/O, large ecosystem
- **Python**: Excellent libraries, readable, versatile
- **Go**: High performance, great concurrency, simple deployment
- **Java/Kotlin**: Enterprise-ready, robust ecosystem

**Database Options:**
- **PostgreSQL**: Robust, ACID compliant, good for transactional outbox
- **MongoDB**: Flexible schema, good for document storage
- **Redis**: Fast, good for caching and simple queues
- **SQLite**: Simple, serverless, good for small-scale

**Framework Options:**
- **Node.js**: Express, Fastify, NestJS
- **Python**: Flask, FastAPI, Django
- **Go**: Gin, Echo, Chi

### Architecture Patterns

Consider these patterns for the outbox:

1. **Transactional Outbox Pattern**
   - Store messages in DB with business data
   - Ensure atomicity with transactions
   - Separate process publishes messages
   - Guarantees at-least-once delivery

2. **Event Sourcing**
   - Store all changes as events
   - Rebuild state from event log
   - Audit trail built-in

3. **Message Queue Integration**
   - Direct integration with MQ systems
   - Reliable delivery guarantees
   - Scaling and load balancing

---

## Questions for Future Clarification

When implementing features, clarify:

1. **What type of messages/correspondence?**
   - Emails, events, documents, API calls?

2. **What are the delivery guarantees?**
   - At-most-once, at-least-once, exactly-once?

3. **What is the expected scale?**
   - Messages per second/day?
   - Storage requirements?

4. **What are the integration requirements?**
   - External systems to integrate with?
   - API requirements?

5. **What are the security requirements?**
   - Authentication/authorization?
   - Encryption needs?
   - Compliance requirements?

---

## Additional Resources

### Outbox Pattern
- [Microservices.io - Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- [Martin Fowler - Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)

### Best Practices
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [The Twelve-Factor App](https://12factor.net/)
- [Semantic Versioning](https://semver.org/)

### Git
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://git-scm.com/book/en/v2)

---

## Changelog

### 2026-01-18
- Initial CLAUDE.md created
- Repository analyzed and documented
- Development workflows established
- AI assistant guidelines defined

---

## Notes for AI Assistants

**Remember:**
- This repository is in its early stages
- Be prepared to adapt to technology decisions made by the owner
- Always ask for clarification when requirements are ambiguous
- Maintain this document as the codebase evolves
- Update the Changelog section when making significant changes
- Reference specific code locations with `file:line` format
- Keep solutions simple and focused on actual requirements

**When in doubt:**
1. Ask questions using AskUserQuestion tool
2. Read existing code before making changes
3. Choose the simplest solution that works
4. Document your decisions
5. Test thoroughly

---

*This document is maintained by AI assistants working on this repository. Keep it updated as the codebase evolves.*
