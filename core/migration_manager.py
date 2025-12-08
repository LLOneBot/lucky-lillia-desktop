"""配置迁移模块 - 负责检测和迁移旧版本配置文件"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """配置迁移管理器 - 检测并迁移旧配置到新位置"""
    
    def __init__(self, app_dir: Path):
        """初始化迁移管理器
        
        Args:
            app_dir: 应用程序所在目录
        """
        self.app_dir = app_dir
        self.old_data_dir = app_dir / "data"
        self.new_data_dir = app_dir / "bin" / "llonebot" / "data"
    
    def check_migration_needed(self) -> Tuple[bool, List[str], bool, List[str], bool]:
        """检查是否需要迁移配置
        
        Returns:
            (是否有旧数据, 需要迁移的config文件列表, 是否需要迁移token, 需要迁移的database文件列表, 是否只需删除)
        """
        # 检查旧目录是否存在
        if not self.old_data_dir.exists():
            return False, [], False, [], False
        
        # 查找旧目录中的 config_<数字>.json 文件
        config_files = []
        for f in self.old_data_dir.glob("config_*.json"):
            # 验证文件名格式: config_<数字>.json
            stem = f.stem  # config_123
            if stem.startswith("config_"):
                num_part = stem[7:]  # 123
                if num_part.isdigit():
                    config_files.append(f.name)
        
        # 检查 webui_token.txt
        has_token = (self.old_data_dir / "webui_token.txt").exists()
        
        # 检查 database 目录下的文件
        old_db_dir = self.old_data_dir / "database"
        new_db_dir = self.new_data_dir / "database"
        db_files = []
        if old_db_dir.exists():
            for f in old_db_dir.iterdir():
                if f.is_file():
                    db_files.append(f.name)
        
        # 如果旧目录没有任何需要关注的文件，不处理
        if not config_files and not has_token and not db_files:
            return False, [], False, [], False
        
        # 检查新目录是否已存在这些文件
        files_to_migrate = []
        for config_file in config_files:
            new_path = self.new_data_dir / config_file
            if not new_path.exists():
                files_to_migrate.append(config_file)
        
        # 检查 token 是否需要迁移
        token_needs_migrate = has_token and not (self.new_data_dir / "webui_token.txt").exists()
        
        # 检查 database 文件是否需要迁移
        db_files_to_migrate = []
        for db_file in db_files:
            new_path = new_db_dir / db_file
            if not new_path.exists():
                db_files_to_migrate.append(db_file)
        
        # 即使不需要迁移任何文件，也需要删除旧目录
        only_delete = not files_to_migrate and not token_needs_migrate and not db_files_to_migrate
        
        return True, files_to_migrate, token_needs_migrate, db_files_to_migrate, only_delete
    
    def migrate_configs(
        self, config_files: List[str], migrate_token: bool, db_files: List[str]
    ) -> Tuple[bool, str]:
        """执行配置迁移
        
        Args:
            config_files: 需要迁移的配置文件列表
            migrate_token: 是否迁移 webui_token.txt
            db_files: 需要迁移的 database 文件列表
            
        Returns:
            (是否成功, 错误消息)
        """
        try:
            # 确保目标目录存在
            self.new_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制配置文件
            for config_file in config_files:
                src = self.old_data_dir / config_file
                dst = self.new_data_dir / config_file
                if src.exists():
                    shutil.copy2(src, dst)
                    logger.info(f"已迁移配置文件: {config_file}")
            
            # 复制 token 文件
            if migrate_token:
                src = self.old_data_dir / "webui_token.txt"
                dst = self.new_data_dir / "webui_token.txt"
                if src.exists():
                    shutil.copy2(src, dst)
                    logger.info("已迁移 webui_token.txt")
            
            # 复制 database 文件
            if db_files:
                new_db_dir = self.new_data_dir / "database"
                new_db_dir.mkdir(parents=True, exist_ok=True)
                old_db_dir = self.old_data_dir / "database"
                for db_file in db_files:
                    src = old_db_dir / db_file
                    dst = new_db_dir / db_file
                    if src.exists():
                        shutil.copy2(src, dst)
                        logger.info(f"已迁移数据库文件: {db_file}")
            
            # 删除整个旧 data 目录
            self._remove_dir(self.old_data_dir)
            
            return True, ""
            
        except Exception as e:
            error_msg = f"迁移配置失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def delete_old_data_dir(self):
        """删除旧的 data 目录"""
        self._remove_dir(self.old_data_dir)
    
    def _remove_dir(self, dir_path: Path):
        """删除整个目录"""
        try:
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                logger.info(f"已删除旧目录: {dir_path}")
        except Exception as e:
            logger.warning(f"删除目录失败: {e}")
