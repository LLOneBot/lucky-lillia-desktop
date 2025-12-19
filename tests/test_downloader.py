"""测试文件下载管理模块"""

import pytest
import os
import tempfile
import tarfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings
from utils.downloader import Downloader


@pytest.fixture
def downloader():
    """创建Downloader实例"""
    return Downloader()


class TestDownloader:
    """测试Downloader类"""
    
    def test_find_in_path_returns_path_when_found(self, downloader):
        """测试在PATH中找到可执行文件时返回路径"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/node"
            result = downloader.find_in_path("node")
            assert result == "/usr/bin/node"
            mock_which.assert_called_once_with("node")
    
    def test_find_in_path_returns_none_when_not_found(self, downloader):
        """测试在PATH中找不到可执行文件时返回None"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = None
            result = downloader.find_in_path("nonexistent")
            assert result is None
    
    def test_check_node_available_finds_node_exe(self, downloader):
        """测试检测系统中的node.exe"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = "C:\\Program Files\\nodejs\\node.exe"
            result = downloader.check_node_available()
            assert result == "C:\\Program Files\\nodejs\\node.exe"
    
    def test_check_node_available_returns_none_when_not_found(self, downloader):
        """测试系统中没有node时返回None"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = None
            result = downloader.check_node_available()
            assert result is None
    
    def test_check_ffmpeg_available_finds_ffmpeg(self, downloader):
        """测试检测系统中的ffmpeg"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = "C:\\ffmpeg\\bin\\ffmpeg.exe"
            result = downloader.check_ffmpeg_available()
            assert result == "C:\\ffmpeg\\bin\\ffmpeg.exe"

    def test_check_ffprobe_available_finds_ffprobe(self, downloader):
        """测试检测系统中的ffprobe"""
        with patch('utils.downloader.shutil.which') as mock_which:
            mock_which.return_value = "C:\\ffmpeg\\bin\\ffprobe.exe"
            result = downloader.check_ffprobe_available()
            assert result == "C:\\ffmpeg\\bin\\ffprobe.exe"
    
    # Feature: qq-bot-manager, Property 16: 文件存在性检查正确性
    @given(
        filename=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='_-.'
            ),
            min_size=1,
            max_size=50
        ).filter(lambda x: x not in ['.', '..'] and not x.startswith('.'))
    )
    def test_check_file_exists_property(self, filename):
        """属性测试：对于任何文件路径，如果该路径指向的文件存在于文件系统中，检查函数应该返回True
        
        **验证需求：9.1**
        """
        downloader = Downloader()
        
        # 创建一个临时目录和文件
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / filename
            
            # 确保文件存在
            file_path.write_text("test content")
            
            # 验证：文件存在时应该返回True
            assert downloader.check_file_exists(str(file_path)) is True
            
            # 删除文件
            file_path.unlink()
            
            # 验证：文件不存在时应该返回False
            assert downloader.check_file_exists(str(file_path)) is False
    
    def test_check_file_exists_with_directory(self, downloader, tmp_path):
        """测试目录路径应该返回False（因为check_file_exists检查的是文件）"""
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()
        assert downloader.check_file_exists(str(dir_path)) is False
    
    def test_check_file_exists_with_nonexistent_path(self, downloader):
        """测试不存在的路径应该返回False"""
        nonexistent_path = "/path/that/does/not/exist/file.txt"
        assert downloader.check_file_exists(nonexistent_path) is False
    
    def test_check_file_exists_with_empty_string(self, downloader):
        """测试空字符串路径应该返回False"""
        assert downloader.check_file_exists("") is False

    # Feature: qq-bot-manager, Property 17: 下载进度报告完整性
    @given(
        file_size=st.integers(min_value=100, max_value=500),
        chunk_size=st.just(256)
    )
    @settings(max_examples=1, deadline=None)
    def test_download_progress_completeness_property(self, file_size, chunk_size):
        """属性测试：对于任何下载过程，进度回调应该至少被调用一次
        
        **验证需求：9.4**
        """
        downloader = Downloader()
        mock_data = b'x' * file_size
        progress_calls = []
        
        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = os.path.join(tmp_dir, "test_file")
            
            # 创建一个有效的tgz文件内容
            tgz_temp_path = os.path.join(tmp_dir, "temp.tgz")
            package_dir = os.path.join(tmp_dir, "package")
            os.makedirs(package_dir)
            with open(os.path.join(package_dir, "pmhq-win-x64.exe"), 'wb') as f:
                f.write(mock_data)
            
            with tarfile.open(tgz_temp_path, 'w:gz') as tar:
                tar.add(package_dir, arcname='package')
            
            with open(tgz_temp_path, 'rb') as f:
                tgz_content = f.read()
            
            with patch('utils.downloader.requests.get') as mock_get, \
                 patch('utils.downloader.get_package_tarball_url') as mock_tarball:
                
                mock_tarball.return_value = "https://registry.npmmirror.com/pmhq/-/pmhq-1.0.0.tgz"
                
                mock_response = MagicMock()
                mock_response.headers = {'content-length': str(len(tgz_content))}
                mock_response.raise_for_status = Mock()
                mock_response.iter_content = lambda chunk_size: [tgz_content]
                mock_get.return_value = mock_response
                
                result = downloader.download_pmhq(save_path, progress_callback)
                
                assert result is True
                assert len(progress_calls) >= 1
                last_downloaded, last_total = progress_calls[-1]
                assert last_downloaded == len(tgz_content)

    def test_get_pmhq_download_url(self, downloader):
        """测试获取PMHQ下载URL"""
        with patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            mock_tarball.return_value = "https://registry.npmmirror.com/pmhq/-/pmhq-1.0.0.tgz"
            url = downloader.get_pmhq_download_url()
            assert "pmhq" in url
            assert ".tgz" in url
    
    def test_get_llbot_download_url(self, downloader):
        """测试获取LLBot下载URL"""
        with patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-dist/-/llonebot-dist-3.0.0.tgz"
            url = downloader.get_llbot_download_url()
            assert "llonebot" in url
            assert ".tgz" in url
    
    def test_get_node_download_url(self, downloader):
        """测试获取Node.exe下载URL"""
        with patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-node-exe/-/llonebot-node-exe-1.0.0.tgz"
            url = downloader.get_node_download_url()
            assert "llonebot-node-exe" in url
            assert ".tgz" in url
    
    def test_get_ffmpeg_download_url(self, downloader):
        """测试获取FFmpeg下载URL"""
        with patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-ffmpeg-exe/-/llonebot-ffmpeg-exe-1.0.0.tgz"
            url = downloader.get_ffmpeg_download_url()
            assert "llonebot-ffmpeg-exe" in url
            assert ".tgz" in url
    
    def test_download_llbot_success(self, downloader, tmp_path):
        """测试成功下载LLBot"""
        save_path = tmp_path / "llbot"
        
        # 创建一个有效的tgz文件内容
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        (package_dir / "llbot.js").write_text("test")
        
        tgz_temp_path = tmp_path / "temp.tgz"
        with tarfile.open(tgz_temp_path, 'w:gz') as tar:
            tar.add(package_dir, arcname='package')
        
        with open(tgz_temp_path, 'rb') as f:
            tgz_content = f.read()
        
        progress_calls = []
        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))
        
        with patch('utils.downloader.requests.get') as mock_get, \
             patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-dist/-/llonebot-dist-3.0.0.tgz"
            
            mock_response = MagicMock()
            mock_response.headers = {'content-length': str(len(tgz_content))}
            mock_response.raise_for_status = Mock()
            mock_response.iter_content = lambda chunk_size: [tgz_content]
            mock_get.return_value = mock_response
            
            result = downloader.download_llbot(str(save_path), progress_callback)
            
            assert result is True
            assert len(progress_calls) >= 1

    def test_download_node_success(self, downloader, tmp_path):
        """测试成功下载Node.exe"""
        save_path = tmp_path / "node.exe"
        
        # 创建一个有效的tgz文件内容
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        (package_dir / "node.exe").write_bytes(b'MZ\x90\x00test')
        
        tgz_temp_path = tmp_path / "temp.tgz"
        with tarfile.open(tgz_temp_path, 'w:gz') as tar:
            tar.add(package_dir, arcname='package')
        
        with open(tgz_temp_path, 'rb') as f:
            tgz_content = f.read()
        
        progress_calls = []
        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))
        
        with patch('utils.downloader.requests.get') as mock_get, \
             patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-exe/-/llonebot-exe-1.0.0.tgz"
            
            mock_response = MagicMock()
            mock_response.headers = {'content-length': str(len(tgz_content))}
            mock_response.raise_for_status = Mock()
            mock_response.iter_content = lambda chunk_size: [tgz_content]
            mock_get.return_value = mock_response
            
            result = downloader.download_node(str(save_path), progress_callback)
            
            assert result is True
            assert len(progress_calls) >= 1
    
    def test_download_ffmpeg_success(self, downloader, tmp_path):
        """测试成功下载FFmpeg"""
        save_path = tmp_path / "ffmpeg.exe"
        
        # 创建一个有效的tgz文件内容
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        (package_dir / "ffmpeg.exe").write_bytes(b'MZ\x90\x00ffmpeg')
        
        tgz_temp_path = tmp_path / "temp.tgz"
        with tarfile.open(tgz_temp_path, 'w:gz') as tar:
            tar.add(package_dir, arcname='package')
        
        with open(tgz_temp_path, 'rb') as f:
            tgz_content = f.read()
        
        with patch('utils.downloader.requests.get') as mock_get, \
             patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            
            mock_tarball.return_value = "https://registry.npmmirror.com/llonebot-ffmpeg-exe/-/llonebot-ffmpeg-exe-1.0.0.tgz"
            
            mock_response = MagicMock()
            mock_response.headers = {'content-length': str(len(tgz_content))}
            mock_response.raise_for_status = Mock()
            mock_response.iter_content = lambda chunk_size: [tgz_content]
            mock_get.return_value = mock_response
            
            result = downloader.download_ffmpeg(str(save_path))
            
            assert result is True
    
    def test_download_ffprobe_calls_download_ffmpeg(self, downloader, tmp_path):
        """测试download_ffprobe调用download_ffmpeg（因为它们在同一个包中）"""
        save_path = tmp_path / "ffprobe.exe"
        
        with patch.object(downloader, 'download_ffmpeg', return_value=True) as mock_download:
            result = downloader.download_ffprobe(str(save_path))
            assert result is True
            mock_download.assert_called_once()


    def test_get_app_update_download_url(self, downloader):
        """测试获取应用更新下载URL"""
        with patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            mock_tarball.return_value = "https://registry.npmmirror.com/lucky-lillia-desktop-win-x64/-/lucky-lillia-desktop-win-x64-1.0.0.tgz"
            url = downloader.get_app_update_download_url()
            assert "lucky-lillia-desktop" in url
            assert ".tgz" in url

    def test_download_app_update_success(self, downloader, tmp_path):
        """测试成功下载应用更新"""
        current_exe = tmp_path / "qq-bot-manager.exe"
        
        # 创建一个有效的tgz文件内容，包含exe文件
        package_dir = tmp_path / "package"
        package_dir.mkdir()
        (package_dir / "qq-bot-manager.exe").write_bytes(b'MZ\x90\x00new_version')
        
        tgz_temp_path = tmp_path / "temp.tgz"
        with tarfile.open(tgz_temp_path, 'w:gz') as tar:
            tar.add(package_dir, arcname='package')
        
        with open(tgz_temp_path, 'rb') as f:
            tgz_content = f.read()
        
        progress_calls = []
        def progress_callback(downloaded, total):
            progress_calls.append((downloaded, total))
        
        with patch('utils.downloader.requests.get') as mock_get, \
             patch('utils.downloader.get_package_tarball_url') as mock_tarball:
            
            mock_tarball.return_value = "https://registry.npmmirror.com/lucky-lillia-desktop-win-x64/-/lucky-lillia-desktop-win-x64-1.0.0.tgz"
            
            mock_response = MagicMock()
            mock_response.headers = {'content-length': str(len(tgz_content))}
            mock_response.raise_for_status = Mock()
            mock_response.iter_content = lambda chunk_size: [tgz_content]
            mock_get.return_value = mock_response
            
            result = downloader.download_app_update(str(current_exe), progress_callback)
            
            # 应该返回新exe的路径
            assert result.endswith('.exe')
            assert os.path.exists(result)
            assert len(progress_calls) >= 1

    def test_apply_app_update_creates_batch_script(self, downloader, tmp_path):
        """测试应用更新创建批处理脚本"""
        new_exe = tmp_path / "new" / "qq-bot-manager.exe"
        new_exe.parent.mkdir()
        new_exe.write_bytes(b'MZ\x90\x00new')
        
        current_exe = tmp_path / "current" / "qq-bot-manager.exe"
        current_exe.parent.mkdir()
        current_exe.write_bytes(b'MZ\x90\x00old')
        
        # 使用当前进程PID
        current_pid = os.getpid()
        batch_script = downloader.apply_app_update(str(new_exe), str(current_exe), current_pid)
        
        # 验证批处理脚本被创建
        assert os.path.exists(batch_script)
        assert batch_script.endswith('_update.bat')
        
        # 验证脚本内容包含必要的命令
        with open(batch_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'qq-bot-manager.exe' in content
        assert str(current_pid) in content  # 验证PID在脚本中
        assert 'copy' in content.lower() or 'move' in content.lower()
