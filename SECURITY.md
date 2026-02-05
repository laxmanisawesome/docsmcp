# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

- Open a public GitHub issue
- Post about it on social media
- Disclose details publicly before a fix is available

### Do

1. **Email**: Send details to [security@yourdomain.com]
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. **Wait**: We'll acknowledge receipt within 48 hours
4. **Coordinate**: Work with us on disclosure timeline

## Security Considerations

### Self-Hosting Risks

DocsMCP is designed for local or private network use. If you expose it to the public internet:

1. **No built-in authentication**: The dashboard and API are open by default
2. **Scraping capabilities**: Could be abused if exposed
3. **Data exposure**: Scraped content is accessible via API

### Recommended Mitigations

If you must expose DocsMCP publicly:

```bash
# Use nginx with basic auth
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8090;
}
```

Or use a VPN/Tailscale for access.

### Web Scraping Legal Notice

⚠️ **Important**: Web scraping may violate:

- Website Terms of Service
- Copyright laws
- CFAA (in the US)
- GDPR (in the EU)

**You are responsible for**:
- Checking robots.txt (we respect it by default)
- Reviewing target site's ToS
- Ensuring compliance with local laws
- Using scraped content appropriately

DocsMCP is a tool. How you use it is your responsibility.

## Security Features

### Current

- Input validation on all endpoints
- Path traversal protection
- Rate limiting ready (via nginx)
- Non-root Docker container
- Minimal dependencies

### Planned

- [ ] Optional basic authentication
- [ ] API key support
- [ ] Audit logging
- [ ] IP allowlisting

## Dependency Security

We regularly update dependencies. To check for vulnerabilities:

```bash
pip install safety
safety check -r requirements.txt
```

## Acknowledgments

We thank security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged (with permission) in release notes.
