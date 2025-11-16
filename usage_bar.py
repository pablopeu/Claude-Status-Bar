# ~/.claude-code/scripts/usage_bar.py
import json
import os
import shutil
from datetime import datetime, timedelta

def get_terminal_width():
    """Obtiene el ancho actual de la terminal"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def calculate_next_reset():
    """Calcula el próximo reset (Sábado 00:00 por defecto)"""
    RESET_DAY = 6  # 0=Domingo, 6=Sábado
    RESET_HOUR = 0
    RESET_MINUTE = 0
    
    now = datetime.now()
    current_weekday = now.weekday()  # 0=Lunes, 6=Domingo
    current_day = (current_weekday + 1) % 7  # Convertir a 0=Domingo
    
    days_until_reset = (RESET_DAY - current_day) % 7
    if days_until_reset == 0:
        reset_time = now.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0)
        if now >= reset_time:
            days_until_reset = 7
    
    next_reset = now + timedelta(days=days_until_reset)
    next_reset = next_reset.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0)
    
    return next_reset.strftime("%a %H:%M")

def create_progress_bar(percentage, width):
    """Crea la barra de progreso con caracteres Unicode"""
    filled = int(percentage * width / 100)
    empty = width - filled
    return "█" * filled + "░" * empty

def claude_usage_bar():
    """
    Función principal que Claude Code ejecuta para mostrar el status bar
    Formato: "75% [████████████░░░░░░░░] Next: Sat 00:00"
    """
    try:
        # Leer config
        config_path = os.path.expanduser("~/.claude.json")
        if not os.path.exists(config_path):
            return ""
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        # Extraer datos
        allowed = data.get('limits', {}).get('daily', {}).get('allowed', 0)
        used = data.get('daily', 0)
        
        if not allowed:
            return ""
        
        percentage = min(int(used * 100 / allowed), 100)
        
        # Calcular ancho dinámico
        terminal_width = get_terminal_width()
        if terminal_width < 50:
            terminal_width = 50
        
        perc_str = f"{percentage}%"
        reset_str = f"Next: {calculate_next_reset()}"
        
        # Ancho fijo: " [] " + espacios = 6 caracteres
        fixed_width = len(perc_str) + len(reset_str) + 6
        bar_width = max(terminal_width - fixed_width, 8)
        
        # Crear barra
        progress_bar = create_progress_bar(percentage, bar_width)
        
        # Retornar línea completa
        return f"{perc_str} [{progress_bar}] {reset_str}"
        
    except:
        return ""

# --- IMPORTANTE: No modificar esta línea ---
# Claude Code busca exactamente esta función para el status bar
__claude_code_status_bar__ = claude_usage_bar
