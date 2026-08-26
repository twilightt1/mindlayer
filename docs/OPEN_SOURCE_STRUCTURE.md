# Orivory — Open Source Repository Structure

## Overview

This document describes the repository structure for Orivory open source project.

## Public Repository

```
orivory/
├── README.md                    ✅ Public - Landing page
├── CONTRIBUTING.md              ✅ Public - Developer guide
├── SECURITY.md                  ✅ Public - Security policy
├── LICENSE                      ✅ Public - MIT License
├── CHANGELOG.md                 ✅ Public - Version history
│
├── docs/                        ✅ Public - Essential docs
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── API.md
│   ├── LOCAL_RUN_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── BACKUP_RESTORE.md
│   ├── OPERATIONS_RUNBOOK.md
│   ├── RAG_TECHNIQUES.md
│   └── EVALUATION_GUIDE.md
│
├── app/                        ✅ Public - Source code
├── frontend/                   ✅ Public - Web app
├── tests/                     ✅ Public - Test suite
└── scripts/                   ✅ Public - Utilities
```

## Internal/Private Documentation

The following should be kept **private** or removed:

```
PRIVATE (keep offline or private repo):
├── orivory-security-trust-guide.md    ❌ Internal security
├── POSITIONING.md                     ❌ Marketing strategy
├── PRD.md                             ❌ Product requirements
├── PORTFOLIO.md                       ❌ Portfolio presentation
├── orivory-product-roadmap-2025.md   ❌ Internal roadmap
├── orivory-feedback-loop-process.md  ❌ Internal process
└── docs/
    ├── SECURITY_EVIDENCE.md          ❌ Audit evidence
    ├── SECURITY_CHECKLIST.md         ❌ Internal checklist
    └── DEMO_EVIDENCE.md              ❌ Demo scripts
```

## Before Publishing

### 1. Clean Up Repository

```bash
# Remove sensitive files
Remove-Item -Path "POSITIONING.md"
Remove-Item -Path "PRD.md"
Remove-Item -Path "PORTFOLIO.md"
Remove-Item -Path "orivory-*.md"
Remove-Item -Path "REBRAND_NOTES.md"

# Remove from docs/
Remove-Item -Path "docs/SECURITY_EVIDENCE.md"
Remove-Item -Path "docs/SECURITY_CHECKLIST.md"
Remove-Item -Path "docs/DEMO_EVIDENCE.md"
```

### 2. Update URLs

```bash
# Update all references to match new repo name
# Replace "mindlayer" with "orivory" in all files
```

### 3. Create GitHub Release

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Next Steps

1. [ ] Remove sensitive files listed above
2. [ ] Verify all URLs point to correct repository
3. [ ] Update .env.example with public-friendly defaults
4. [ ] Create v1.0.0 release on GitHub
5. [ ] Announce to community
