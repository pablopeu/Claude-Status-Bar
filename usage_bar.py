#!/usr/bin/env python3
# ~/.claude-code/scripts/usage_bar.py
"""
Claude Code Status Bar - Muestra uso de contexto y tiempo de reset
Formato: [████████░░] 75% Reset: Sat 00:00
"""
import json
import sys
import shutil
import os
from pathlib import Path
from datetime import datetime, timedelta

def get_terminal_width():
    """Obtiene el ancho actual de la terminal"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def get_context_limit(model_info):
    """
    Determina el límite de contexto según el modelo
    - Sonnet 4.5: 1.2M tokens (límite de sesión para Claude Pro)
    - Otros modelos: 200K tokens
    """
    if not model_info:
        return 200_000

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    # Detectar Sonnet 4.5 (1.2M session limit para Claude Pro)
    # Nota: El context window es 1M, pero el límite de sesión es ~1.2M
    if 'sonnet-4-5' in model_id or 'sonnet 4.5' in model_name or 'claude-sonnet-4-5' in model_id:
        return 1_200_000

    # Por defecto 200K para otros modelos
    return 200_000

def get_plan_name(model_info):
    """
    Determina el nombre del plan según el modelo
    """
    if not model_info:
        return "Free"

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    if 'opus' in model_id or 'opus' in model_name:
        return "Pro"
    elif 'sonnet' in model_id or 'sonnet' in model_name:
        return "Pro"
    elif 'haiku' in model_id or 'haiku' in model_name:
        return "Free"

    return "Free"

def calculate_next_reset():
    """
    Calcula el próximo reset de Claude Code
    Los límites se resetean cada 5 horas en bloques:
    00:00-05:00, 05:00-10:00, 10:00-15:00, 15:00-20:00, 20:00-01:00 (siguiente día)
    """
    now = datetime.now()
    current_hour = now.hour

    # Determinar el próximo bloque de 5 horas
    if current_hour < 5:
        reset_hour = 5
        reset_day = now
    elif current_hour < 10:
        reset_hour = 10
        reset_day = now
    elif current_hour < 15:
        reset_hour = 15
        reset_day = now
    elif current_hour < 20:
        reset_hour = 20
        reset_day = now
    else:  # >= 20
        reset_hour = 0
        reset_day = now + timedelta(days=1)

    next_reset = reset_day.replace(hour=reset_hour, minute=0, second=0, microsecond=0)

    # Formato: "Sat 15:00" o "Today 15:00"
    if next_reset.date() == now.date():
        return f"Today {next_reset.strftime('%H:%M')}"
    elif next_reset.date() == (now + timedelta(days=1)).date():
        return f"Tmrw {next_reset.strftime('%H:%M')}"
    else:
        return next_reset.strftime("%a %H:%M")

def get_session_tokens(session_id):
    """
    Lee el archivo JSONL de la sesión y calcula los tokens totales
    Retorna: (input_tokens, output_tokens, cache_creation, cache_read)
    """
    # Buscar en las posibles ubicaciones de Claude
    possible_paths = [
        Path.home() / ".claude" / "projects",
        Path.home() / ".config" / "claude" / "projects"
    ]

    for base_path in possible_paths:
        if not base_path.exists():
            continue

        # Buscar el archivo JSONL de esta sesión
        for jsonl_file in base_path.rglob("*.jsonl"):
            if session_id in jsonl_file.name:
                return parse_jsonl_tokens(jsonl_file)

    return 0, 0, 0, 0

def parse_jsonl_tokens(jsonl_path):
    """
    Parsea un archivo JSONL y suma todos los tokens
    """
    total_input = 0
    total_output = 0
    total_cache_creation = 0
    total_cache_read = 0

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)

                # Extraer usage de diferentes ubicaciones posibles
                usage = data.get('usage', {})
                if not usage and 'message' in data:
                    usage = data['message'].get('usage', {})

                total_input += usage.get('input_tokens', 0)
                total_output += usage.get('output_tokens', 0)
                total_cache_creation += usage.get('cache_creation_input_tokens', 0)
                total_cache_read += usage.get('cache_read_input_tokens', 0)

    except Exception as e:
        # Si hay error leyendo el archivo, retornar ceros
        pass

    return total_input, total_output, total_cache_creation, total_cache_read

def get_color_code(percentage):
    """
    Retorna código de color ANSI según el porcentaje de uso
    Verde: 0-50%, Amarillo: 50-80%, Rojo: 80-100%
    """
    if percentage >= 80:
        return "\033[31m"  # Rojo (menos brillante para fondo negro)
    elif percentage >= 50:
        return "\033[33m"  # Amarillo (menos brillante para fondo negro)
    else:
        return "\033[32m"  # Verde (menos brillante para fondo negro)

def create_progress_bar(percentage, width):
    """Crea la barra de progreso con caracteres Unicode y colores"""
    filled = int(percentage * width / 100)
    empty = width - filled

    # Código de color según el porcentaje
    color = get_color_code(percentage)
    reset = "\033[0m"  # Reset color

    # Crear barra con color
    bar = color + ("█" * filled) + reset + ("░" * empty)
    return bar

def claude_usage_bar():
    """
    Función principal que Claude Code ejecuta para mostrar el status bar
    Lee JSON de stdin y muestra: [████████░░] 75% Reset: Sat 00:00
    """
    try:
        # Leer JSON de stdin (Claude Code pasa datos de la sesión)
        input_data = sys.stdin.read().strip()
        if not input_data:
            return ""

        data = json.loads(input_data)

        # DEBUG: Guardar datos recibidos para análisis
        debug_file = os.path.expanduser("~/.claude-code/statusbar-debug.json")
        try:
            with open(debug_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

        # Extraer información de la sesión
        session_id = data.get('session_id', '')
        model_info = data.get('model', {})

        # Determinar límite de contexto según el modelo
        context_limit = get_context_limit(model_info)

        # Leer tokens del archivo JSONL de la sesión
        input_tokens, output_tokens, cache_creation, cache_read = get_session_tokens(session_id)

        # Calcular total de tokens
        # Incluimos: input + output + cache_creation
        # Los cache_creation tokens SÍ cuentan para el límite de la sesión
        # Los cache_read NO se incluyen (son lecturas del caché, más baratos)
        usage_tokens = input_tokens + output_tokens + cache_creation

        # Si no hay datos de tokens, mostrar mensaje básico
        if usage_tokens == 0:
            plan = get_plan_name(model_info)
            return f"Claude Code ({plan}) - Reset: {calculate_next_reset()}"

        # Calcular porcentaje de uso
        percentage = min(int((usage_tokens / context_limit) * 100), 100)

        # Calcular ancho dinámico de la terminal
        terminal_width = get_terminal_width()
        if terminal_width < 50:
            terminal_width = 50

        # Formatear tokens en formato legible (K para miles)
        def format_tokens(tokens):
            if tokens >= 1_000_000:
                return f"{tokens/1_000_000:.1f}M"
            elif tokens >= 1_000:
                return f"{tokens/1_000:.0f}K"
            else:
                return str(tokens)

        # Preparar strings de información
        color = get_color_code(percentage)
        reset_color = "\033[0m"

        perc_str = f"{color}{percentage}%{reset_color}"
        tokens_str = f"{format_tokens(usage_tokens)}/{format_tokens(context_limit)}"
        reset_str = f"Reset: {calculate_next_reset()}"

        # Calcular ancho disponible para la barra
        # Formato: "[bar] XX% (XXK/XXM) Reset: Xxx XX:XX"
        # Nota: Los códigos de color no cuentan para el ancho visual
        fixed_width = 4 + len(f"{percentage}%") + len(f" ({tokens_str}) ") + len(reset_str)
        bar_width = max(terminal_width - fixed_width, 10)

        # Crear barra de progreso
        progress_bar = create_progress_bar(percentage, bar_width)

        # Retornar línea completa con colores: [████░░] 2% (30K/1M) Reset: Today 15:00
        return f"[{progress_bar}] {perc_str} ({tokens_str}) {reset_str}"

    except Exception as e:
        # En caso de error, mostrar mensaje genérico
        return f"Claude Code (Error: {str(e)[:20]})"

# --- IMPORTANTE: No modificar esta línea ---
# Claude Code busca exactamente esta función para el status bar
__claude_code_status_bar__ = claude_usage_bar

# Permitir ejecución directa para pruebas
if __name__ == "__main__":
    result = claude_usage_bar()
    if result:
        print(result)
