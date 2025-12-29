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
    - Sonnet 4.5: 1M tokens
    - Otros modelos: 200K tokens
    """
    if not model_info:
        return 200_000

    model_id = model_info.get('id', '').lower()
    model_name = model_info.get('display_name', '').lower()

    # Detectar Sonnet 4.5 (1M context)
    if 'sonnet-4-5' in model_id or 'sonnet 4.5' in model_name or 'claude-sonnet-4-5' in model_id:
        return 1_000_000

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

def get_color_code(percentage):
    """
    Retorna código de color ANSI apagado según el porcentaje de uso
    Verde oscuro (0-50%), Amarillo oscuro (50-80%), Rojo oscuro (80-100%)
    """
    if percentage >= 80:
        return "\033[31m"  # Rojo oscuro
    elif percentage >= 50:
        return "\033[33m"  # Amarillo oscuro
    else:
        return "\033[32m"  # Verde oscuro

def calculate_time_to_reset():
    """
    Calcula el tiempo hasta el próximo reset de Claude Code
    Los límites se resetean cada 5 horas en bloques:
    00:00-05:00, 05:00-10:00, 10:00-15:00, 15:00-20:00, 20:00-01:00 (siguiente día)
    Retorna: tupla (horas, minutos)
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

    # Calcular diferencia en horas y minutos
    time_diff = next_reset - now
    hours = time_diff.seconds // 3600
    minutes = (time_diff.seconds % 3600) // 60

    return hours, minutes

def create_progress_bar(percentage, width):
    """Crea la barra de progreso con caracteres Unicode y colores apagados"""
    filled = int(percentage * width / 100)
    empty = width - filled

    # Obtener color según porcentaje
    color = get_color_code(percentage)
    reset = "\033[0m"

    # Barra coloreada: caracteres llenos en color, caracteres vacíos sin color
    return color + ("█" * filled) + reset + ("░" * empty)

def get_weekly_usage_percentage(data):
    """
    Obtiene el porcentaje de uso semanal desde los datos de Claude Code
    Si no está disponible, retorna None
    """
    try:
        # Buscar información de uso semanal en diferentes campos del JSON
        # Claude Code puede pasar estos datos en varios formatos

        # Opción 1: Campo directo weekly_usage_percentage
        if 'weekly_usage_percentage' in data:
            return int(data['weekly_usage_percentage'])

        # Opción 2: weekly_usage con used/limit
        weekly_usage = data.get('weekly_usage', {})
        if weekly_usage:
            used = weekly_usage.get('used', 0)
            limit = weekly_usage.get('limit', 0)
            if limit > 0:
                return int((used / limit) * 100)

        # Opción 3: Calcular desde remaining percentage (si dice "87% left" = 13% usado)
        weekly_remaining = data.get('weekly_remaining_percentage')
        if weekly_remaining is not None:
            return int(100 - weekly_remaining)

        # Si no hay datos disponibles, retornar None
        return None
    except:
        return None

def get_token_usage_from_transcript(transcript_path):
    """
    Lee el transcript de la sesión actual y calcula el uso de tokens
    El archivo es JSONL (JSON Lines): cada línea es un JSON separado
    """
    try:
        if not os.path.exists(transcript_path):
            return None, None

        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_creation = 0
        total_cache_read = 0

        with open(transcript_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)

                    # Solo procesar mensajes de tipo "assistant"
                    if entry.get('type') != 'assistant':
                        continue

                    # Extraer usage de message.usage
                    message = entry.get('message', {})
                    usage = message.get('usage', {})

                    if not usage:
                        continue

                    # Sumar tokens de input (nuevos)
                    total_input_tokens += usage.get('input_tokens', 0)

                    # Sumar tokens de output
                    total_output_tokens += usage.get('output_tokens', 0)

                    # Sumar cache creation tokens
                    total_cache_creation += usage.get('cache_creation_input_tokens', 0)

                    # Sumar cache read tokens
                    total_cache_read += usage.get('cache_read_input_tokens', 0)

                except json.JSONDecodeError:
                    # Ignorar líneas que no sean JSON válido
                    continue

        # El contexto total usado incluye:
        # - input_tokens: tokens nuevos procesados
        # - cache_creation: tokens usados para crear cache
        # - cache_read: tokens leídos de cache (cuestan menos pero ocupan contexto)
        # - output_tokens: tokens de respuesta
        total_context_tokens = total_input_tokens + total_cache_creation + total_cache_read + total_output_tokens

        return total_context_tokens, total_output_tokens
    except Exception as e:
        # En caso de error, retornar None
        return None, None

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

        # Extraer información del modelo
        model_info = data.get('model', {})

        # Determinar límite de contexto según el modelo
        context_limit = get_context_limit(model_info)

        # Intentar obtener tokens de varias fuentes
        usage_tokens = 0

        # Método 1: Campos directos en data
        current_tokens = data.get('current_tokens', 0)
        expected_total_tokens = data.get('expected_total_tokens', 0)
        input_tokens = data.get('inputTokens', 0)

        # Método 2: Leer desde el transcript
        transcript_path = data.get('transcript_path', '')
        if transcript_path:
            input_tok, output_tok = get_token_usage_from_transcript(transcript_path)
            if input_tok:
                usage_tokens = input_tok

        # Método 3: Usar campos directos si están disponibles
        if not usage_tokens:
            if current_tokens > 0:
                usage_tokens = current_tokens
            elif expected_total_tokens > 0:
                usage_tokens = expected_total_tokens
            elif input_tokens > 0:
                usage_tokens = input_tokens

        # Si no hay datos de tokens, mostrar plan por defecto
        if usage_tokens == 0:
            plan = get_plan_name(model_info)
            return f"Claude Code ({plan})"

        # Calcular porcentaje de uso
        percentage = min(int((usage_tokens / context_limit) * 100), 100)

        # Obtener uso semanal
        weekly_percentage = get_weekly_usage_percentage(data)

        # Calcular tiempo hasta reset
        hours, minutes = calculate_time_to_reset()

        # Calcular ancho dinámico de la terminal
        terminal_width = get_terminal_width()
        if terminal_width < 50:
            terminal_width = 50

        # Preparar strings de información con el nuevo formato compacto
        # Formato: [████████████░░░░░░░░] 4% TTR:2H 30M Week:13%
        color = get_color_code(percentage)
        reset = "\033[0m"

        perc_str = f"{color}{percentage}%{reset}"
        ttr_str = f"TTR:{hours}H {minutes}M"
        week_str = f"Week:{weekly_percentage}%" if weekly_percentage is not None else ""

        # Calcular ancho disponible para la barra
        # Formato: "[bar] X% TTR:XH XM Week:X%"
        # Nota: len() cuenta los códigos ANSI, así que usamos len sin colores
        fixed_width = 4 + len(f"{percentage}%") + len(ttr_str) + (len(week_str) if week_str else 0)
        bar_width = max(terminal_width - fixed_width, 10)

        # Crear barra de progreso con colores
        progress_bar = create_progress_bar(percentage, bar_width)

        # Construir línea completa
        if week_str:
            return f"[{progress_bar}] {perc_str} {ttr_str} {week_str}"
        else:
            return f"[{progress_bar}] {perc_str} {ttr_str}"

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
