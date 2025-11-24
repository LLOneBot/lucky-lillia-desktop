"""演示主入口功能 - 验证应用可以正确初始化"""

from main import initialize_managers, setup_logging
from __version__ import __version__
from utils.constants import APP_NAME

def demo_initialization():
    """演示应用初始化过程"""
    print("="*60)
    print(f"{APP_NAME} v{__version__} - 初始化演示")
    print("="*60)
    print()
    
    # 1. 设置日志系统
    print("1. 设置日志系统...")
    logger = setup_logging()
    print(f"   ✓ 日志系统已配置: {logger.name}")
    print()
    
    # 2. 初始化所有管理器
    print("2. 初始化所有管理器...")
    try:
        managers = initialize_managers()
        print(f"   ✓ 进程管理器: {type(managers['process_manager']).__name__}")
        print(f"   ✓ 日志收集器: {type(managers['log_collector']).__name__}")
        print(f"   ✓ 配置管理器: {type(managers['config_manager']).__name__}")
        print(f"   ✓ 版本检测器: {type(managers['version_detector']).__name__}")
        print(f"   ✓ 更新检查器: {type(managers['update_checker']).__name__}")
        print(f"   ✓ 本地存储: {type(managers['storage']).__name__}")
        print()
        
        # 3. 验证配置加载
        print("3. 验证配置管理...")
        config = managers['config_manager'].load_config()
        print(f"   ✓ 配置已加载，包含 {len(config)} 个配置项")
        print()
        
        # 4. 验证本地存储
        print("4. 验证本地存储...")
        test_key = "demo_test"
        test_value = "演示值"
        managers['storage'].save_setting(test_key, test_value)
        loaded_value = managers['storage'].load_setting(test_key)
        assert loaded_value == test_value
        managers['storage'].delete_setting(test_key)
        print(f"   ✓ 本地存储读写正常")
        print()
        
        # 5. 验证进程管理器状态
        print("5. 验证进程管理器...")
        from core.process_manager import ProcessStatus
        pmhq_status = managers['process_manager'].get_process_status("pmhq")
        llonebot_status = managers['process_manager'].get_process_status("llonebot")
        print(f"   ✓ PMHQ状态: {pmhq_status.value}")
        print(f"   ✓ LLOneBot状态: {llonebot_status.value}")
        print()
        
        print("="*60)
        print("✓ 所有组件初始化成功！应用已准备就绪。")
        print("="*60)
        print()
        print("提示：运行 'python main.py' 启动完整的GUI应用")
        
        return True
        
    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = demo_initialization()
    exit(0 if success else 1)
