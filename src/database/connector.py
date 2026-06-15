from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def db_connector(path):
    engine = create_engine(f"sqlite:///{path}")
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    return session