# Security Policy

## Supported Versions

| Version | Status | Released |
|--------|--------|----------|
| 1.x.x | ✅ Active | 2025 |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability, please report it **responsibly**:

1. **DO NOT** open a public GitHub issue
2. Report via [GitHub Security Advisories](https://github.com/twilightt1/orivory/security/advisories/new)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

### Response Timeline

- ✅ Acknowledge within 48 hours
- ✅ Provide fix timeline
- ✅ Credit in release notes (if desired)

---

## 🔒 Security Best Practices

When deploying Orivory:

### Authentication
- Use strong JWT secrets (min 32 characters)
- Enable HTTPS in production
- Rotate secrets regularly

### Database
- Use strong PostgreSQL passwords
- Enable SSL connections
- Regular backups

### Configuration
- Never commit `.env` files
- Use environment variables for secrets
- Review CORS settings for production

### Docker
- Run as non-root user
- Keep images updated
- Use read-only containers where possible

---

## ⚠️ Known Limitations

- Self-hosted deployments are responsible for their own security configuration
- API rate limiting should be configured at the infrastructure level
- Regular security audits are recommended

---

## 🔐 Security Features

| Feature | Status |
|---------|--------|
| JWT Authentication | ✅ |
| Refresh Token Hashing | ✅ |
| Rate Limiting | ✅ |
| HTTPS Enforcement | ✅ |
| CORS Protection | ✅ |
| Input Validation | ✅ |

---

Thank you for helping keep Orivory secure! 🔒
