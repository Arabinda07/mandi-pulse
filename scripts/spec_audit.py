#!/usr/bin/env python3
"""
Mandi Pulse: Spec Kit & Constitutional Invariant Auditor
Validates that .specify/ constitution, templates, and specifications are structurally sound.
"""

import os
import sys

def audit():
    print("[INFO] Starting Spec Kit & Constitutional Invariant Audit...")
    errors = []

    # 1. Verify Constitution Exists
    constitution_path = os.path.join(".specify", "constitution.md")
    if not os.path.exists(constitution_path):
        errors.append("Missing .specify/constitution.md")
    else:
        print("[OK] Project Constitution exists.")

    # 2. Verify Spec Templates Exist
    templates = [
        "spec-template.md",
        "plan-template.md",
        "tasks-template.md",
        "checklist-template.md",
    ]
    for t in templates:
        tp = os.path.join(".specify", "templates", t)
        if not os.path.exists(tp):
            errors.append(f"Missing template: {tp}")
        else:
            print(f"[OK] Template verified: {t}")

    # 3. Verify Specifications in .specify/specs/
    specs_dir = os.path.join(".specify", "specs")
    if os.path.exists(specs_dir):
        for entry in os.listdir(specs_dir):
            spec_folder = os.path.join(specs_dir, entry)
            if os.path.isdir(spec_folder):
                spec_md = os.path.join(spec_folder, "spec.md")
                if not os.path.exists(spec_md):
                    errors.append(f"Spec package '{entry}' is missing spec.md")
                else:
                    print(f"[OK] Specification package verified: {entry}")

    if errors:
        print(f"\n[FAIL] Found {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\n[SUCCESS] All Spec Kit structures and specifications verified.")

if __name__ == "__main__":
    audit()
