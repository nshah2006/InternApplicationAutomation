#!/usr/bin/env python3
"""
Helper script for database migrations.
"""

import os
import sys
import subprocess

def run_migration(command):
    """Run an alembic migration command."""
    cmd = ['alembic'] + command.split()
    print(f'Running: {" ".join(cmd)}')
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python migrate.py <command>')
        print('Commands:')
        print('  init          - Initialize database (create tables)')
        print('  upgrade       - Apply all pending migrations')
        print('  downgrade     - Rollback last migration')
        print('  revision      - Create a new migration')
        print('  history       - Show migration history')
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        success = run_migration('upgrade head')
    elif command == 'upgrade':
        success = run_migration('upgrade head')
    elif command == 'downgrade':
        success = run_migration('downgrade -1')
    elif command == 'revision':
        msg = sys.argv[2] if len(sys.argv) > 2 else 'auto migration'
        success = run_migration(f'revision --autogenerate -m "{msg}"')
    elif command == 'history':
        success = run_migration('history')
    else:
        print(f'Unknown command: {command}')
        sys.exit(1)
    
    sys.exit(0 if success else 1)
