from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime,Column, ForeignKey, Integer, String, Float, Boolean, or_
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import datetime
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    password_hash = Column(String(64))
    email = Column(String)
    picture = Column(String)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
    	s = Serializer(secret_key, expires_in = expiration)
    	return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
    	s = Serializer(secret_key)
    	try:
    		data = s.loads(token)
    	except SignatureExpired:
    		#Valid Token, but expired
    		return None
    	except BadSignature:
    		#Invalid Token
    		return None
    	user_id = data['id']
    	return user_id

    @property
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'picture': self.picture
        }


class Request(Base):
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    meal_type = Column(String(50), nullable=False)
    location_string = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    meal_time = Column(String, default=datetime.datetime.utcnow)
    filled = Column(Boolean)


class Proposal(Base):
    __tablename__ = 'proposal'
    id = Column(Integer, primary_key=True)
    user_proposed_to = Column(Integer)
    user_proposed_from = Column(Integer)
    request_id = Column(Integer, ForeignKey('request.id'))
    request = relationship(Request)
    filled = Column(Boolean)


class MealDate(Base):
    __tablename__ = 'meal_date'
    id = Column(Integer, primary_key=True)
    user_1 = Column(Integer)
    user_2 = Column(Integer)
    restaurant_name = Column(String)
    restaurant_address = Column(String)
    restaurant_picture = Column(String)
    meal_time = Column(String, default=datetime.datetime.utcnow)
engine = create_engine('sqlite:///data.db')
Base.metadata.create_all(engine)
