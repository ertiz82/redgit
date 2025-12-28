# Tunnel Integrations

Expose local ports to the internet for webhooks, Planning Poker, and remote access.

## Overview

Tunnel integrations allow you to expose local ports to the internet. This is useful for:

- **Webhooks** - Receive callbacks from notification services (Telegram, Slack)
- **Planning Poker** - Remote team members can join your poker session
- **Development** - Share your local server with teammates

## Available Integrations

| Integration | Description | Requirements |
|-------------|-------------|--------------|
| [ngrok](https://ngrok.com) | Popular tunnel service with free tier | ngrok binary |
| [cloudflare-tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) | Fast, uses Cloudflare's global network | cloudflared binary |
| [localtunnel](https://theboroer.github.io/localtunnel-www/) | Simple npm package, no signup | Node.js |
| [bore](https://github.com/ekzhang/bore) | Fast Rust-based tunnel | bore binary |
| [serveo](https://serveo.net) | SSH-based, no installation | SSH client |

## Quick Start

```bash
# Install a tunnel integration
rg install ngrok

# Configure it
rg integration configure ngrok

# Start a tunnel
rg tunnel start 8080

# Check status
rg tunnel status

# Stop the tunnel
rg tunnel stop
```

## Choosing a Tunnel

### ngrok (Recommended for most users)
- Pros: Easy to use, HTTPS by default, good documentation
- Cons: Free tier has session limits (2 hours)
- Best for: General use, development

### cloudflare-tunnel
- Pros: Fast, no session limits, global network
- Cons: Slightly more complex setup
- Best for: Production webhooks, performance-critical use

### localtunnel
- Pros: Free, no signup, simple
- Cons: Less reliable, may have downtime
- Best for: Quick testing

### bore
- Pros: Very fast, minimal resources, self-hostable
- Cons: TCP only (not HTTP), requires port access
- Best for: Advanced users, self-hosting

### serveo
- Pros: No installation needed (uses SSH)
- Cons: May have availability issues
- Best for: Quick access when nothing is installed

## Commands

### Start Tunnel

```bash
rg tunnel start <PORT> [OPTIONS]
  --region, -r    Server region (if supported)

# Examples
rg tunnel start 8080
rg tunnel start 3000 --region eu
```

### Stop Tunnel

```bash
rg tunnel stop
```

### Check Status

```bash
rg tunnel status

# Output:
# Running
#    Integration: ngrok
#    URL: https://abc123.ngrok.io
```

### Get URL

```bash
rg tunnel url

# Output:
# https://abc123.ngrok.io
```

## Configuration

Tunnel integrations are configured in `.redgit/config.yaml`:

```yaml
integrations:
  ngrok:
    auth_token: "your-token"  # Optional
    region: "us"              # Optional

active:
  tunnel: ngrok
```

## Integration with Other Features

### Webhooks

Tunnel integrations work with the webhook server:

```bash
# Start webhook server with tunnel
rg webhook start --ngrok

# The tunnel URL is automatically configured
```

### Planning Poker

Poker sessions automatically use the configured tunnel:

```bash
# Configure tunnel first
rg install ngrok
rg integration configure ngrok

# Start poker - tunnel is used automatically
rg poker start --sprint active
```

## API

### TunnelBase Class

All tunnel integrations extend `TunnelBase`:

```python
from redgit.integrations.base import TunnelBase, IntegrationType

class MyTunnel(TunnelBase):
    name = "my-tunnel"
    integration_type = IntegrationType.TUNNEL

    def setup(self, config: dict):
        # Configure from config
        self.enabled = True

    def start_tunnel(self, port: int, **kwargs) -> Optional[str]:
        # Start the tunnel
        # Return public URL or None
        return "https://example.com"

    def stop_tunnel(self) -> bool:
        # Stop the tunnel
        return True

    def get_public_url(self) -> Optional[str]:
        # Return current URL if running
        return self._url
```

### Registry Functions

```python
from redgit.integrations.registry import get_tunnel_integration
from redgit.core.config import ConfigManager

config = ConfigManager().load()
tunnel = get_tunnel_integration(config)

if tunnel and tunnel.enabled:
    url = tunnel.start_tunnel(8080)
    print(f"Tunnel running at: {url}")

    # Later...
    tunnel.stop_tunnel()
```

## Troubleshooting

### "No tunnel integration configured"

Install and configure a tunnel:
```bash
rg install ngrok
rg integration configure ngrok
```

### Tunnel fails to start

1. Check if the binary is installed:
   ```bash
   ngrok version
   # or
   cloudflared version
   ```

2. Check if another tunnel is running:
   ```bash
   rg tunnel stop
   ```

3. Try a different tunnel:
   ```bash
   rg install serveo  # No installation needed
   ```

### URL not accessible

1. Check firewall settings
2. Verify the local port is listening
3. Check tunnel status: `rg tunnel status`

## See Also

- [Planning Poker](./planning-poker.md)
- [Webhook Commands](./webhooks.md)
- [Tunnel Integrations on RedGit-Tap](https://github.com/ertiz82/redgit-tap#tunnel)
