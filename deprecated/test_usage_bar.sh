#!/bin/bash
# Script de prueba para verificar el funcionamiento de usage_bar.py

echo "=== Pruebas de Claude Code Status Bar ==="
echo ""

# Colores para la salida
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Sonnet 4.5 con 45% de uso
echo -e "${BLUE}Test 1: Sonnet 4.5 (1M tokens) - 45% de uso${NC}"
echo '{"current_tokens": 450000, "expected_total_tokens": 500000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 usage_bar.py
echo ""

# Test 2: Sonnet 4.5 con 90% de uso
echo -e "${BLUE}Test 2: Sonnet 4.5 (1M tokens) - 90% de uso${NC}"
echo '{"current_tokens": 900000, "expected_total_tokens": 950000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 usage_bar.py
echo ""

# Test 3: Sonnet 3.5 con 60% de uso (200K limit)
echo -e "${BLUE}Test 3: Sonnet 3.5 (200K tokens) - 60% de uso${NC}"
echo '{"current_tokens": 120000, "expected_total_tokens": 150000, "model": {"id": "claude-sonnet-3-5", "display_name": "Claude Sonnet 3.5"}}' | python3 usage_bar.py
echo ""

# Test 4: Haiku con 25% de uso
echo -e "${BLUE}Test 4: Haiku (200K tokens) - 25% de uso${NC}"
echo '{"current_tokens": 50000, "expected_total_tokens": 60000, "model": {"id": "claude-haiku", "display_name": "Claude Haiku"}}' | python3 usage_bar.py
echo ""

# Test 5: Sin datos de tokens (muestra plan)
echo -e "${BLUE}Test 5: Sin datos de tokens - debería mostrar plan${NC}"
echo '{"current_tokens": 0, "expected_total_tokens": 0, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 usage_bar.py
echo ""

# Test 6: Uso extremadamente alto (100%+)
echo -e "${BLUE}Test 6: Uso extremo (>100%) - debe limitarse a 100%${NC}"
echo '{"current_tokens": 1200000, "expected_total_tokens": 1200000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 usage_bar.py
echo ""

# Test 7: Uso muy bajo (5%)
echo -e "${BLUE}Test 7: Uso bajo - 5%${NC}"
echo '{"current_tokens": 50000, "expected_total_tokens": 60000, "model": {"id": "claude-sonnet-4-5", "display_name": "Claude Sonnet 4.5"}}' | python3 usage_bar.py
echo ""

# Test 8: JSON inválido (debe mostrar error)
echo -e "${BLUE}Test 8: JSON inválido - debería mostrar error${NC}"
echo '{invalid json' | python3 usage_bar.py
echo ""

# Test 9: Sin stdin (debería retornar vacío)
echo -e "${BLUE}Test 9: Sin stdin - debería retornar vacío${NC}"
echo '' | python3 usage_bar.py
echo ""

echo -e "${GREEN}=== Todas las pruebas completadas ===${NC}"
echo ""
echo -e "${YELLOW}Verifica que:${NC}"
echo "1. La barra de progreso se muestre correctamente: [████░░]"
echo "2. El porcentaje coincida con el uso esperado"
echo "3. El tiempo de reset se muestre (Today HH:MM o Tmrw HH:MM)"
echo "4. Todo esté en una sola línea"
echo "5. Los errores se manejen correctamente"
