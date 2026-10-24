Secrets and process management for running btc-agent on an EC2 instance, so API keys never go
into git and never need retyping if the instance is replaced.

How it fits together: the keys live in SSM Parameter Store, not on the instance or in this repo.
`btc-agent-secrets.service` runs `fetch_secrets.sh` on every boot to pull them down into
`/etc/btc-agent/env` (root:btc-agent, mode 640), and `btc-agent.service` loads that file as its
environment before starting `timer.py`. A terminated-and-replaced instance just needs the same
IAM role attached and it re-fetches the current keys on its own.

## One-time setup (do this yourself -- it needs your real AWS credentials and real key values)

1. Store each key in Parameter Store as a `SecureString` (replace the example values):
   ```bash
   aws ssm put-parameter --name /btc-agent/OPENAI_API_KEY      --type SecureString --value "sk-..."
   aws ssm put-parameter --name /btc-agent/TELEGRAM_BOT_TOKEN  --type SecureString --value "..."
   aws ssm put-parameter --name /btc-agent/MAILTRAP_API_TOKEN --type SecureString --value "..."
   aws ssm put-parameter --name /btc-agent/NEWS_API_KEY        --type SecureString --value "..."
   ```
   (`google_sheets.py` isn't wired into the app yet -- add `/btc-agent/GOOGLE_CREDENTIALS_BASE64`
   the same way if/when it is. `STARTING_CASH_BALANCE` isn't a secret; it's fine left as the
   default in `src/agent.py`, or added here too as a plain `String` for consistency.)

2. Create an IAM role for the instance using `iam-policy.json` in this directory, and attach it as
   the instance's IAM instance profile (EC2 console: Actions -> Security -> Modify IAM role, or set
   it at launch time). No access keys are stored anywhere -- the role is what grants access.

3. On the instance: create the system user the service runs as, and deploy the code:
   ```bash
   sudo useradd --system --home-dir /opt/btc-agent --shell /usr/sbin/nologin btc-agent
   sudo mkdir -p /opt/btc-agent
   # ... deploy the repo's btc_agent/ contents into /opt/btc-agent, create .venv, pip install ...
   sudo chown -R btc-agent:btc-agent /opt/btc-agent
   ```

4. Install and enable the systemd units:
   ```bash
   sudo cp deploy/btc-agent-secrets.service deploy/btc-agent.service /etc/systemd/system/
   sudo chmod +x /opt/btc-agent/deploy/fetch_secrets.sh
   sudo systemctl daemon-reload
   sudo systemctl enable --now btc-agent-secrets.service btc-agent.service
   ```

From here on, `systemctl status btc-agent` shows whether it's running, `journalctl -u btc-agent -f`
tails its logs, and a reboot or a replacement instance (same IAM role attached) re-fetches secrets
and starts trading on its own.
