#!/bin/bash
# Script de instalación automática para Claude Code Status Bar
# Autor: Claude Code Status Bar Team
# Uso: bash install.sh

set -e  # Salir si hay algún error

# Colores para la salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Code Status Bar - Instalador Automático      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar Python 3
echo -e "${YELLOW}[1/5]${NC} Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 no está instalado${NC}"
    echo ""
    echo "Por favor, instala Python 3 primero:"
    echo "  Debian/Ubuntu: sudo apt update && sudo apt install python3 -y"
    echo "  Fedora/RHEL:   sudo dnf install python3 -y"
    echo "  macOS:         brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python 3 encontrado: $PYTHON_VERSION${NC}"
echo ""

# Crear directorio
echo -e "${YELLOW}[2/5]${NC} Creando directorio de scripts..."
mkdir -p ~/.claude-code/scripts
echo -e "${GREEN}✓ Directorio creado: ~/.claude-code/scripts${NC}"
echo ""

# Copiar script
echo -e "${YELLOW}[3/5]${NC} Copiando script de status bar..."
if [ -f "usage_bar.py" ]; then
    cp usage_bar.py ~/.claude-code/scripts/
    chmod +x ~/.claude-code/scripts/usage_bar.py
    echo -e "${GREEN}✓ Script copiado y permisos configurados${NC}"
else
    echo -e "${RED}✗ No se encontró usage_bar.py en el directorio actual${NC}"
    echo "Asegúrate de ejecutar este script desde el directorio Claude-Status-Bar"
    exit 1
fi
echo ""

# Probar script
echo -e "${YELLOW}[4/5]${NC} Probando el script..."
TEST_OUTPUT=$(echo '{"current_tokens": 450000, "expected_total_tokens": 500000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 ~/.claude-code/scripts/usage_bar.py)

if [ -n "$TEST_OUTPUT" ]; then
    echo -e "${GREEN}✓ Script funciona correctamente${NC}"
    echo "  Salida de prueba: $TEST_OUTPUT"
else
    echo -e "${RED}✗ El script no produjo salida${NC}"
    exit 1
fi
echo ""

# Configurar Claude Code
echo -e "${YELLOW}[5/5]${NC} Configurando Claude Code..."

SETTINGS_FILE="$HOME/.claude/settings.json"
SETTINGS_DIR="$HOME/.claude"

# Crear directorio si no existe
mkdir -p "$SETTINGS_DIR"

# Verificar si el archivo existe
if [ -f "$SETTINGS_FILE" ]; then
    echo -e "${YELLOW}⚠ El archivo settings.json ya existe${NC}"
    echo "Contenido actual:"
    cat "$SETTINGS_FILE"
    echo ""

    # Verificar si ya tiene configuración de statusLine
    if grep -q '"statusLine"' "$SETTINGS_FILE"; then
        echo -e "${YELLOW}⚠ Ya existe una configuración de statusLine${NC}"
        echo ""
        read -p "¿Deseas sobrescribirla? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            echo -e "${BLUE}ℹ Instalación completada sin modificar settings.json${NC}"
            echo "Puedes agregar manualmente la configuración:"
            echo ""
            echo '  "statusLine": {'
            echo '    "type": "command",'
            echo '    "command": "python3 ~/.claude-code/scripts/usage_bar.py",'
            echo '    "padding": 0'
            echo '  }'
            exit 0
        fi
    fi

    # Hacer backup
    BACKUP_FILE="$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$SETTINGS_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup creado: $BACKUP_FILE${NC}"

    # Agregar o actualizar statusLine usando Python
    python3 << 'EOF'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")
with open(settings_file, 'r') as f:
    settings = json.load(f)

settings['statusLine'] = {
    "type": "command",
    "command": "python3 ~/.claude-code/scripts/usage_bar.py",
    "padding": 0
}

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print("✓ Configuración actualizada")
EOF

else
    # Crear archivo nuevo
    cat > "$SETTINGS_FILE" << 'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude-code/scripts/usage_bar.py",
    "padding": 0
  }
}
EOF
    echo -e "${GREEN}✓ Archivo settings.json creado${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✓ Instalación completada exitosamente          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "1. Cierra completamente Claude Code (si está abierto)"
echo "2. Vuelve a abrir Claude Code"
echo "3. Deberías ver el status bar en la parte inferior"
echo ""
echo -e "${BLUE}Ejemplo de salida:${NC}"
echo "  [████████████░░░░░░░░] 45% Reset: Today 15:00"
echo ""
echo -e "${YELLOW}Si tienes problemas:${NC}"
echo "  - Lee la sección de troubleshooting en README.md"
echo "  - Ejecuta: python3 ~/.claude-code/scripts/usage_bar.py (manual)"
echo "  - Verifica: cat ~/.claude/settings.json"
echo ""
echo -e "${GREEN}¡Gracias por usar Claude Code Status Bar!${NC}"
