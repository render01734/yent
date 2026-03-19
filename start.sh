#!/bin/bash

# Python loglarının (konsol çıktılarının) gecikmeden, anında web arayüzüne düşmesini sağlar
export PYTHONUNBUFFERED=1

echo "[SİSTEM] Yenten (YespowerR16) madencilik altyapısı başlatılıyor..."
echo "[SİSTEM] Web loglarını görmek için Insert tuşuna basmayı unutmayın."

# engine.py dosyasını ana süreç olarak (PID 1) başlatır
exec python3 /app/engine.py
