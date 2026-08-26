# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Currently Active |

---

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Send a detailed report to the maintainers via:
   - GitHub [Security Advisories](https://github.com/twilightt1/orivory/security/advisories/new)
   - Or contact directly (if known)

3. Include in your report:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

4. We will:
   - Acknowledge receipt within 48 hours
   - Provide an estimated timeline for a fix
   - Credit you in the release notes (if desired)

---

## Security Best Practices

When deploying Orivory:

### 🔐 Authentication
- Use strong JWT secrets (min 32 characters)
- Enable HTTPS in production
- Rotate secrets regularly

### 🗄️ Database
- Use strong PostgreSQL passwords
- Enable SSL connections
- Regular backups

### 🔧 Configuration
- Never commit `.env` files
- Use environment variables for secrets
- Review CORS settings for production

### 🐳 Docker
- Run as non-root user
- Keep images updated
- Use read-only containers where possible

---

## Known Limitations

- Self-hosted deployments are responsible for their own security configuration
- API rate limiting should be configured at the infrastructure level
- Regular security audits are recommended

---

Thank you for helping keep Orivory secure! 🔒
