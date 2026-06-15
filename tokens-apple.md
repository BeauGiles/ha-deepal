## Getting your tokens

Tokens are obtained by intercepting the Deepal app's network traffic using a proxy tool. The easiest option is **mitmproxy**, which is free and open source.

See the instructions below for macOS and an iPhone (or iPad)

### Step 1 — Install mitmproxy

Download and install mitmproxy from [mitmproxy.org](https://mitmproxy.org).

On macOS you can also use Homebrew from the Terminal:

```bash
brew install mitmproxy
```

### Step 2 — Start mitmweb

mitmweb gives you a browser-based interface to view captured traffic:

on macOS, open the Terminal app:

```bash
mitmweb
```

This starts the proxy on port `8080` and opens a web interface at `http://127.0.0.1:8081`.

### Step 3 — Configure your iPhone to use the proxy

1. On your Mac, find your local IP address (System Settings → Wi-Fi → your network → details)
2. On your iPhone, go to **Settings → Wi-Fi → tap your network → Configure Proxy**
3. Select **Manual** and enter:
   - Server: your Mac's IP address (e.g. `192.168.1.100`)
   - Port: `8080`
4. Tap Save

### Step 4 — Install the mitmproxy certificate on your iPhone

1. On your iPhone, open Safari and go to `http://mitm.it`
2. Tap **Apple** and follow the prompts to download the profile
3. Go to **Settings → General → VPN & Device Management** and install the downloaded profile
4. Go to **Settings → General → About → Certificate Trust Settings** and enable full trust for the mitmproxy certificate

### Step 5 — Capture the login request

1. Fully log out of the Deepal app on your iPhone
2. Open the Deepal app and log in with your email and password
3. In mitmweb (at `http://127.0.0.1:8081` on your Mac), look for a request to: https://m.iov.changanauto.sg/appgw/intl-app-auth/api/login/email-pass-in
<img width="1608" height="265" alt="requests" src="https://github.com/user-attachments/assets/6755d548-a66a-42ca-b3a9-dcad971bf674" />

4. Click that request and select the **Response** tab
5. In the JSON response, copy the values for:
   - `token` — starts with `Bearer eyJ...`
   - `refreshToken` — starts with `Bearer eyJ...`


<img width="1597" height="930" alt="token" src="https://github.com/user-attachments/assets/b7c8d94f-5875-4030-957b-597a63cd175e" />


### Step 6 — Clean up

Once you have your tokens, remove the proxy configuration from your iPhone (Settings → Wi-Fi → your network → Configure Proxy → Off) so your normal internet traffic is not routed through the proxy.

### Step 7 — Enter tokens in Home Assistant

When adding the Deepal integration in Home Assistant, paste the full `token` and `refreshToken` values including the `Bearer ` prefix. The integration will automatically strip or add the prefix if needed.

> **Note:** Tokens expire after approximately 1 hour but are automatically refreshed by the integration. The refresh token is valid for ~90 days.
> If your tokens are ever invalidated (e.g. you log in on another device), a repair notification will appear in Home Assistant prompting you to capture and paste fresh tokens.
