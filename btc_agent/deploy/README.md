# Deploying btc-agent on EC2

Secrets and process management for running btc-agent on an EC2 instance, so API keys never go into git and never need
retyping if the instance is replaced.

## How it fits together

The API keys live in **SSM Parameter Store** (free for these keys), not on the instance or in this repo. Three systemd
units do the rest:

| Unit | Runs as | What it does |
|---|---|---|
| `btc-agent-secrets.service` | root | On every boot, runs `fetch_secrets.sh` to pull the keys into `/etc/btc-agent/env` (owner `root:btc-agent`, mode 640). |
| `btc-agent.service` | `btc-agent` | Loads that file as its environment and runs `timer.py`, which runs `main.py` (the agent) at the start of every hour. |
| `btc-agent-app.service` | `btc-agent` | Loads the same file and runs the Streamlit frontend (`app.py`) on port 8501. |

Both app units require the secrets unit, so they only start once the keys have been fetched. A terminated-and-replaced
instance just needs the same IAM role attached, and it re-fetches the current keys on its own.

The repo is cloned to `/opt/btc-agent`, so the paths used throughout are:

```
/opt/btc-agent/                  # the git clone (repo root), owned by root
├── .venv/                       # Python virtual environment, owned by root
└── btc_agent/                   # the app: working directory for both app units
    ├── databases/trading.db     # writable by btc-agent; created on the first run
    ├── logs/btc_agent.log       # writable by btc-agent; created on the first run
    └── deploy/                  # this folder
/var/lib/btc-agent/              # the btc-agent user's home (Streamlit and Keras cache files)
```

The code is owned by root and the `btc-agent` user can only write `databases/` and `logs/`, so the running agent can't
modify its own code, and `git pull` always runs as root.

## Before you start

- **Instance size:** at least 2 GB of RAM (e.g. `t3.small`). TensorFlow and Streamlit together don't fit in 1 GB.
- **Python 3.10 or newer** (3.12 matches development). Amazon Linux 2023's default `python3` is 3.9, which is too old:
  install `python3.12` with `sudo dnf install -y python3.12`. Ubuntu 24.04's default `python3` is already 3.12.
- **Git and the AWS CLI:** Amazon Linux 2023 includes the AWS CLI; on Ubuntu install it first
  (see the [AWS CLI install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)).
- **Repo access:** if the GitHub repo is private, the instance needs a deploy key or token to clone and pull it.

## One-time setup in AWS (do this yourself: it needs your real AWS credentials and real key values)

1. **Store each key in Parameter Store** as a `SecureString`, in the same region as the instance (replace the example values):
   ```bash
   aws ssm put-parameter --name /btc-agent/OPENAI_API_KEY     --type SecureString --value "sk-..."
   aws ssm put-parameter --name /btc-agent/TELEGRAM_BOT_TOKEN --type SecureString --value "..."
   aws ssm put-parameter --name /btc-agent/MAILTRAP_API_TOKEN --type SecureString --value "..."
   aws ssm put-parameter --name /btc-agent/NEWS_API_KEY       --type SecureString --value "..."
   ```
   Names must be directly under `/btc-agent/` and be valid environment variable names (letters, digits and underscores);
   anything else is skipped. `STARTING_CASH_BALANCE` isn't a secret: it defaults to 10000 in `src/agent.py`, or add it as a
   plain `String` parameter to change it. `google_sheets.py` isn't wired into the app yet; add
   `/btc-agent/GOOGLE_CREDENTIALS_BASE64` the same way if and when it is.

2. **Create an IAM role** for EC2 with the policy in `iam-policy.json`, and attach it to the instance (EC2 console:
   Actions -> Security -> Modify IAM role, or set it at launch). No access keys are stored anywhere; the role grants access.

3. **Security group:** allow inbound SSH (22) and Streamlit (8501) **from your own IP only**. Streamlit has no login, so
   anyone who can reach port 8501 can see the portfolio.

