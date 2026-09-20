"""Optional helper: download the NIST PDFs into data/raw_pdfs/.

Usage (from the project root):  python scripts/download_pdfs.py

If a link is dead, download that file manually (search its title on
https://csrc.nist.gov/publications) and save it under the filename shown here.
"""
import sys
import urllib.request
from pathlib import Path

PDFS = {
    "nist_csf_2_0.pdf": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
    "nist_sp_800_61r2.pdf": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf",
    "nist_sp_800_63b_4.pdf": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-63B-4.pdf",
    "nist_sp_800_30r1.pdf": "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-30r1.pdf",
    "nist_sp_800_40r4.pdf": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-40r4.pdf",
    "nist_sp_800_83r1.pdf": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-83r1.pdf",
    "nist_sp_800_88r1.pdf": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-88r1.pdf",
    "nist_sp_800_34r1.pdf": "https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-34r1.pdf",
    "nist_ir_7621r1.pdf": "https://nvlpubs.nist.gov/nistpubs/ir/2016/NIST.IR.7621r1.pdf",
}

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw_pdfs"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, url in PDFS.items():
        dest = OUT_DIR / name
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"[skip] {name} (already downloaded)")
            continue
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if not data.startswith(b"%PDF"):
                raise ValueError("response is not a PDF")
            dest.write_bytes(data)
            print(f"[ ok ] {name} ({len(data) / 1e6:.1f} MB)")
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}\n       -> download manually: {url}")
            failed.append(name)
    print(f"\nDone. {len(PDFS) - len(failed)}/{len(PDFS)} files available in {OUT_DIR}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
