from sqlalchemy import create_engine, Column, Integer, String, DateTime, Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# 创建数据表基类
Base = declarative_base()


# 订阅表
class Subscription(Base):
    __tablename__ = 'subscription'

    id = Column(Integer, Sequence('subscription_id_seq'), primary_key=True, nullable=False)
    sub_id = Column(Integer, nullable=False, comment='直播间房间号')
    up_name = Column(String(64), nullable=False, comment='up名称')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    def __init__(self, sub_id, up_name, created_at=None, updated_at=None):
        self.sub_id = sub_id
        self.up_name = up_name
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Subscription(sub_id='%s', up_name='%s', created_at='%s', created_at='%s')>" % (
                   self.sub_id, self.up_name, self.created_at, self.updated_at)


# 文件表
class Files(Base):
    __tablename__ = 'files'

    id = Column(Integer, Sequence('files_id_seq'), primary_key=True, nullable=False)
    file_name_hash = Column(String(16), nullable=False, comment='文件名sha1')
    sub_id = Column(Integer, nullable=False, comment='文件对应的直播间房间号')
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    def __init__(self, file_name_hash, sub_id, created_at=None, updated_at=None):
        self.file_name_hash = file_name_hash
        self.sub_id = sub_id
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return "<Files(file_name_hash='%s', sub_id='%s', created_at='%s', created_at='%s')>" % (
                   self.file_name_hash, self.sub_id, self.created_at, self.updated_at)


# 格式化数据库引擎链接
DB_ENGINE = f'sqlite:///data.db'

# 初始化数据库连接
engine = create_engine(DB_ENGINE, encoding='utf8', pool_recycle=3600, pool_pre_ping=True)
# 初始化数据库结构
Base.metadata.create_all(engine)
# 创建DBSession对象
DBSession = sessionmaker()
DBSession.configure(bind=engine)
# 创建session对象
DBSESSION = DBSession()


__all__ = [
    'DBSESSION',
    'Subscription',
    'Files'
]
