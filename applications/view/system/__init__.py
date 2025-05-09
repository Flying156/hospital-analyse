from flask import Flask, Blueprint

from applications.view.system.index import bp as index_bp
from applications.view.system.log import bp as log_bp
from applications.view.system.passport import bp as passport_bp
from applications.view.system.power import bp as power_bp
from applications.view.system.rights import bp as right_bp
from applications.view.system.role import bp as role_bp
from applications.view.system.user import bp as user_bp
from applications.view.system.hospital import bp as hospital_bp
from applications.view.system.analysis import bp as analysis_bp
from applications.view.system.department import bp as department_bp
from applications.view.system.hosptialType import bp as hosptialType_bp
from applications.view.system.hospitalAverage import bp as hospitalAverage_bp
from applications.view.system.hospitalLevelDepart import bp as hospitalLevelDepart_bp
from applications.view.system.hospitalCluster import bp as hospitalCluster_bp
# 创建sys
system_bp = Blueprint('system', __name__, url_prefix='/system')


def register_system_bps(app: Flask):
    # 在admin_bp下注册子蓝图
    system_bp.register_blueprint(user_bp)
    system_bp.register_blueprint(log_bp)
    system_bp.register_blueprint(power_bp)
    system_bp.register_blueprint(role_bp)
    system_bp.register_blueprint(analysis_bp)
    system_bp.register_blueprint(passport_bp)
    system_bp.register_blueprint(right_bp)
    system_bp.register_blueprint(hospital_bp)
    system_bp.register_blueprint(department_bp)
    system_bp.register_blueprint(hosptialType_bp)
    system_bp.register_blueprint(hospitalAverage_bp)
    system_bp.register_blueprint(hospitalLevelDepart_bp)
    system_bp.register_blueprint(hospitalCluster_bp)
    app.register_blueprint(index_bp)
    app.register_blueprint(system_bp)
