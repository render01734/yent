FROM debian:bookworm-slim

# Python ve madencinin (binary) ihtiyaç duyabileceği temel kütüphaneleri kuruyoruz
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 ca-certificates libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kod dosyalarını çalışma dizinine kopyalıyoruz
COPY engine.py /app/engine.py
COPY start.sh /app/start.sh

# Başlatıcı betiğe (start.sh) çalışma izni veriyoruz
RUN chmod +x /app/start.sh

# Güvenlik: Render vb. platformların root izinleriyle ilgili hata vermemesi için
# standart bir kullanıcı (appuser) oluşturup yetkilendiriyoruz
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Web arayüzünün (Insert ile açılan) dışarıya açılacağı port
EXPOSE 8080

# Konteyner ayağa kalktığında çalıştırılacak ilk komut
CMD ["/app/start.sh"]
