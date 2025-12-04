#!/bin/bash
# install.sh — smart-commit kurulum script'i
# Kullanım: chmod +x install.sh && ./install.sh

set -e

echo "🚀 smart-commit v1.0 kurulumu başlatılıyor..."

# 1. Node.js ≥20 kontrolü
if ! command -v node &> /dev/null; then
    echo "❌ Node.js bulunamadı. Kurulum:"
    echo "   macOS: brew install node"
    echo "   Ubuntu: sudo apt install nodejs npm"
    exit 1
fi

NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VER" -lt 20 ]; then
    echo "❌ Node.js sürümünüz $NODE_VER — ≥20 gereklidir."
    exit 1
fi

# 2. Qwen Code CLI'yi kur
echo "📦 Qwen Code CLI kuruluyor..."
if command -v qwen &> /dev/null; then
    echo "✅ qwen zaten kurulu."
else
    npm install -g @qwen-code/qwen-code@latest
    echo "✅ qwen kuruldu: $(qwen --version)"
fi

# 3. Python bağımlılıkları
echo "🐍 Python bağımlılıkları kuruluyor..."
pip3 install typer rich PyYAML GitPython requests

# 4. .qwen ayarları (otomatik yetkilendirme için)
QWEN_DIR="$HOME/.qwen"
mkdir -p "$QWEN_DIR"
cat > "$QWEN_DIR/settings.json" << 'EOF'
{
  "sessionTokenLimit": 32000,
  "experimental": {
    "visionModelPreview": false
  }
}
EOF
echo "✅ ~/.qwen/settings.json oluşturuldu."

# 5. Kurulum tamam
echo
echo "🎉 Kurulum tamamlandı!"
echo
echo "Şimdi çalıştırabilirsiniz:"
echo "  python3 smart_commit.py init"
echo "veya:"
echo "  python3 smart_commit.py propose"