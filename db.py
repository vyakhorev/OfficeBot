import sqlalchemy as sa

import sqlalchemy.ext.declarative
import traceback

BASE = sa.ext.declarative.declarative_base()

class abst_key:
    def __repr__(self):
        return self.string_key()

    def __my_key(self):
        return (self.__tablename__, self.rec_id)

    def string_key(self):
        s_r = ""
        for s in self.__my_key():
            s_r += str(s)
        return s_r

    def __eq__(x, y):
        return x.__my_key() == y.__my_key()

    def __hash__(self):
        return hash(self.__my_key())

class cUser(BASE, abst_key):
    __tablename__ = "user"
    rec_id = sa.Column(sa.Integer, primary_key=True)
    telegram_id = sa.Column(sa.String(255))
    telegram_name = sa.Column(sa.Unicode(255))

    def __repr__(self):
        return self.telegram_name

class cChat(BASE, abst_key):
    __tablename__ = "chat"
    rec_id = sa.Column(sa.Integer, primary_key=True)
    chat_id = sa.Column(sa.String(255))
    user_rec_id = sa.Column(sa.Integer, sa.ForeignKey('user.rec_id'))
    user = sa.orm.relationship("cUser")

    def __repr__(self):
        return self.telegram_name

class c_database_handler:
    def __init__(self, db_conn_str):
        self.engine = sa.create_engine(db_conn_str, echo=False, encoding='utf-8')
        BASE.metadata.create_all(self.engine)
        self.session_maker = sa.orm.sessionmaker(bind=self.engine)
        self._active_sess = None

    def _activate_session(self):
        if self._active_sess is None:
            self._active_sess = self.session_maker()

    def get_active_session(self):
        self._activate_session()
        return self._active_sess

    def add_object_to_session(self, obj):
        self._activate_session()
        self._active_sess.add(obj)

    def delete_concrete_object(self, an_object):
        self._activate_session()
        # Merge?
        self._active_sess.delete(an_object)
        self._active_sess.commit()

    def commit_session(self):
        self._activate_session()
        try:
            self._active_sess.commit()
        except:
            print("Error with commiting the session")
            print(traceback.format_exc())
            self.close_session()

    def close_session(self):
        self._activate_session()
        self._active_sess.close()
        self._active_sess = None

    def commit_and_close_session(self):
        self.commit_session()
        self.close_session()

############
# FUNCTIONS
############


def check_for_user(sess, user_tele_id):
    if sess.query(cUser).filter_by(telegram_id=user_tele_id).count() > 0:
        return True
    return False

def get_all_chats(sess):
    return sess.query(cChat).all()

