"""
CLI: python -m etl.cli run --mode full|oil|gas|rig|concession
      python -m etl.cli healthcheck
"""
import argparse
import sys


def cmd_run(args):
    from etl.run import run_etl
    run_id, ok, user_msg, tech = run_etl(args.mode, triggered_by="cli")
    print(f"Run ID: {run_id}")
    print(f"Success: {ok}")
    if user_msg:
        print(f"Message: {user_msg}")
    if not ok and tech.get("error"):
        print(f"Error: {tech.get('error')}")
    sys.exit(0 if ok else 1)


def cmd_healthcheck(args):
    from etl.healthcheck import healthcheck
    ok, messages = healthcheck()
    for m in messages:
        print(m)
    sys.exit(0 if ok else 1)


def main():
    parser = argparse.ArgumentParser(description="NUPRC ETL Pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run pipeline")
    run_p.add_argument("--mode", choices=["full", "oil", "gas", "rig", "concession"], default="full", help="Pipeline mode")
    run_p.set_defaults(func=cmd_run)

    health_p = sub.add_parser("healthcheck", help="Verify NUPRC pages, concession PDF, DB")
    health_p.set_defaults(func=cmd_healthcheck)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
