import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import shutil, os, subprocess, threading
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont

REPO_DIR   = Path(__file__).parent
PAGES_BASE = "https://santhosh-m31.github.io/drone-qr-data/"
RAW_BASE   = "https://raw.githubusercontent.com/Santhosh-M31/drone-qr-data/master/"
LOGO_PATH  = REPO_DIR / "logo.jpg"

LOGO_URL   = PAGES_BASE + "logo.jpg"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{LABEL}</title>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; margin: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      background: #f5f7fa;
      color: #1f2937;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .card {{
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.08);
      padding: 32px 28px;
      max-width: 420px;
      width: 100%;
      text-align: center;
    }}
    .logo {{
      max-width: 180px;
      height: auto;
      margin-bottom: 20px;
    }}
    .msg {{
      font-size: 18px;
      font-weight: 600;
      margin: 12px 0 8px;
    }}
    .fname {{
      font-family: Consolas, "Courier New", monospace;
      background: #eef2f7;
      color: #111827;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 14px;
      word-break: break-all;
      display: inline-block;
      margin-bottom: 20px;
    }}
    .redirect {{
      font-size: 15px;
      color: #4b5563;
      margin-top: 12px;
    }}
    .count {{
      display: inline-block;
      min-width: 28px;
      font-weight: 700;
      color: #0f62fe;
      font-size: 20px;
    }}
    .manual {{
      display: block;
      margin-top: 18px;
      font-size: 13px;
      color: #6b7280;
      text-decoration: none;
    }}
    .manual a {{ color: #0f62fe; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="card">
    <img class="logo" src="{LOGO_URL}" alt="Tec Solution Group">
    <div class="msg">You have downloaded</div>
    <div class="fname" id="fname">{BASENAME}.csv</div>
    <div class="redirect">
      Redirecting to company website in <span class="count" id="count">5</span>
    </div>
    <div class="manual">
      Not redirecting? <a id="manualLink" href="https://www.tecsolutiongroup.com/">Click here</a>
    </div>
  </div>

  <script>
    (async function() {{
      const rawUrl = '{RAW_URL}';
      const redirectUrl = 'https://www.tecsolutiongroup.com/';
      const d = new Date();
      const ts = d.getFullYear() + String(d.getMonth()+1).padStart(2,'0') + String(d.getDate()).padStart(2,'0') + '_' + String(d.getHours()).padStart(2,'0') + String(d.getMinutes()).padStart(2,'0') + String(d.getSeconds()).padStart(2,'0');
      const filename = '{BASENAME}_' + ts + '.csv';
      document.getElementById('fname').textContent = filename;

      try {{
        const res = await fetch(rawUrl);
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 3000);
      }} catch (e) {{
        const a = document.createElement('a');
        a.href = rawUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }}

      let n = 5;
      const countEl = document.getElementById('count');
      const timer = setInterval(() => {{
        n -= 1;
        if (n <= 0) {{
          clearInterval(timer);
          window.location.href = redirectUrl;
        }} else {{
          countEl.textContent = n;
        }}
      }}, 1000);
    }})();
  </script>
</body>
</html>
"""


def to_label(filename):
    """product-delivery-01-01.csv  ->  Product Delivery 01 01"""
    stem = Path(filename).stem
    return " ".join(w.capitalize() for w in stem.replace("-", " ").replace("_", " ").split())


def git_run(args):
    return subprocess.run(["git"] + args, cwd=REPO_DIR, capture_output=True, text=True)


def get_modified_csvs():
    """Return set of CSV filenames (repo root only) that have uncommitted changes."""
    r = git_run(["status", "--porcelain"])
    modified = set()
    for line in r.stdout.splitlines():
        if not line.strip():
            continue
        name = line[3:].strip().strip('"')
        if name.endswith(".csv") and "/" not in name and "\\" not in name:
            modified.add(name)
    return modified


def list_repo_csvs():
    """Return sorted list of CSV filenames in the repo root."""
    return sorted(f.name for f in REPO_DIR.glob("*.csv"))


# ──────────────────────────────────────────────────────────────────────────────
# Background worker for Tab 1 (Publish New)
# ──────────────────────────────────────────────────────────────────────────────

def publish_worker(csv_path_str, log_fn, done_fn):
    def git_log(args):
        r = git_run(args)
        if r.stdout.strip(): log_fn(r.stdout.strip())
        if r.stderr.strip(): log_fn(r.stderr.strip())
        return r.returncode

    try:
        csv_path = Path(csv_path_str.strip().strip('"'))
        if not csv_path.exists():
            log_fn(f"ERROR: File not found:\n  {csv_path}")
            done_fn(success=False)
            return

        filename = csv_path.name
        basename = csv_path.stem
        label    = to_label(filename)

        log_fn(f"File  : {filename}")
        log_fn(f"Label : {label}\n")

        # 1. Copy CSV into repo root
        dest = REPO_DIR / filename
        shutil.copy2(csv_path, dest)
        log_fn(f"Copied CSV     ->  {dest}")

        raw_url  = RAW_BASE + filename
        page_url = PAGES_BASE + "download/" + basename + ".html"

        # 2. Generate HTML download page
        (REPO_DIR / "download").mkdir(exist_ok=True)
        html_path = REPO_DIR / "download" / (basename + ".html")
        html_path.write_text(
            HTML_TEMPLATE.format(LABEL=label, RAW_URL=raw_url,
                                 FILENAME=filename, BASENAME=basename,
                                 LOGO_URL=LOGO_URL),
            encoding="utf-8"
        )
        log_fn(f"HTML page      ->  {html_path}")

        # 3. Generate QR code image
        (REPO_DIR / "qrcodes").mkdir(exist_ok=True)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10, border=4,
        )
        qr.add_data(page_url)
        qr.make(fit=True)
        qr_img  = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_w, qr_h = qr_img.size

        logo = Image.open(LOGO_PATH).convert("RGB")
        lpad = 20
        lw   = qr_w - lpad * 2
        lh   = int(logo.height * (lw / logo.width))
        logo_r = logo.resize((lw, lh), Image.LANCZOS)

        lbl_h = 55
        total = lh + 12 + qr_h + lbl_h
        final = Image.new("RGB", (qr_w, total), "white")
        final.paste(logo_r, (lpad, 8))
        final.paste(qr_img, (0, lh + 12))

        draw = ImageDraw.Draw(final)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
        except Exception:
            font = ImageFont.load_default()

        bbox   = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(((qr_w - text_w) // 2, lh + 12 + qr_h + 14), label, fill="black", font=font)

        out_path = REPO_DIR / "qrcodes" / (basename + "_QR.png")
        final.save(out_path)
        log_fn(f"QR image       ->  {out_path}\n")

        # 4. Git commit & push
        log_fn("Running git add...")
        git_log(["add", str(dest), str(html_path), str(out_path)])

        log_fn("Running git commit...")
        git_log(["commit", "-m", f"Add {filename}"])

        log_fn("Running git push...")
        rc = git_log(["push"])

        if rc == 0:
            log_fn("\n" + "=" * 52)
            log_fn("PUBLISHED SUCCESSFULLY")
            log_fn(f"Scan URL  : {page_url}")
            log_fn(f"QR image  : {out_path}")
            log_fn("(GitHub Pages may take ~1 min to refresh)")
            log_fn("=" * 52)
            done_fn(success=True, label=label, page_url=page_url, out_path=out_path)
        else:
            log_fn("\nGit push FAILED — check the log above.")
            done_fn(success=False)

    except Exception as exc:
        import traceback
        log_fn(f"ERROR: {exc}\n{traceback.format_exc()}")
        done_fn(success=False)


# ──────────────────────────────────────────────────────────────────────────────
# Main application
# ──────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drone QR Publisher")
        self.geometry("700x560")
        self.resizable(False, False)
        self.configure(bg="#f0f4f8")

        tk.Label(self, text="Drone QR Publisher",
                 font=("Arial", 17, "bold"), bg="#f0f4f8", fg="#1a3a5c").pack(pady=(14, 2))
        tk.Frame(self, height=1, bg="#c8d8e8").pack(fill="x", padx=18, pady=(4, 0))

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",         background="#f0f4f8", borderwidth=0)
        style.configure("TNotebook.Tab",     font=("Arial", 10, "bold"), padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", "#0055bb"), ("!selected", "#dde8f4")],
                  foreground=[("selected", "white"),   ("!selected", "#333")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(6, 14))

        self._build_publish_tab(nb)
        self._build_manage_tab(nb)

    # ── Tab 1: Publish New CSV ────────────────────────────────────────────────

    def _build_publish_tab(self, nb):
        f = tk.Frame(nb, bg="#f0f4f8")
        nb.add(f, text="  Publish New CSV  ")

        row = tk.Frame(f, bg="#f0f4f8")
        row.pack(fill="x", padx=18, pady=(16, 6))
        tk.Label(row, text="CSV File:", font=("Arial", 10, "bold"),
                 bg="#f0f4f8", width=9, anchor="w").pack(side="left")
        self.path_var = tk.StringVar()
        tk.Entry(row, textvariable=self.path_var, font=("Arial", 10),
                 width=48, relief="solid", bd=1).pack(side="left", padx=(4, 6), ipady=4)
        tk.Button(row, text="Browse...", command=self._browse, font=("Arial", 9),
                  relief="solid", bd=1, padx=6, pady=2).pack(side="left")

        self.preview_var = tk.StringVar(value='Label preview:  —')
        tk.Label(f, textvariable=self.preview_var, font=("Arial", 10, "italic"),
                 bg="#f0f4f8", fg="#0066cc").pack(anchor="w", padx=22)
        self.path_var.trace_add("write", self._on_path_change)

        self.pub_btn = tk.Button(f, text="Publish & Generate QR",
                                 font=("Arial", 12, "bold"),
                                 bg="#0055bb", fg="white",
                                 activebackground="#003d99", activeforeground="white",
                                 relief="flat", padx=16, pady=8, cursor="hand2",
                                 command=self._on_publish)
        self.pub_btn.pack(pady=10)

        tk.Label(f, text="Log", font=("Arial", 9, "bold"), bg="#f0f4f8", anchor="w").pack(fill="x", padx=18)
        self.pub_log = scrolledtext.ScrolledText(f, height=12, font=("Courier", 9),
                                                  state="disabled", bg="#1e1e2e", fg="#d4d4d4",
                                                  relief="flat", bd=0)
        self.pub_log.pack(fill="both", padx=18, pady=(2, 14))

    # ── Tab 2: Manage Existing CSVs ───────────────────────────────────────────

    def _build_manage_tab(self, nb):
        f = tk.Frame(nb, bg="#f0f4f8")
        nb.add(f, text="  Manage Existing CSVs  ")

        # Top bar
        top = tk.Frame(f, bg="#f0f4f8")
        top.pack(fill="x", padx=18, pady=(14, 6))
        tk.Label(top, text="CSVs in the GitHub repo:", font=("Arial", 10, "bold"),
                 bg="#f0f4f8").pack(side="left")
        self.pull_btn = tk.Button(top, text="⟳  Pull Latest from GitHub",
                                   font=("Arial", 9, "bold"),
                                   bg="#2a7a38", fg="white", activebackground="#1d5828",
                                   relief="flat", padx=10, pady=4, cursor="hand2",
                                   command=self._on_pull)
        self.pull_btn.pack(side="right")

        # Listbox
        lf = tk.Frame(f, bg="#f0f4f8")
        lf.pack(fill="both", expand=True, padx=18)

        sb = tk.Scrollbar(lf, orient="vertical")
        self.csv_list = tk.Listbox(lf, font=("Courier", 10), yscrollcommand=sb.set,
                                    selectmode="single", relief="solid", bd=1,
                                    activestyle="none", height=10,
                                    bg="white", fg="#222",
                                    selectbackground="#0055bb", selectforeground="white")
        sb.config(command=self.csv_list.yview)
        sb.pack(side="right", fill="y")
        self.csv_list.pack(side="left", fill="both", expand=True)
        self._csv_names = []

        # Action buttons
        btn_row = tk.Frame(f, bg="#f0f4f8")
        btn_row.pack(fill="x", padx=18, pady=(8, 4))
        self.open_btn = tk.Button(btn_row, text="Open for Editing",
                                   font=("Arial", 10, "bold"),
                                   bg="#555", fg="white", activebackground="#333",
                                   relief="flat", padx=12, pady=6, cursor="hand2",
                                   command=self._on_open)
        self.open_btn.pack(side="left", padx=(0, 10))
        self.push_sel_btn = tk.Button(btn_row, text="Push Selected File to GitHub",
                                       font=("Arial", 10, "bold"),
                                       bg="#0055bb", fg="white", activebackground="#003d99",
                                       relief="flat", padx=12, pady=6, cursor="hand2",
                                       command=self._on_push_selected)
        self.push_sel_btn.pack(side="left")

        # Log
        tk.Label(f, text="Log", font=("Arial", 9, "bold"), bg="#f0f4f8", anchor="w").pack(fill="x", padx=18)
        self.mgr_log = scrolledtext.ScrolledText(f, height=7, font=("Courier", 9),
                                                  state="disabled", bg="#1e1e2e", fg="#d4d4d4",
                                                  relief="flat", bd=0)
        self.mgr_log.pack(fill="x", padx=18, pady=(2, 12))

        # Populate on startup
        self.after(100, self._refresh_csv_list)

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _log(self, widget, msg):
        widget.configure(state="normal")
        widget.insert(tk.END, msg + "\n")
        widget.see(tk.END)
        widget.configure(state="disabled")
        widget.update_idletasks()

    def _refresh_csv_list(self):
        modified = get_modified_csvs()
        names    = list_repo_csvs()
        self.csv_list.delete(0, tk.END)
        self._csv_names = names
        for name in names:
            tag = "  ★ modified" if name in modified else ""
            self.csv_list.insert(tk.END, f"  {name}{tag}")
        # Color modified rows
        for i, name in enumerate(names):
            if name in modified:
                self.csv_list.itemconfig(i, fg="#cc6600")

    # ── Tab 1 callbacks ───────────────────────────────────────────────────────

    def _browse(self):
        p = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if p:
            self.path_var.set(p)

    def _on_path_change(self, *_):
        val = self.path_var.get().strip().strip('"')
        if val:
            try:
                self.preview_var.set(f'Label preview:  "{to_label(Path(val).name)}"')
            except Exception:
                self.preview_var.set('Label preview:  —')
        else:
            self.preview_var.set('Label preview:  —')

    def _on_publish(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No file selected", "Please enter or browse for a CSV file.")
            return
        self.pub_btn.configure(state="disabled")
        self.pub_log.configure(state="normal")
        self.pub_log.delete("1.0", tk.END)
        self.pub_log.configure(state="disabled")

        def log_fn(msg):
            self._log(self.pub_log, msg)

        def done_fn(success, label="", page_url="", out_path=""):
            self.pub_btn.configure(state="normal")
            self.after(0, self._refresh_csv_list)
            if success:
                messagebox.showinfo(
                    "Published!",
                    f"QR code published!\n\nLabel: {label}\n\nScan URL:\n{page_url}\n\n"
                    f"QR image:\n{out_path}\n\n"
                    "GitHub Pages may take ~1 min to go live."
                )

        threading.Thread(target=publish_worker, args=(path, log_fn, done_fn), daemon=True).start()

    # ── Tab 2 callbacks ───────────────────────────────────────────────────────

    def _on_pull(self):
        self.pull_btn.configure(state="disabled")

        def worker():
            self._log(self.mgr_log, "Running git pull...")
            r = git_run(["pull"])
            if r.stdout.strip(): self._log(self.mgr_log, r.stdout.strip())
            if r.stderr.strip(): self._log(self.mgr_log, r.stderr.strip())
            if r.returncode == 0:
                self._log(self.mgr_log, "Pull complete.")
            else:
                self._log(self.mgr_log, "Pull finished with warnings — see above.")
            self.after(0, self._refresh_csv_list)
            self.after(0, lambda: self.pull_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _on_open(self):
        sel = self.csv_list.curselection()
        if not sel:
            messagebox.showwarning("No file selected", "Click a CSV in the list first.")
            return
        name = self._csv_names[sel[0]]
        path = REPO_DIR / name
        if not path.exists():
            messagebox.showerror("Not found", f"{name} was not found locally.\nTry Pull Latest first.")
            return
        os.startfile(str(path))
        self._log(self.mgr_log, f"Opened: {name}  (save in your editor, then click Push)")

    def _on_push_selected(self):
        sel = self.csv_list.curselection()
        if not sel:
            messagebox.showwarning("No file selected", "Click a CSV in the list first.")
            return
        name = self._csv_names[sel[0]]
        self.push_sel_btn.configure(state="disabled")

        def worker():
            self._log(self.mgr_log, f"\nPushing {name}...")

            def glog(args):
                r = git_run(args)
                if r.stdout.strip(): self._log(self.mgr_log, r.stdout.strip())
                if r.stderr.strip(): self._log(self.mgr_log, r.stderr.strip())
                return r.returncode

            glog(["add", str(REPO_DIR / name)])
            rc = glog(["commit", "-m", f"Update {name}"])
            if rc != 0:
                self._log(self.mgr_log, "(nothing new to commit, or commit failed)")
            rc = glog(["push"])

            if rc == 0:
                self._log(self.mgr_log, f"Done! {name} pushed to GitHub.")
                self.after(0, self._refresh_csv_list)
                self.after(0, lambda: messagebox.showinfo(
                    "Pushed!", f"{name}\nhas been pushed to GitHub successfully."
                ))
            else:
                self._log(self.mgr_log, "Push FAILED — see output above.")
                self.after(0, lambda: messagebox.showerror(
                    "Push Failed", "Git push failed.\nCheck the log for details."
                ))
            self.after(0, lambda: self.push_sel_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
