__version__ = '0.1.0'

def syncdb(pool=None):
    """
    Create tables if they don't exist
    """
    from flask_philo_sqlalchemy.schema import Base  # noqa
    from flask_philo_sqlalchemy.orm import BaseModel  # noqa
    from flask_philo_sqlalchemy.connection import create_pool

    if pool is None:
        pool = create_pool()

    for conn_name, conn in pool.connections.items():
        Base.metadata.create_all(conn.engine)


def cleandb(pool=None):
    from flask_philo_sqlalchemy.schema import Base  # noqa
    from flask_philo_sqlalchemy.orm import BaseModel  # noqa
    from flask_philo_sqlalchemy.connection import create_pool

    if pool is None:
        pool = create_pool()

    for t in reversed(BaseModel.metadata.sorted_tables):
        sql = 'delete from {} cascade;'.format(t.name)
        for conn_name, conn in pool.connections.items():
            conn.session.execute(sql)
            conn.session.commit()
