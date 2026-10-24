# One-off / manual helper for setting the trading agent's cash balance directly, without going
# through the agent (which has no tool for creating or resetting cash on its own). run_agent already
# calls seed_cash_if_empty itself on every cycle, so this script is only needed to pick a starting
# balance other than STARTING_CASH_BALANCE, or to manually top up / adjust cash later via --force.
#
# Run from the btc_agent directory:
#   python seed_cash.py              # seed STARTING_CASH_BALANCE (env var, default 10000) if no balance is set yet
#   python seed_cash.py 5000         # seed a specific starting balance if no balance is set yet
#   python seed_cash.py 5000 --force # overwrite the existing balance (e.g. a manual top-up)

import argparse

from src.agent import STARTING_CASH_BALANCE, _cash_balance, _set_cash
from src.database.database import get_engine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("amount", type=float, nargs="?", default=STARTING_CASH_BALANCE, help=f"Cash balance to set (default: {STARTING_CASH_BALANCE})")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing balance instead of leaving it alone")
    args = parser.parse_args()

    engine = get_engine()
    current = _cash_balance(engine)
    if current is not None and not args.force:
        print(f"Cash is already set to {current:.2f}; leaving it alone. Pass --force to overwrite.")
        return

    _set_cash(engine, args.amount)
    print(f"Cash set to {args.amount:.2f}.")


if __name__ == "__main__":
    main()
