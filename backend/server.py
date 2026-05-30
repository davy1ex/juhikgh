#!/usr/bin/env python3
"""
HTTP сервер для управления пауком-роботом через веб-интерфейс.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from servo_manager import ServoManager

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

servo_manager = ServoManager()

MOTION_METHODS = {
    'move_forward_cycle',
    'move_forward_cycle_low',
    'move_backward_cycle',
    'step_right',
    'step_left',
    'wave_fl_leg',
    'stand_up',
    'sit_down',
    'push_up',
}


def _action_route(method_name, success_msg, error_msg):
    def handler():
        if method_name in MOTION_METHODS and servo_manager.is_motion_busy():
            return jsonify({
                "success": False,
                "message": "Робот уже выполняет движение",
                "busy": True,
            }), 409
        try:
            success = getattr(servo_manager, method_name)()
            if success is None:
                return jsonify({
                    "success": False,
                    "message": "Робот уже выполняет движение",
                    "busy": True,
                }), 409
            status = 200 if success else 500
            msg = success_msg if success else error_msg
            return jsonify({"success": success, "message": msg}), status
        except Exception as e:
            return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    return handler


@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')


@app.route('/calibrate')
def calibrate():
    return send_from_directory('../frontend', 'calibrate.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('../frontend', filename)


@app.route('/api/angles', methods=['GET'])
def get_angles():
    angles = servo_manager.get_all_angles()
    return jsonify(angles)


@app.route('/api/i2c_status', methods=['GET'])
def i2c_status():
    connected = servo_manager.is_i2c_connected()
    return jsonify({
        "connected": connected,
        "message": "PCA9685 подключен" if connected else "I2C не найден",
    })


@app.route('/api/motion_status', methods=['GET'])
def motion_status():
    return jsonify({"busy": servo_manager.is_motion_busy()})


@app.route('/api/set_angle', methods=['POST'])
def set_angle():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data"}), 400
        leg = data.get('leg')
        joint = data.get('joint')
        angle = data.get('angle')
        if not leg or not joint or angle is None:
            return jsonify({"success": False, "message": "Missing leg, joint or angle"}), 400
        success = servo_manager.set_angle(leg, joint, angle)
        if success:
            return jsonify({"success": True, "message": f"Angle {leg} {joint} set to {angle}°"})
        return jsonify({"success": False, "message": "Invalid parameters (leg, joint or angle)"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


app.add_url_rule('/api/move_forward', 'move_forward', _action_route('move_forward_cycle', 'Forward step completed', 'Error during forward movement'), methods=['POST'])
app.add_url_rule('/api/move_forward_2', 'move_forward_2', _action_route('move_forward_cycle_low', 'Forward (low stance) completed', 'Error during forward (low stance)'), methods=['POST'])
app.add_url_rule('/api/move_backward', 'move_backward', _action_route('move_backward_cycle', 'Backward movement completed', 'Error during backward movement'), methods=['POST'])
app.add_url_rule('/api/move_right', 'move_right', _action_route('step_right', 'Right step completed', 'Error during right movement'), methods=['POST'])
app.add_url_rule('/api/move_left', 'move_left', _action_route('step_left', 'Left step completed', 'Error during left movement'), methods=['POST'])
app.add_url_rule('/api/wave_fl', 'wave_fl', _action_route('wave_fl_leg', 'FL leg waved', 'Error during wave'), methods=['POST'])
app.add_url_rule('/api/stand_up', 'stand_up', _action_route('stand_up', 'Spider stood up', 'Error during stand up'), methods=['POST'])
app.add_url_rule('/api/sit_down', 'sit_down', _action_route('sit_down', 'Spider sat down', 'Error during sit down'), methods=['POST'])
app.add_url_rule('/api/push_up', 'push_up', _action_route('push_up', 'Push-up completed', 'Error during push-up'), methods=['POST'])


if __name__ == '__main__':
    import os
    debug = os.environ.get('SPIDER_DEBUG', '1') == '1'

    print("=" * 60)
    print("Starting spider robot control server")
    print("=" * 60)
    print("Open in browser: http://localhost:5000")
    print("Calibration:     http://localhost:5000/calibrate")
    print("I2C PCA9685:", "подключен" if servo_manager.is_i2c_connected() else "не найден")
    print("Debug mode:", debug)
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=debug)
