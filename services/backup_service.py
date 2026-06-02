"""
数据库自动备份服务 — 每日自动备份 cache.db
"""
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def run_backup(
    db_path: str | Path = None,
    backup_dir: str | Path = None,
    keep_days: int = 7,
) -> bool:
    """
    执行数据库备份
    - 将 db_path 复制为 backup_dir/cache_YYYYMMDD.db
    - 同一天已备份则跳过（幂等）
    - 清理超过 keep_days 天的旧备份
    返回 True 表示备份成功或已存在，False 表示失败
    """
    if db_path is None:
        db_path = Path(__file__).parent.parent / "cache.db"
    else:
        db_path = Path(db_path)

    if backup_dir is None:
        backup_dir = Path(__file__).parent.parent / "backups"
    else:
        backup_dir = Path(backup_dir)

    try:
        # 源文件不存在则跳过
        if not db_path.exists():
            logger.info("cache.db 不存在，跳过备份")
            return True

        # 创建备份目录
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 幂等：当天已备份则跳过
        today_str = datetime.now().strftime("%Y%m%d")
        dest = backup_dir / f"cache_{today_str}.db"
        if dest.exists():
            logger.info(f"当天备份已存在: {dest.name}")
            _clean_old_backups(backup_dir, keep_days)
            return True

        # 执行备份
        shutil.copy2(str(db_path), str(dest))
        logger.info(f"备份完成: {dest.name}")

        # 清理旧备份
        _clean_old_backups(backup_dir, keep_days)

        return True

    except Exception as e:
        logger.warning(f"备份失败（不影响应用运行）: {e}")
        return False


def _clean_old_backups(backup_dir: Path, keep_days: int) -> None:
    """清理超过 keep_days 天的旧备份"""
    cutoff = datetime.now() - timedelta(days=keep_days)
    for f in backup_dir.glob("cache_*.db"):
        try:
            # 从文件名提取日期，格式 cache_YYYYMMDD.db
            date_str = f.stem.replace("cache_", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < cutoff:
                f.unlink()
                logger.info(f"清理旧备份: {f.name}")
        except (ValueError, OSError):
            pass  # 无法解析文件名或删除失败，跳过
