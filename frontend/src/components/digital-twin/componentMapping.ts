export const MAPPING: Record<string, string[]> = {
    'engine': [
        'KC390.002_turbina_0', 
        'KC390_Motor_0', 
        'KC390.003_Fan_lim_0'
    ],
    'landing_gear': [
        'KC3901_fuzelagem_wheel.003_0', 
        'KC3902_fuzelagem_gear_0', 
        'KC3902_fuzelagem_wheel_0', 
        'KC3903_fuzelagem_gear_0', 
        'KC3902.001_fuzelagem_wheel.003_0', 
        'KC3902.002_fuzelagem_wheel.003_0', 
        'KC390.001_fuzelagem_gear_0',
        'KC3902.003_fuzelagem_wheel.003_0', 
        'KC3902.004_fuzelagem_wheel.003_0',
        'KC390.013_fuzelagem_gear_parts_0'
    ],
    'avionics': [
        'KC390.005_radar_0', 
        'KC390.006_hud_0', 
        'KC390.007_painel_0', 
        'KC390.010_painel_0'
    ],
    // The model doesn't have explicit meshes for these. 
    // We map them to logical proxies if needed, or leave them empty.
    'hydraulic_pump': [],
    'valve': [],
    'fuel_pump': []
};