## One-time setup on the instance

4. **Create the service user, clone the repo, and install the dependencies:**
   ```bash
   sudo useradd --system --create-home --home-dir /var/lib/btc-agent --shell /usr/sbin/nologin btc-agent
   sudo git clone <your-repo-url> /opt/btc-agent
   sudo python3.12 -m venv /opt/btc-agent/.venv   # or python3 on Ubuntu 24.04
   sudo /opt/btc-agent/.venv/bin/pip install -r /opt/btc-agent/btc_agent/requirements.txt
   # The only places the services write to:
   sudo install -d -o btc-agent -g btc-agent /opt/btc-agent/btc_agent/databases /opt/btc-agent/btc_agent/logs
   ```

5. **Install the secrets script** to a fixed location outside the repo, so the secrets unit doesn't depend on where the
   repo is cloned, and only changes when you deliberately reinstall it:
   ```bash
   sudo install -o root -g root -m 755 /opt/btc-agent/btc_agent/deploy/fetch_secrets.sh /usr/local/sbin/btc-agent-fetch-secrets
   ```

6. **Install and start the systemd units:**
   ```bash
   sudo cp /opt/btc-agent/btc_agent/deploy/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now btc-agent-secrets.service btc-agent.service btc-agent-app.service
   ```

7. **Check the keys arrived** (this lists names only, not values):
   ```bash
   sudo cut -d= -f1 /etc/btc-agent/env
   ```

8. **Do one run by hand** before trusting the hourly timer. This loads the env file and runs `main.py` once as the
   service user:
   ```bash
   sudo -u btc-agent -H bash -c 'set -a; . /etc/btc-agent/env; set +a; cd /opt/btc-agent/btc_agent && ../.venv/bin/python main.py'
   ```
   Then check `/opt/btc-agent/btc_agent/logs/btc_agent.log` for errors, and open `http://<instance-public-ip>:8501` to see
   the frontend.

## Day-to-day

| Task | Command |
|---|---|
| Is it running? | `systemctl status btc-agent btc-agent-app` |
| Follow the agent's logs | `journalctl -u btc-agent -f` (or `tail -f /opt/btc-agent/btc_agent/logs/btc_agent.log`) |
| Follow the frontend's logs | `journalctl -u btc-agent-app -f` |
| Did the secrets fetch work? | `journalctl -u btc-agent-secrets` |
| Stop trading | `sudo systemctl stop btc-agent` |

**Deploying code changes** (`git fetch` alone doesn't change any files; `git pull` does):
```bash
sudo git -C /opt/btc-agent pull
sudo /opt/btc-agent/.venv/bin/pip install -r /opt/btc-agent/btc_agent/requirements.txt
sudo systemctl restart btc-agent btc-agent-app
```
If a pull changed anything in `deploy/`, repeat steps 5 and 6 (and `sudo systemctl daemon-reload`) before restarting.

**Changing a key:** update it in Parameter Store (`aws ssm put-parameter --name /btc-agent/NAME --value "..." --overwrite`),
then re-fetch and restart:
```bash
sudo systemctl restart btc-agent-secrets && sudo systemctl restart btc-agent btc-agent-app
```

## Troubleshooting

- **`btc-agent-secrets` failed with "Couldn't determine the AWS region":** the instance metadata service isn't reachable.
  Add `Environment=AWS_REGION=<your-region>` under `[Service]` in `btc-agent-secrets.service`, then repeat step 6.
- **"No parameters found" or an AccessDenied error:** the IAM role isn't attached, its policy doesn't match
  `iam-policy.json`, or the parameters were created in a different region from the instance.
- **"Permission denied" writing `trading.db` or `btc_agent.log`:** re-run the `install -d` line from step 4.
- **The agent or frontend won't start:** `journalctl -u btc-agent -n 50` shows the error. A missing key (e.g.
  `TELEGRAM_BOT_TOKEN is not set`) means it isn't in Parameter Store under `/btc-agent/`.
