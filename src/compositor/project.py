import numpy as np

def world_to_screen(point_3d, view_matrix_1d, proj_matrix_1d, viewport_width=2048, viewport_height=1536, enu_transform=None):
    """
    Projects a 3D point to 2D screen coordinates.
    """
    # ... (matrices reshaped same as before)
    view_matrix = np.array(view_matrix_1d).reshape((4, 4), order='F')
    proj_matrix = np.array(proj_matrix_1d).reshape((4, 4), order='F')
    
    # 1. Coordinate Transform (Optional: ENU -> ECEF)
    # If the point is ENU and matrix is ECEF, we need this.
    v_world = np.array([point_3d[0], point_3d[1], point_3d[2], 1.0])
    if enu_transform is not None:
        v_world = enu_transform @ v_world
    
    # 2. World -> Camera Space (View Transform)
    v_camera = view_matrix @ v_world
    
    # 3. Camera -> Clip Space (Projection Transform)
    v_clip = proj_matrix @ v_camera
    
    # 4. W-Check
    if v_clip[3] <= 0:
        return None
        
    # 5. Perspective Divide -> NDC
    ndc = v_clip[:3] / v_clip[3]
    
    # 6. Viewport Transform -> Screen
    screen_x = (ndc[0] + 1.0) * 0.5 * viewport_width
    screen_y = (1.0 - ndc[1]) * 0.5 * viewport_height
    
    return (float(screen_x), float(screen_y))

def get_billboard_rotation(camera_world_dir):
    """
    Calculates the 2D rotation for a billboard label so it faces the camera
    while remaining perpendicular to the ground.
    
    Args:
        camera_world_dir: dict {'x':, 'y':, 'z':} direction vector in local ENU frame.
        
    Returns:
        Angle in degrees for the text rotation.
    """
    # Project camera direction onto ground plane (ignore Z)
    dx = camera_world_dir['x']
    dy = camera_world_dir['y']
    
    # Angle from the North (Y) axis
    angle_rad = np.arctan2(dx, dy)
    
    return np.degrees(angle_rad)
