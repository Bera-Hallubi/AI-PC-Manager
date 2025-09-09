"""
Performance configuration for UI components
Optimizes UI responsiveness and reduces glitching
"""

# UI Performance Settings
UI_PERFORMANCE_CONFIG = {
    # Update intervals (in milliseconds)
    'status_update_interval': 15000,  # 15 seconds
    'learning_update_interval': 60000,  # 60 seconds
    'system_update_interval': 10000,  # 10 seconds
    
    # Throttling settings
    'min_update_interval': 5.0,  # Minimum seconds between updates
    'max_updates_per_minute': 10,  # Maximum updates per minute
    
    # Caching settings
    'cache_duration': 2.0,  # Cache duration in seconds
    'enable_metrics_caching': True,
    'enable_ui_caching': True,
    
    # UI optimization settings
    'simplified_status_display': True,
    'reduced_learning_info': True,
    'disable_animations': True,
    'lazy_loading': True,
    
    # System monitoring optimization
    'reduced_monitoring_frequency': True,
    'cpu_interval': 5.0,
    'memory_interval': 5.0,
    'disk_interval': 20.0,
    'network_interval': 10.0,
    'process_interval': 30.0,
    
    # Alert thresholds (to reduce false alerts)
    'cpu_threshold': 90.0,
    'memory_threshold': 95.0,
    'disk_threshold': 98.0,
    'temperature_threshold': 85.0,
    
    # Data processing optimization
    'max_command_history': 100,
    'max_learned_patterns': 50,
    'max_metrics_history': 500,
    
    # UI rendering optimization
    'enable_double_buffering': True,
    'reduce_repaints': True,
    'optimize_text_rendering': True,
}

def get_performance_config():
    """Get performance configuration"""
    return UI_PERFORMANCE_CONFIG.copy()

def apply_performance_optimizations():
    """Apply performance optimizations to the application"""
    import os
    import sys
    
    # Set environment variables for better performance
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '0'
    os.environ['QT_SCALE_FACTOR'] = '1'
    
    # Disable Qt debug output
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;*.warning=false'
    
    # Optimize Python garbage collection
    import gc
    gc.set_threshold(1000, 10, 10)  # More aggressive garbage collection
    
    return True

def create_optimized_timer_config():
    """Create optimized timer configuration for UI updates"""
    return {
        'status_timer': {
            'interval': UI_PERFORMANCE_CONFIG['status_update_interval'],
            'single_shot': False,
            'throttle': True,
            'throttle_duration': UI_PERFORMANCE_CONFIG['min_update_interval']
        },
        'learning_timer': {
            'interval': UI_PERFORMANCE_CONFIG['learning_update_interval'],
            'single_shot': False,
            'throttle': True,
            'throttle_duration': UI_PERFORMANCE_CONFIG['min_update_interval']
        },
        'system_timer': {
            'interval': UI_PERFORMANCE_CONFIG['system_update_interval'],
            'single_shot': False,
            'throttle': True,
            'throttle_duration': 2.0
        }
    }

def get_ui_optimization_tips():
    """Get UI optimization tips for better performance"""
    return [
        "Use QTimer with throttling to prevent excessive updates",
        "Cache frequently accessed data to reduce computation",
        "Simplify UI text displays to reduce rendering time",
        "Use lazy loading for heavy components",
        "Disable animations for better responsiveness",
        "Reduce monitoring frequency to lower CPU usage",
        "Implement data pagination for large datasets",
        "Use QThread for heavy operations to avoid UI blocking",
        "Optimize text rendering with simplified formatting",
        "Cache system metrics to avoid repeated computation"
    ]
