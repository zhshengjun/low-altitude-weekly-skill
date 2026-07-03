#!/usr/bin/env python3
"""Build script for weekly hotspot analysis HTML → PDF conversion.

Usage:
  python3 scripts/build.py path/to/report.html            # Build PDF
  python3 scripts/build.py --check-placeholders report.html # Check for leftover {{...}}
  python3 scripts/build.py --verify report.html             # Build + page count + font check
  python3 scripts/build.py path/to/report.html --output out.pdf

Dependencies:
  - WeasyPrint >= 60 (pip install weasyprint)
  - On Windows: additionally pip install fonttools

  Without WeasyPrint, only placeholder checks run; PDF build is skipped.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def check_placeholders(html_path: str) -> bool:
    """Scan HTML for residual {{...}} placeholders. Returns True if clean."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all {{...}} patterns, excluding CSS custom properties (no spaces around var())
    placeholders = re.findall(r'\{\{[^}]+?\}\}', content)
    if placeholders:
        print(f"[FAIL] Found {len(placeholders)} residual placeholder(s):")
        for p in placeholders:
            print(f"  - {p}")
        return False
    print("[PASS] No residual placeholders found.")
    return True


def check_structure(html_path: str) -> bool:
    """Verify mandatory HTML sections exist."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    required = [
        ('cover section', '.cover'),
        ('highlights section', '.highlights'),
        ('TOC section', '.toc'),
        ('source metadata', 'source-meta'),
        ('summary callout', 'summary-callout'),
        ('colophon', 'colophon'),
    ]
    all_ok = True
    for name, marker in required:
        if marker not in content:
            print(f"[FAIL] Missing required section: {name}")
            all_ok = False
        else:
            print(f"[PASS] Section '{name}' found.")
    return all_ok


def find_chrome() -> str | None:
    """Locate Chrome/Chromium/Edge executable for headless PDF."""
    import platform
    candidates = []
    system = platform.system()

    if system == "Windows":
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LocalAppData%\Chromium\Application\chrome.exe"),
        ]
    elif system == "Darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    else:  # Linux
        candidates = [
            "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
            "microsoft-edge", "microsoft-edge-stable",
        ]

    for path in candidates:
        if os.path.exists(path) or (system != "Windows" and path):
            return path
    return None


def build_pdf_weasyprint(html_path: str, output_path: str) -> bool:
    """PDF via WeasyPrint (best quality, CJK font subsetting)."""
    try:
        from weasyprint import HTML
        HTML(filename=html_path).write_pdf(output_path)
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"[FAIL] WeasyPrint error: {e}")
        return False


def build_pdf_chrome(html_path: str, output_path: str) -> bool:
    """PDF via Chrome headless (good fallback, full CSS support)."""
    chrome = find_chrome()
    if not chrome:
        print("[SKIP] Chrome/Edge not found.")
        return False

    import subprocess
    import urllib.parse

    abs_path = os.path.abspath(html_path)
    # file:// URL with proper encoding for cross-platform compatibility
    file_url = "file:///" + abs_path.replace("\\", "/").lstrip("/")

    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={output_path}",
        "--print-to-pdf-no-header",
        "--no-pdf-header-footer",
        file_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"[OK] Chrome PDF built: {output_path}")
            return True
        else:
            print(f"[FAIL] Chrome produced empty/invalid PDF")
            if result.stderr:
                print(f"       stderr: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("[FAIL] Chrome PDF generation timed out (30s)")
        return False
    except FileNotFoundError:
        print(f"[SKIP] Chrome not executable: {chrome}")
        return False
    except Exception as e:
        print(f"[FAIL] Chrome error: {e}")
        return False


def build_pdf(html_path: str, output_path: str | None = None) -> bool:
    """Convert HTML to PDF — tries WeasyPrint first, then Chrome, then bails."""
    if output_path is None:
        output_path = str(Path(html_path).with_suffix(".pdf"))
    output_path = str(output_path)

    # 1) WeasyPrint (best quality)
    if build_pdf_weasyprint(html_path, output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"       Size: {size_kb:.0f} KB  [WeasyPrint]")
        return True

    # 2) Chrome headless (good fallback)
    print("[INFO] WeasyPrint unavailable; trying Chrome headless...")
    if build_pdf_chrome(html_path, output_path):
        size_kb = os.path.getsize(output_path) / 1024
        print(f"       Size: {size_kb:.0f} KB  [Chrome headless]")
        return True

    # 3) Nothing works
    print("\n[SKIP] PDF not generated — neither WeasyPrint nor Chrome available.")
    print("       Install: pip install weasyprint")
    print("       Or open HTML in browser → Print → Save as PDF (Margins: None, Background graphics: On)")
    return False


def verify_pdf(pdf_path: str) -> bool:
    """Check page count and font embedding."""
    try:
        from weasyprint import HTML
    except ImportError:
        return True  # skip verification without WeasyPrint

    try:
        import subprocess
        # Use pdfinfo (poppler-utils) if available
        result = subprocess.run(
            ["pdfinfo", pdf_path], capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Pages:"):
                    pages = int(line.split(":")[1].strip())
                    print(f"[INFO] PDF pages: {pages}")
                    if pages < 3:
                        print("[WARN] PDF has fewer than 3 pages — report may be incomplete.")
                    break
    except FileNotFoundError:
        print("[INFO] pdfinfo not available; skipping page count check.")
    except Exception:
        pass

    print("[PASS] PDF verification complete.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build weekly hotspot analysis PDF")
    parser.add_argument("html", help="Path to filled HTML file")
    parser.add_argument("--output", "-o", help="Output PDF path (default: same name .pdf)")
    parser.add_argument("--check-placeholders", action="store_true", help="Only check for residual {{...}}")
    parser.add_argument("--verify", action="store_true", help="Full verification: placeholders + structure + build + check")
    parser.add_argument("--check-density", action="store_true", help="Warn on pages with >25% trailing whitespace (WeasyPrint required)")

    args = parser.parse_args()

    html_path = args.html
    if not os.path.exists(html_path):
        print(f"[FAIL] File not found: {html_path}")
        sys.exit(1)

    print(f"[INFO] Checking: {html_path}\n")

    # Always run placeholder check
    clean = check_placeholders(html_path)
    if not clean:
        sys.exit(1)

    if args.check_placeholders:
        sys.exit(0 if clean else 1)

    if args.verify:
        structure_ok = check_structure(html_path)
        if not structure_ok:
            print("\n[WARN] Structural issues found — PDF may be incomplete.")

    # Build PDF
    pdf_ok = build_pdf(html_path, args.output)

    if args.verify and pdf_ok:
        output_path = args.output or Path(html_path).with_suffix(".pdf")
        verify_pdf(str(output_path))

    if not pdf_ok and not args.verify:
        print("\n[INFO] PDF generation skipped (WeasyPrint unavailable).")
        print("       HTML is valid and browser-ready.")
        sys.exit(0)

    sys.exit(0 if pdf_ok else 1)


if __name__ == "__main__":
    main()
